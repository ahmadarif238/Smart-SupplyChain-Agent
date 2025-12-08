"""
Utility functions for parsing and extracting structured data from text.
"""
import json
import re
from typing import Optional, Dict, Any


def try_parse_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to extract and parse JSON from text that may contain additional formatting.
    
    This function is useful when dealing with LLM responses that might wrap JSON
    in markdown code blocks or include additional text before/after the JSON.
    
    Args:
        text: The text string that may contain JSON
        
    Returns:
        Parsed JSON as a dictionary if successful, None otherwise
        
    Examples:
        >>> try_parse_json_from_text('{"key": "value"}')
        {'key': 'value'}
        
        >>> try_parse_json_from_text('```json\\n{"key": "value"}\\n```')
        {'key': 'value'}
        
        >>> try_parse_json_from_text('Some text {"key": "value"} more text')
        {'key': 'value'}
    """
    if not text or not isinstance(text, str):
        return None
    
    # Strategy 1: Try parsing the entire text as JSON
    try:
        return json.loads(text.strip())
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Strategy 2: Extract JSON from markdown code blocks
    # Patterns: ```json\n{...}\n``` or ```\n{...}\n```
    code_block_patterns = [
        r'```(?:json)?\s*\n([\s\S]*?)\n```',  # Markdown code blocks
        r'`([^`]+)`',  # Inline code blocks
    ]
    
    for pattern in code_block_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                return json.loads(match.strip())
            except (json.JSONDecodeError, ValueError):
                continue
    
    # Strategy 3: Find JSON objects or arrays in the text
    # Look for patterns like {...} or [...]
    json_patterns = [
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple nested objects
        r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]',  # Simple nested arrays
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                # Try to parse each potential JSON match
                parsed = json.loads(match)
                # Return the first valid JSON object/array found
                if isinstance(parsed, (dict, list)):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                continue
    
    # Strategy 4: Try to find JSON by looking for balanced braces
    # This handles more complex nested structures
    try:
        # Find the first '{' and try to parse from there
        start_idx = text.find('{')
        if start_idx != -1:
            # Track brace depth to find the matching closing brace
            depth = 0
            in_string = False
            escape_next = False
            
            for i in range(start_idx, len(text)):
                char = text[i]
                
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char == '"' and not in_string:
                    in_string = True
                elif char == '"' and in_string:
                    in_string = False
                elif char == '{' and not in_string:
                    depth += 1
                elif char == '}' and not in_string:
                    depth -= 1
                    if depth == 0:
                        # Found matching closing brace
                        potential_json = text[start_idx:i+1]
                        try:
                            return json.loads(potential_json)
                        except (json.JSONDecodeError, ValueError):
                            break
    except Exception:
        pass
    
    # If all strategies fail, return None
    return None


def extract_json_array(text: str) -> Optional[list]:
    """
    Attempts to extract and parse a JSON array from text.
    
    Args:
        text: The text string that may contain a JSON array
        
    Returns:
        Parsed JSON array as a list if successful, None otherwise
    """
    result = try_parse_json_from_text(text)
    if isinstance(result, list):
        return result
    return None


def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to extract and parse a JSON object from text.
    
    Args:
        text: The text string that may contain a JSON object
        
    Returns:
        Parsed JSON object as a dictionary if successful, None otherwise
    """
    result = try_parse_json_from_text(text)
    if isinstance(result, dict):
        return result
    return None
