# app/utils/gemini_utils.py
import os
import re
import json
import logging
import time
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("gemini_utils")

# Import config (NO token_manager - it was causing blocking)
from app.config.llm_config import LLMConfig

# Import Google GenAI client
try:
    from google import genai
    from google.genai import types
    GEMINI_CLIENT = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    logger.info("✅ Gemini client initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize Gemini client: {e}")
    GEMINI_CLIENT = None

# Rate-limit tracking
_last_gemini_call_time = 0
_rate_limit_delay = 0

def clean_llm_response(text: str) -> str:
    """Remove <think> blocks and commentary."""
    if not text:
        return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"^\s*Assistant:", "", text, flags=re.IGNORECASE)
    return text.strip()

def query_gemini(model: str, prompt: str, max_tokens: int = 2048, timeout: int = 30, max_retries: int = 3) -> str:
    """
    Query Google Gemini with retry logic.
    
    Args:
        model: Gemini model name (e.g., "gemini-2.5-flash")
        prompt: Prompt text
        max_tokens: Max tokens in response
        timeout: Per-request timeout in seconds (NOTE: Gemini SDK doesn't support timeout directly)
        max_retries: Max number of retry attempts
    
    Returns:
        Cleaned LLM response string, or None if failed
    """
    global _last_gemini_call_time, _rate_limit_delay
    
    if GEMINI_CLIENT is None:
        logger.error("❌ Gemini client not initialized")
        raise RuntimeError("Gemini client not installed or GEMINI_API_KEY is not configured.")
    
    cleaned_prompt = prompt
    retry_count = 0
    base_delay = 1
    
    while retry_count <= max_retries:
        try:
            # Throttle requests
            elapsed = time.time() - _last_gemini_call_time
            if _rate_limit_delay > 0 and elapsed < _rate_limit_delay:
                wait_time = _rate_limit_delay - elapsed
                logger.info(f"Rate limit throttle: waiting {wait_time:.1f}s")
                time.sleep(wait_time)
            
            _last_gemini_call_time = time.time()
            
            # Make API call
            logger.debug(f"Calling Gemini API: {model}")
            resp = GEMINI_CLIENT.models.generate_content(
                model=model,
                contents=[cleaned_prompt],
                config=types.GenerateContentConfig(
                    system_instruction="You are a logistics and supply chain expert. Provide clear, data-driven responses.",
                    temperature=0.1,
                    max_output_tokens=max_tokens
                )
            )
            
            # Reset rate limit delay on success
            _rate_limit_delay = 0
            
            # Extract text from response
            try:
                content = resp.text
                logger.info(f"✅ Gemini API call successful ({len(content)} chars)")
            except Exception:
                content = str(resp)
            
            return clean_llm_response(content)
            
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a rate limit error (429)
            if "429" in error_str or "rate_limit" in error_str.lower() or "quota" in error_str.lower():
                if retry_count < max_retries:
                    wait_time = base_delay * (2 ** retry_count)
                    _rate_limit_delay = wait_time
                    
                    retry_count += 1
                    logger.warning(f"Rate limit (429). Retry {retry_count}/{max_retries} after {wait_time}s")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Rate limit retries exhausted for {model}")
                    return None
            else:
                # Non-rate-limit error
                logger.error(f"Gemini query failed (attempt {retry_count + 1}): {error_str[:200]}")
                if retry_count < max_retries:
                    retry_count += 1
                    time.sleep(base_delay * (2 ** (retry_count - 1)))
                    continue
                # All retries exhausted, return None for fallback
                logger.error("All retries exhausted, returning None for fallback")
                return None

def extract_retry_after(error_str: str) -> Optional[float]:
    """Extract retry delay from error message."""
    try:
        match = re.search(r'try again in ([\d.]+)s', error_str)
        if match:
            return float(match.group(1)) + 1.0
    except Exception:
        pass
    return None

def try_parse_json_from_text(text: str):
    """Find and parse JSON from text."""
    if not text:
        return None
    text = clean_llm_response(text)
    try:
        return json.loads(text)
    except Exception:
        pass
    # Find JSON object/array
    m = re.search(r"(\{(?:.|\s)*\}|\[(?:.|\s)*\])", text)
    if m:
        blob = m.group(0)
        try:
            return json.loads(blob)
        except Exception:
            try:
                fixed = re.sub(r"'", '"', blob)
                return json.loads(fixed)
            except Exception:
                return None
    return None
