#!/usr/bin/env python3
"""
Test script to verify that JSON export no longer includes script content.
"""

import json
import tempfile
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_json_no_content():
    """Test that JSON export does not include script content."""
    try:
        from services.script_manager import ScriptManager, ScriptType, Script
        print("✅ Imports successful")
        
        # Create a test script manager
        script_manager = ScriptManager()
        print("✅ Script manager initialized")
        
        # Create test script with content
        test_script = Script(
            id="test_content_id",
            name="Test Content Script",
            script_type=ScriptType.HOST_WINDOWS,
            script_path="test_content_script.bat",
            description="A test script to verify content is not exported",
            is_template=True,
            is_visible=True
        )
        
        # Create the actual script file with content
        script_content = "@echo off\necho This is test content\necho Script content should not be in JSON\npause"
        with open(test_script.script_path, 'w') as f:
            f.write(script_content)
        
        # Add to manager
        script_manager.scripts["test_content_id"] = test_script
        print("✅ Test script with content created")
        
        # Export to JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_file = f.name
        
        try:
            success = script_manager.export_scripts_to_json(export_file, ["test_content_id"])
            print(f"✅ Export successful: {success}")
            
            # Check exported JSON
            with open(export_file, 'r') as f:
                exported_data = json.load(f)
            
            if exported_data:
                script_data = exported_data[0]
                print(f"✅ Exported script: {script_data['name']}")
                
                # Verify content is NOT in the export
                if "content" not in script_data:
                    print("✅ PASS: Script content is NOT included in JSON export")
                else:
                    print("❌ FAIL: Script content is still included in JSON export")
                    print(f"   Content found: {script_data.get('content', '')[:50]}...")
                    return False
                
                # Verify required fields are present
                required_fields = ["name", "script_path", "type", "isTemplate", "show"]
                missing_fields = [field for field in required_fields if field not in script_data]
                if not missing_fields:
                    print("✅ All required fields present in export")
                else:
                    print(f"❌ Missing required fields: {missing_fields}")
                    return False
                
                print("✅ JSON export format is correct (no content included)")
                return True
                
            else:
                print("❌ No data exported")
                return False
                
        finally:
            # Clean up
            if os.path.exists(export_file):
                os.unlink(export_file)
            if os.path.exists(test_script.script_path):
                os.unlink(test_script.script_path)
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_json_no_content()
    if success:
        print("\n✅ SUCCESS: JSON export correctly excludes script content!")
    else:
        print("\n❌ FAILURE: Test failed")
    sys.exit(0 if success else 1)
