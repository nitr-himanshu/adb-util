#!/usr/bin/env python3
"""Test file operations and directory listing."""

import sys
import asyncio
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def test_file_operations():
    try:
        from adb.file_operations import FileOperations
        
        # Test with a common device ID (you might need to change this)
        device_id = "emulator-5554"  # Change this to your actual device ID
        
        print(f"Testing file operations with device: {device_id}")
        
        file_ops = FileOperations(device_id)
        
        # Test connection
        print("Testing device connection...")
        connection_ok = await file_ops.test_device_connection()
        print(f"Connection test: {'✅ PASSED' if connection_ok else '❌ FAILED'}")
        
        if not connection_ok:
            print("Cannot proceed without device connection")
            return False
        
        # Test directory listing
        print("\nTesting directory listing...")
        test_paths = ["/", "/sdcard/", "/system/", "/data/"]
        
        for path in test_paths:
            try:
                print(f"\nListing {path}:")
                files = await file_ops.list_directory(path)
                print(f"Found {len(files)} items")
                
                if files:
                    print("First 5 items:")
                    for i, file_info in enumerate(files[:5]):
                        icon = "📁" if file_info.is_directory else "📄"
                        print(f"  {icon} {file_info.name}")
                else:
                    print("  No files found or access denied")
                    
            except Exception as e:
                print(f"  Error listing {path}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Testing ADB File Operations")
    print("=" * 40)
    
    # Run the async test
    result = asyncio.run(test_file_operations())
    
    if result:
        print("\n🎉 File operations test completed!")
    else:
        print("\n❌ File operations test failed!")
        print("\nTroubleshooting:")
        print("1. Make sure ADB is installed and in your PATH")
        print("2. Make sure your device is connected and authorized")
        print("3. Run 'adb devices' to check device status")
        print("4. Update the device_id in this script if needed")
