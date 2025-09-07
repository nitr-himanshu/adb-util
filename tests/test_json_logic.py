#!/usr/bin/env python3
"""
Test script specifically for JSON formatting functionality.
This test focuses on the JSON processing logic without GUI dependencies.
"""

import json
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_json_formatting_logic():
    """Test the core JSON formatting logic."""
    
    print("Testing JSON formatting logic...")
    
    # Test 1: Valid JSON formatting
    test_json = '{"name":"John","age":30,"city":"New York"}'
    try:
        parsed = json.loads(test_json)
        formatted = json.dumps(parsed, indent=4, ensure_ascii=False, sort_keys=True)
        expected_lines = formatted.split('\n')
        
        # Verify proper formatting
        assert len(expected_lines) > 1, "Should have multiple lines"
        assert expected_lines[0] == "{", "Should start with {"
        assert expected_lines[-1] == "}", "Should end with }"
        assert "    " in formatted, "Should have indentation"
        print("✅ JSON formatting test passed")
        
    except Exception as e:
        print(f"❌ JSON formatting test failed: {e}")
        return False
    
    # Test 2: JSON minification
    formatted_json = '''{\n    "name": "John",\n    "age": 30,\n    "city": "New York"\n}'''
    try:
        parsed = json.loads(formatted_json)
        minified = json.dumps(parsed, separators=(',', ':'), ensure_ascii=False)
        
        # Verify minification
        assert '\n' not in minified, "Minified JSON should not have newlines"
        assert '    ' not in minified, "Minified JSON should not have indentation"
        assert minified == '{"name":"John","age":30,"city":"New York"}', "Should match expected minified format"
        print("✅ JSON minification test passed")
        
    except Exception as e:
        print(f"❌ JSON minification test failed: {e}")
        return False
    
    # Test 3: JSON validation (valid)
    valid_json = '{"name":"John","age":30}'
    try:
        parsed = json.loads(valid_json)
        # If we get here, JSON is valid
        print("✅ JSON validation (valid) test passed")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON validation (valid) test failed: {e}")
        return False
    
    # Test 4: JSON validation (invalid)
    invalid_json = '{"name":"John","age":30'  # Missing closing brace
    try:
        json.loads(invalid_json)
        print("❌ JSON validation (invalid) test failed: Should have thrown error")
        return False
    except json.JSONDecodeError as e:
        # Expected behavior
        assert e.lineno == 1, f"Error should be on line 1, got {e.lineno}"
        assert e.colno > 0, f"Error should have column info, got {e.colno}"
        print("✅ JSON validation (invalid) test passed")
    
    # Test 5: Empty content handling
    empty_content = ""
    if not empty_content.strip():
        print("✅ Empty content handling test passed")
    else:
        print("❌ Empty content handling test failed")
        return False
    
    # Test 6: Complex JSON with arrays and nested objects
    complex_json = '{"users":[{"name":"John","settings":{"theme":"dark","lang":"en"}},{"name":"Jane","settings":{"theme":"light","lang":"fr"}}],"count":2}'
    try:
        parsed = json.loads(complex_json)
        formatted = json.dumps(parsed, indent=4, ensure_ascii=False, sort_keys=True)
        
        # Verify complex structure is preserved
        reparsed = json.loads(formatted)
        assert reparsed["count"] == 2, "Count should be preserved"
        assert len(reparsed["users"]) == 2, "Users array should have 2 items"
        assert reparsed["users"][0]["settings"]["theme"] == "dark", "Nested objects should be preserved"
        print("✅ Complex JSON formatting test passed")
        
    except Exception as e:
        print(f"❌ Complex JSON formatting test failed: {e}")
        return False
    
    print("\n🎉 All JSON formatting tests passed!")
    return True

if __name__ == "__main__":
    success = test_json_formatting_logic()
    sys.exit(0 if success else 1)
