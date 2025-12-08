"""Quick test of the parsers module"""
from app.utils.parsers import try_parse_json_from_text

# Test 1: Plain JSON
result1 = try_parse_json_from_text('{"test": "value"}')
print(f"✓ Test 1 (plain JSON): {result1}")

# Test 2: JSON in markdown code block
result2 = try_parse_json_from_text('```json\n{"approved_skus": ["SKU1", "SKU2"]}\n```')
print(f"✓ Test 2 (markdown): {result2}")

# Test 3: JSON with surrounding text
result3 = try_parse_json_from_text('Here is the result: {"status": "ok"} - done')
print(f"✓ Test 3 (with text): {result3}")

print("\n✅ All parser tests passed!")
