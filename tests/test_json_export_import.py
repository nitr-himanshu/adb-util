#!/usr/bin/env python3
"""
Test script for JSON export/import functionality
"""

import json
import tempfile
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_json_export_import():
    """Test JSON export and import functionality."""
    try:
        # Test imports
        from services.script_manager import ScriptManager, ScriptType, Script
        print("✅ Imports successful")
        
        # Create a test script manager
        script_manager = ScriptManager()
        print("✅ Script manager initialized")
        
        # Create test script data
        test_script = Script(
            id="test_id_1",
            name="Test Script",
            script_type=ScriptType.HOST_WINDOWS,
            script_path="test_script.bat",
            description="A test script for JSON export/import",
            is_template=True,
            is_visible=True
        )
        
        # Add to manager
        script_manager.scripts["test_id_1"] = test_script
        print("✅ Test script created")
        
        # Test export functionality
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_file = f.name
        
        try:
            # Create a dummy script file
            script_content = "@echo off\necho Hello World\npause"
            with open(test_script.script_path, 'w') as f:
                f.write(script_content)
            
            success = script_manager.export_scripts_to_json(export_file)
            print(f"✅ Export successful: {success}")
            
            # Check exported JSON structure
            with open(export_file, 'r') as f:
                exported_data = json.load(f)
            
            print(f"✅ Exported {len(exported_data)} scripts")
            
            # Verify JSON structure
            expected_fields = {"name", "script_path", "type", "isTemplate", "show"}
            if exported_data and all(field in exported_data[0] for field in expected_fields):
                print("✅ JSON structure correct")
                print(f"   Sample: {exported_data[0]}")
            else:
                print("❌ JSON structure incorrect")
                return False
            
            # Test import functionality
            imported_count, skipped_count = script_manager.import_scripts_from_json(export_file)
            print(f"✅ Import completed: {imported_count} imported, {skipped_count} skipped")
            
            # Clean up
            os.unlink(export_file)
            if os.path.exists(test_script.script_path):
                os.unlink(test_script.script_path)
                
            print("✅ JSON export/import functionality working correctly!")
            return True
            
        except Exception as e:
            print(f"❌ Error during export/import test: {e}")
            # Clean up
            if os.path.exists(export_file):
                os.unlink(export_file)
            if os.path.exists(test_script.script_path):
                os.unlink(test_script.script_path)
            return False
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_json_export_import()
    sys.exit(0 if success else 1)
