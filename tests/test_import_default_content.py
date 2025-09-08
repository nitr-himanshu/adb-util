#!/usr/bin/env python3
"""
Test script to verify that JSON import creates default content when none is provided.
"""

import json
import tempfile
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_import_creates_default_content():
    """Test that JSON import creates default content when none provided."""
    try:
        from services.script_manager import ScriptManager
        print("✅ Imports successful")
        
        # Create test JSON without content
        test_data = [
            {
                "name": "Test Windows No Content",
                "script_path": "test_windows.bat",
                "type": "host_windows",
                "isTemplate": True,
                "show": True,
                "description": "Test Windows script without content"
            },
            {
                "name": "Test Linux No Content",
                "script_path": "test_linux.sh",
                "type": "host_linux",
                "isTemplate": False,
                "show": True,
                "description": "Test Linux script without content"
            },
            {
                "name": "Test Device No Content",
                "script_path": "test_device.sh",
                "type": "device",
                "isTemplate": False,
                "show": True,
                "description": "Test device script without content"
            }
        ]
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f, indent=2)
            json_file = f.name
        
        print("✅ Test JSON created (without content fields)")
        
        # Initialize script manager
        script_manager = ScriptManager()
        print("✅ Script manager initialized")
        
        try:
            # Import scripts
            imported_count, skipped_count = script_manager.import_scripts_from_json(json_file)
            print(f"✅ Import completed: {imported_count} imported, {skipped_count} skipped")
            
            if imported_count > 0:
                # Check that default content was created
                scripts = script_manager.get_all_scripts()
                
                for script in scripts:
                    if script.name in ["Test Windows No Content", "Test Linux No Content", "Test Device No Content"]:
                        # Check that script file was created
                        if os.path.exists(script.script_path):
                            with open(script.script_path, 'r') as f:
                                content = f.read()
                            
                            print(f"✅ Script file created: {script.name}")
                            print(f"   Content preview: {content[:50]}...")
                            
                            # Verify content is not empty and contains expected elements
                            if content.strip():
                                if script.script_type.value == "host_windows" and "@echo off" in content:
                                    print(f"✅ Windows default content created correctly")
                                elif script.script_type.value == "host_linux" and "#!/bin/bash" in content:
                                    print(f"✅ Linux default content created correctly")
                                elif script.script_type.value == "device" and "#!/system/bin/sh" in content:
                                    print(f"✅ Device default content created correctly")
                                else:
                                    print(f"⚠️ Default content may not match expected format for {script.script_type.value}")
                            else:
                                print(f"❌ Script file is empty: {script.name}")
                                return False
                        else:
                            print(f"❌ Script file not created: {script.name}")
                            return False
                
                print("✅ All imported scripts have default content")
                return True
            else:
                print("❌ No scripts were imported")
                return False
                
        finally:
            # Clean up
            if os.path.exists(json_file):
                os.unlink(json_file)
            
            # Clean up created script files
            scripts = script_manager.get_all_scripts()
            for script in scripts:
                if script.name in ["Test Windows No Content", "Test Linux No Content", "Test Device No Content"]:
                    if os.path.exists(script.script_path):
                        os.unlink(script.script_path)
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_import_creates_default_content()
    if success:
        print("\n✅ SUCCESS: JSON import correctly creates default content!")
    else:
        print("\n❌ FAILURE: Test failed")
    sys.exit(0 if success else 1)
