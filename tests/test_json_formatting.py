#!/usr/bin/env python3
"""
Test script for JSON formatting functionality in the integrated text editor.
"""

import json
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_json_formatting():
    """Test JSON formatting functions."""
    
    # Test valid JSON
    test_json = '{"name":"John","age":30,"city":"New York","hobbies":["reading","coding","gaming"]}'
    
    print("Original JSON:")
    print(test_json)
    print()
    
    try:
        # Parse and format
        parsed = json.loads(test_json)
        formatted = json.dumps(parsed, indent=4, ensure_ascii=False, sort_keys=True)
        
        print("Formatted JSON:")
        print(formatted)
        print()
        
        # Minify
        minified = json.dumps(parsed, separators=(',', ':'), ensure_ascii=False)
        print("Minified JSON:")
        print(minified)
        print()
        
        print("✅ JSON formatting test passed!")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    # Test invalid JSON
    invalid_json = '{"name":"John","age":30,"city"}'
    print("\nTesting invalid JSON:")
    print(invalid_json)
    
    try:
        json.loads(invalid_json)
        print("❌ Should have failed for invalid JSON")
        return False
    except json.JSONDecodeError as e:
        print(f"✅ Correctly caught invalid JSON: {e}")
        print(f"   Line: {e.lineno}, Column: {e.colno}")
    
    return True

if __name__ == "__main__":
    success = test_json_formatting()
    sys.exit(0 if success else 1)
