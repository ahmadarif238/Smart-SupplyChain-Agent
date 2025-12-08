# app/utils/token_manager.py
"""
Token Management System for Google Gemini API rate limiting.
Tracks request/token usage and enforces quotas to prevent 429 errors.
"""

import time
import logging
from typing import Dict, Optional
from collections import deque
from threading import Lock

from app.config.llm_config import LLMConfig

logger = logging.getLogger("token_manager")


class TokenManager:
    """
    Manages token and request rate limiting for Google Gemini API.
    Uses sliding window algorithm to track usage per minute.
    """
    
    def __init__(self):
        self.lock = Lock()
        
        # Sliding window: store (timestamp, tokens) tuples
        self.token_usage = deque(maxlen=300)  # Last 300 requests (all models)
        self.request_timestamps = deque(maxlen=300)  # All requests
        
        # Circuit breaker state
        self.circuit_breaker_tripped = False
        self.circuit_breaker_reset_time = 0
        
        # Statistics
        self.total_requests = 0
        self.total_tokens = 0
        self.rate_limit_hits = 0
        
        logger.info(f"TokenManager initialized with config: {LLMConfig.to_dict()}")
    
    def estimate_tokens(self, text: str, model: str = "gemini-2.5-flash") -> int:
        """
        Estimate token count for text.
        Uses rough approximation: 1 token ≈ 4 characters for English.
        
        For production, consider using tiktoken library for accurate counts.
        """
        if not text:
            return 0
        
        # Rough estimate: 4 chars per token (conservative)
        estimated = len(text) // 4
        
        # Add small buffer for special tokens
        return int(estimated * 1.1)
    
    def can_make_request(self, model: str, estimated_tokens: int) -> bool:
        """
        Check if we can make a request without exceeding rate limits.
        
        Args:
            model: Model name (e.g., "llama-3.3-70b-versatile")
            estimated_tokens: Estimated tokens for this request
            
        Returns:
            True if request can be made, False if would exceed limits
        """
        if not LLMConfig.ENABLE_TOKEN_TRACKING:
            return True
        
        # Check circuit breaker
        if self._is_circuit_breaker_tripped():
            logger.warning("Circuit breaker tripped, blocking LLM request")
            return False
        
        with self.lock:
            current_time = time.time()
            
            # Clean old entries (older than 60 seconds)
            self._cleanup_old_entries(current_time)
            
            # Check RPD limit (Gemini uses daily limit, but we track per-minute for safety)
            # For simplicity, we'll use a per-minute approximation: 240 RPD ≈ 0.17 RPM
            # But since Gemini's limit is generous, we'll just track total calls
            requests_last_minute = len([
                ts for ts in self.request_timestamps
                if current_time - ts < 60
            ])
            
            # More lenient check - Gemini allows 250 RPD, so ~4 RPM sustained
            if requests_last_minute >= 4:
                logger.warning(
                    f"Rate limit threshold: {requests_last_minute} requests/min (Gemini: 250 RPD)"
                )
                self.rate_limit_hits += 1
                return False
            
            # Check TPM limit (single limit for all Gemini models)
            tpm_limit = LLMConfig.get_model_tpm_limit(model)
            
            tokens_last_minute = sum([
                tokens for ts, tokens in self.token_usage
                if current_time - ts < 60
            ])
            
            if tokens_last_minute + estimated_tokens > tpm_limit:
                logger.warning(
                    f"TPM limit would be exceeded: "
                    f"{tokens_last_minute + estimated_tokens}/{tpm_limit} for {model}"
                )
                self.rate_limit_hits += 1
                return False
            
            return True
    
    def record_request(self, model: str, tokens_used: int):
        """
        Record a successful request for rate limiting tracking.
        
        Args:
            model: Model name
            tokens_used: Actual tokens consumed (from API response)
        """
        if not LLMConfig.ENABLE_TOKEN_TRACKING:
            return
        
        with self.lock:
            current_time = time.time()
            
            # Record request timestamp
            self.request_timestamps.append(current_time)
            
            # Record token usage (all models use same pool in Gemini)
            self.token_usage.append((current_time, tokens_used))
            self.total_tokens += tokens_used
            
            self.total_requests += 1
            
            # Check if we should trip circuit breaker
            self._check_circuit_breaker()
    
    def get_quota_status(self) -> Dict[str, any]:
        """
        Get current quota usage and remaining capacity.
        
        Returns:
            Dictionary with quota information
        """
        with self.lock:
            current_time = time.time()
            self._cleanup_old_entries(current_time)
            
            # Calculate usage in last minute
            requests_last_minute = len([
                ts for ts in self.request_timestamps
                if current_time - ts < 60
            ])
            
            tokens_last_minute = sum([
                tokens for ts, tokens in self.token_usage
                if current_time - ts < 60
            ])
            
            return {
                "requests": {
                    "used": requests_last_minute,
                    "limit": LLMConfig.GEMINI_MAX_RPD,
                    "remaining": max(0, LLMConfig.GEMINI_MAX_RPD - requests_last_minute),
                    "percentage": (requests_last_minute / max(1, LLMConfig.GEMINI_MAX_RPD)) * 100
                },
                "tokens": {
                    "used": tokens_last_minute,
                    "limit": LLMConfig.GEMINI_MAX_TPM,
                    "remaining": max(0, LLMConfig.GEMINI_MAX_TPM - tokens_last_minute),
                    "percentage": (tokens_last_minute / LLMConfig.GEMINI_MAX_TPM) * 100
                },
                "statistics": {
                    "total_requests": self.total_requests,
                    "total_tokens": self.total_tokens,
                    "rate_limit_hits": self.rate_limit_hits
                },
                "circuit_breaker": {
                    "tripped": self.circuit_breaker_tripped,
                    "reset_time": self.circuit_breaker_reset_time
                }
            }
    
    def reset_statistics(self):
        """Reset usage statistics (useful for testing)."""
        with self.lock:
            self.total_requests = 0
            self.total_tokens = 0
            self.rate_limit_hits = 0
            logger.info("Token manager statistics reset")
    
    def _cleanup_old_entries(self, current_time: float):
        """Remove entries older than 60 seconds."""
        cutoff = current_time - 60
        
        # Clean request timestamps
        while self.request_timestamps and self.request_timestamps[0] < cutoff:
            self.request_timestamps.popleft()
        
        # Clean token usage
        while self.token_usage and self.token_usage[0][0] < cutoff:
            self.token_usage.popleft()
    
    def _check_circuit_breaker(self):
        """Check if circuit breaker should trip based on usage."""
        if not LLMConfig.ENABLE_CIRCUIT_BREAKER:
            return
        
        quota = self.get_quota_status()
        
        # Trip if any quota exceeds threshold
        for resource in ["requests", "tokens"]:
            if quota[resource]["percentage"] > LLMConfig.CIRCUIT_BREAKER_THRESHOLD * 100:
                if not self.circuit_breaker_tripped:
                    self.circuit_breaker_tripped = True
                    self.circuit_breaker_reset_time = time.time() + 60  # Reset after 1 minute
                    logger.error(
                        f"🚨 CIRCUIT BREAKER TRIPPED: {resource} at "
                        f"{quota[resource]['percentage']:.1f}% usage"
                    )
                return
    
    def _is_circuit_breaker_tripped(self) -> bool:
        """Check if circuit breaker is currently tripped."""
        if not self.circuit_breaker_tripped:
            return False
        
        # Auto-reset after timeout
        if time.time() >= self.circuit_breaker_reset_time:
            self.circuit_breaker_tripped = False
            logger.info("✅ Circuit breaker reset")
            return False
        
        return True


# Global singleton instance
token_manager = TokenManager()
