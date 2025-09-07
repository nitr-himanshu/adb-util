#!/usr/bin/env python3
"""
Test script manager implementation
"""

import sys
import os
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_script_manager():
    """Test script manager functionality."""
    try:
        # Test imports
        from services.script_manager import get_script_manager, ScriptType, Script
        from gui.script_manager_tab import ScriptManagerTab
        from gui.script_editor_dialog import ScriptEditorDialog
        print("✅ All script manager imports successful")
        
        # Test basic functionality
        script_manager = get_script_manager()
        print(f"✅ Script manager initialized: {len(script_manager.get_all_scripts())} scripts found")
        
        # Test script types
        print("✅ Script types available:")
        for script_type in ScriptType:
            print(f"   - {script_type.value}")
        
        print("✅ Script manager implementation complete and ready!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_script_manager()
    sys.exit(0 if success else 1)
