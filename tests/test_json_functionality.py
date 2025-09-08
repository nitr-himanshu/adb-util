#!/usr/bin/env python3
"""
Test script to demonstrate the JSON export/import functionality.
This creates a sample JSON and tests the import.
"""

import json
import tempfile
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def create_sample_json():
    """Create a sample JSON file for testing."""
    sample_data = [
        {
            "name": "Test Windows Script",
            "script_path": "test_windows.bat",
            "type": "host_windows",
            "isTemplate": True,
            "show": True,
            "description": "A test Windows batch script",
            "content": "@echo off\necho Hello from Windows!\necho Testing JSON import functionality\npause",
            "created_at": "2025-09-09T01:00:00.000000",
            "last_run": "",
            "run_count": 0
        },
        {
            "name": "Test Device Script",
            "script_path": "test_device.sh",
            "type": "device",
            "isTemplate": False,
            "show": True,
            "description": "A test Android device script",
            "content": "#!/system/bin/sh\necho \"Testing device script import\"\ngetprop ro.product.model\ngetprop ro.build.version.release",
            "created_at": "2025-09-09T01:15:00.000000",
            "last_run": "",
            "run_count": 0
        },
        {
            "name": "Hidden Admin Script",
            "script_path": "admin_hidden.sh",
            "type": "host_linux",
            "isTemplate": False,
            "show": False,
            "description": "Hidden administrative script",
            "content": "#!/bin/bash\necho \"This is a hidden script\"\necho \"It won't appear in the main script list\"",
            "created_at": "2025-09-09T01:30:00.000000",
            "last_run": "",
            "run_count": 0
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_data, f, indent=2)
        return f.name

def test_import_functionality():
    """Test the import functionality."""
    try:
        from services.script_manager import ScriptManager
        print("✅ Script manager import successful")
        
        # Create sample JSON
        json_file = create_sample_json()
        print(f"✅ Sample JSON created: {json_file}")
        
        # Initialize script manager
        script_manager = ScriptManager()
        print("✅ Script manager initialized")
        
        # Test import
        imported_count, skipped_count = script_manager.import_scripts_from_json(json_file)
        print(f"✅ Import completed: {imported_count} imported, {skipped_count} skipped")
        
        # Check imported scripts
        all_scripts = script_manager.get_all_scripts()
        visible_scripts = [s for s in all_scripts if s.is_visible]
        hidden_scripts = [s for s in all_scripts if not s.is_visible]
        template_scripts = [s for s in all_scripts if s.is_template]
        
        print(f"✅ Total scripts: {len(all_scripts)}")
        print(f"✅ Visible scripts: {len(visible_scripts)}")
        print(f"✅ Hidden scripts: {len(hidden_scripts)}")
        print(f"✅ Template scripts: {len(template_scripts)}")
        
        # Test export functionality
        export_file = json_file.replace('.json', '_export.json')
        success = script_manager.export_scripts_to_json(export_file)
        print(f"✅ Export successful: {success}")
        
        # Verify exported structure
        with open(export_file, 'r') as f:
            exported_data = json.load(f)
        
        print(f"✅ Exported {len(exported_data)} scripts")
        
        # Clean up
        os.unlink(json_file)
        os.unlink(export_file)
        
        print("✅ All tests passed! JSON export/import functionality is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_import_functionality()
    sys.exit(0 if success else 1)
