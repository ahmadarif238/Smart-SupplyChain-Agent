# app/config/llm_config.py
"""
Centralized LLM configuration for Groq API integration.
Manages rate limits, model selection, and token budgets.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class LLMConfig:
    """Configuration for LLM models and token management."""
    
    # Groq Model Selection (Free Tier - Production Models)
    # Source: https://console.groq.com/docs/models
    # NOTE (2026-08): Groq decommissioned ALL Llama chat models
    # (llama-3.1-8b-instant, llama-3.3-70b-versatile, llama3-*-8192).
    # The current free production line-up is the openai/gpt-oss-* family.
    # Model ids are env-overridable so a future rename needs no redeploy.
    FORECAST_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")      # demand forecasting
    SUMMARY_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")       # cycle summaries
    DIALOGUE_MODEL = os.getenv("GROQ_FAST_MODEL", "openai/gpt-oss-20b")  # fast dialogue
    NEGOTIATION_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")   # negotiation reasoning

    # gpt-oss models are reasoning models: without these two params the chain of
    # thought is streamed back inside `content` and breaks every downstream parser.
    REASONING_FORMAT = "hidden"   # strip chain-of-thought from the response
    REASONING_EFFORT = "low"      # keep latency/token use close to the old 8b/70b models

    # Timeout Configuration
    FORECAST_TIMEOUT = 30  # seconds
    SUMMARY_TIMEOUT = 45   # seconds  
    DIALOGUE_TIMEOUT = 15  # seconds
    NEGOTIATION_TIMEOUT = 25  # seconds
    
    # Token Management
    ENABLE_TOKEN_TRACKING = True
    MAX_PROMPT_TOKENS = int(os.getenv("MAX_PROMPT_TOKENS", "2000"))
    MAX_COMPLETION_TOKENS = int(os.getenv("MAX_COMPLETION_TOKENS", "500"))
    
    # Call Limits Per Cycle
    MAX_FORECAST_LLM_CALLS = int(os.getenv("MAX_FORECAST_LLM_CALLS", "10"))
    MAX_NEGOTIATION_LLM_CALLS = int(os.getenv("MAX_NEGOTIATION_LLM_CALLS", "5"))
    MAX_DIALOGUE_LLM_CALLS = int(os.getenv("MAX_DIALOGUE_LLM_CALLS", "5"))
    
    # Retry Settings
    MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
    BASE_RETRY_DELAY = float(os.getenv("LLM_RETRY_DELAY", "1.0"))
    
    # Circuit Breaker
    ENABLE_CIRCUIT_BREAKER = os.getenv("ENABLE_CIRCUIT_BREAKER", "true").lower() == "true"
    CIRCUIT_BREAKER_THRESHOLD = float(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "0.9"))
    
    @classmethod
    def get_timeout_for_task(cls, task: str) -> int:
        """Get appropriate timeout for specific task."""
        timeouts = {
            "forecast": cls.FORECAST_TIMEOUT,
            "negotiation": cls.NEGOTIATION_TIMEOUT,
            "dialogue": cls.DIALOGUE_TIMEOUT,
            "summary": cls.SUMMARY_TIMEOUT
        }
        return timeouts.get(task.lower(), 30)
    
    @classmethod
    def to_dict(cls) -> dict:
        """Export configuration as dictionary for logging/debugging."""
        return {
            "forecast_model": cls.FORECAST_MODEL,
            "negotiation_model": cls.NEGOTIATION_MODEL,
            "dialogue_model": cls.DIALOGUE_MODEL,
            "summary_model": cls.SUMMARY_MODEL,
            "max_forecast_calls": cls.MAX_FORECAST_LLM_CALLS,
            "max_negotiation_calls": cls.MAX_NEGOTIATION_LLM_CALLS,
            "token_tracking_enabled": cls.ENABLE_TOKEN_TRACKING,
            "circuit_breaker_enabled": cls.ENABLE_CIRCUIT_BREAKER
        }
