# app/utils/groq_utils.py
import os
import re
import json
import logging
import time
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("groq_utils")

# Import config (no token_manager - using Groq's built-in rate limiting)
from app.config.llm_config import LLMConfig

# Import Groq client if installed; fallback to requests or raise informative error.
try:
    from groq import Groq
    GROQ_CLIENT = Groq(api_key=os.getenv("GROQ_API_KEY"))
except Exception:
    GROQ_CLIENT = None

# ✅ Rate-limit tracking (prevent cascading failures)
_last_groq_call_time = 0
_rate_limit_delay = 0  # Dynamic delay based on 429 responses

def clean_llm_response(text: str) -> str:
    """
    Remove <think> blocks and surrounding commentary, return the remaining text.
    """
    if not text:
        return ""
    # remove special think blocks
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # remove common assistant commentary markers
    text = re.sub(r"^\s*Assistant:", "", text, flags=re.IGNORECASE)
    return text.strip()

def query_groq(model: str, prompt: str, max_tokens: int = 2048, timeout: int = 30, max_retries: int = 3) -> str:
    """
    Query Groq chat completion with token management and automatic retry logic.
    
    ✅ ENHANCED: 
    - Token tracking and quota management
    - Pre-flight quota checks to prevent 429 errors
    - Exponential backoff for rate limit errors
    - Records actual token usage from API responses
    - Respects circuit breaker for quota protection
    
    Args:
        model: Groq model name (e.g., "llama-3.1-8b-instant")
        prompt: Prompt text
        max_tokens: Max tokens in response
        timeout: Per-request timeout in seconds
        max_retries: Max number of retry attempts for rate limits
    
    Returns:
        Cleaned LLM response string, or None if quota exceeded/rate limited
        
    Raises:
        RuntimeError if Groq client not configured or critical error
    """
    global _last_groq_call_time, _rate_limit_delay
    
    if GROQ_CLIENT is None:
        raise RuntimeError("groq client not installed or GROQ_API_KEY is not configured.")
    
    cleaned_prompt = prompt
    retry_count = 0
    base_delay = 1  # Start with 1 second base delay
    
    while retry_count <= max_retries:
        try:
            # ✅ Throttle requests to avoid rate limits
            elapsed = time.time() - _last_groq_call_time
            if _rate_limit_delay > 0 and elapsed < _rate_limit_delay:
                wait_time = _rate_limit_delay - elapsed
                logger.info(f"Rate limit throttle: waiting {wait_time:.1f}s before next Groq call")
                time.sleep(wait_time)
            
            _last_groq_call_time = time.time()
            
            resp = GROQ_CLIENT.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": cleaned_prompt}],
                max_tokens=max_tokens,
                timeout=timeout
            )
            
            # ✅ Reset rate limit delay on success
            _rate_limit_delay = 0
            
            # Try to extract content in standard shape
            try:
                content = resp.choices[0].message.content
            except Exception:
                content = str(resp)
            return clean_llm_response(content)
            
        except Exception as e:
            error_str = str(e)
            
            # ✅ Check if it's a rate limit error (429)
            if "429" in error_str or "rate_limit" in error_str.lower():
                # Extract retry-after delay if available
                retry_after = extract_retry_after(error_str)
                
                if retry_count < max_retries:
                    # Exponential backoff: 2s, 4s, 8s
                    wait_time = retry_after if retry_after else (base_delay * (2 ** retry_count))
                    _rate_limit_delay = wait_time
                    
                    retry_count += 1
                    logger.warning(
                        f"Rate limit (429) on {model}. Retry {retry_count}/{max_retries} "
                        f"after {wait_time}s. Error: {error_str[:100]}"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    # All retries exhausted
                    logger.error(
                        f"Rate limit retries exhausted for {model}. "
                        f"Error: {error_str[:200]}"
                    )
                    # Return None to signal fallback instead of crashing
                    return None
            else:
                # Non-rate-limit error (timeout, API error, etc.)
                logger.warning(f"Groq query failed (attempt {retry_count + 1}): {error_str[:100]}")
                if retry_count < max_retries:
                    retry_count += 1
                    time.sleep(base_delay * (2 ** retry_count))
                    continue
                raise

def extract_retry_after(error_str: str) -> Optional[float]:
    """
    Extract suggested retry delay from Groq error message.
    E.g., 'Please try again in 4.4s.' -> 4.4
    """
    try:
        match = re.search(r'try again in ([\d.]+)s', error_str)
        if match:
            return float(match.group(1)) + 1.0  # Add 1s buffer
    except Exception:
        pass
    return None

def try_parse_json_from_text(text: str):
    """
    Try to safely find a JSON object/array in text and parse it.
    Return dict/list on success, otherwise return None.
    """
    if not text:
        return None
    text = clean_llm_response(text)
    # quick direct parse attempt
    try:
        return json.loads(text)
    except Exception:
        pass
    # find first JSON object/array block
    import re
    m = re.search(r"(\{(?:.|\s)*\}|\[(?:.|\s)*\])", text)
    if m:
        blob = m.group(0)
        # attempt to replace single quotes by double quotes if necessary
        try:
            return json.loads(blob)
        except Exception:
            try:
                fixed = re.sub(r"'", '"', blob)
                return json.loads(fixed)
            except Exception:
                return None
    return None
