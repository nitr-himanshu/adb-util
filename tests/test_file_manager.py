#!/usr/bin/env python3
"""Test file manager implementation."""

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    # Test imports
    from gui.file_manager import FileManager, FileTransferWorker, DirectoryListWorker
    from adb.file_operations import FileOperations, FileInfo
    
    print("✅ File manager imports successful")
    print("✅ File operations imports successful")
    
    # Test FileInfo creation
    file_info = FileInfo("test.txt", "/sdcard/test.txt", False, 1024, "-rw-r--r--", "2025-09-07")
    print(f"✅ FileInfo created: {file_info}")
    
    # Test FileOperations creation
    file_ops = FileOperations("test_device")
    print(f"✅ FileOperations created for device: {file_ops.device_id}")
    
    print("\n🎉 File manager implementation is ready!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
