#!/usr/bin/env python3
"""
Test script for device discovery functionality.

This script tests the device discovery logic implementation.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from adb.device_manager import DeviceManager
from adb.command_runner import CommandRunner
from utils.logger import get_logger, enable_file_logging


async def test_device_discovery():
    """Test device discovery functionality."""
    logger = get_logger(__name__)
    
    print("=== ADB-UTIL Device Discovery Test ===\n")
    
    # Enable file logging for testing
    enable_file_logging()
    logger.info("Starting device discovery test")
    
    # Create device manager
    device_manager = DeviceManager()
    
    # Test ADB availability
    print("1. Testing ADB availability...")
    if device_manager.is_adb_available():
        print("   ✅ ADB is available")
        logger.info("ADB is available")
    else:
        print("   ❌ ADB is not available")
        logger.error("ADB is not available")
        print("\n   Please ensure ADB is installed and in your PATH.")
        print("   You can download ADB from: https://developer.android.com/studio/releases/platform-tools")
        return
    
    # Test device discovery
    print("\n2. Discovering devices...")
    devices = await device_manager.discover_devices()
    
    if not devices:
        print("   ❌ No devices found")
        logger.warning("No devices found")
        print("\n   Tips:")
        print("   - Connect an Android device via USB")
        print("   - Enable USB debugging on the device")
        print("   - Run 'adb devices' manually to check connection")
    else:
        print(f"   ✅ Found {len(devices)} device(s)")
        logger.info(f"Found {len(devices)} devices")
        
        for i, device in enumerate(devices, 1):
            print(f"\n   Device {i}:")
            print(f"     ID: {device.id}")
            print(f"     Status: {device.status}")
            print(f"     Connection: {device.connection_type}")
            if device.ip_address:
                print(f"     IP Address: {device.ip_address}")
            print(f"     Online: {device.is_online}")
            print(f"     Display Name: {device.display_name}")
            
            if device.is_online:
                print(f"     Name: {device.name or 'Unknown'}")
                print(f"     Model: {device.model or 'Unknown'}")
                print(f"     Manufacturer: {device.manufacturer or 'Unknown'}")
                print(f"     Android Version: {device.android_version or 'Unknown'}")
                print(f"     API Level: {device.api_level or 'Unknown'}")
    
    # Test command runner if devices available
    online_devices = [d for d in devices if d.is_online]
    if online_devices:
        print("\n3. Testing command execution...")
        device = online_devices[0]
        command_runner = CommandRunner(device.id)
        
        # Test simple command
        print(f"   Testing simple command on {device.id}...")
        stdout, stderr, return_code = await command_runner.execute_shell_command("echo 'Hello from ADB-UTIL'")
        
        if return_code == 0:
            print(f"   ✅ Command executed successfully")
            print(f"     Output: {stdout.strip()}")
        else:
            print(f"   ❌ Command failed with return code {return_code}")
            print(f"     Error: {stderr}")
        
        # Test property retrieval
        print(f"   Testing property retrieval...")
        properties = await command_runner.get_device_properties()
        
        if properties:
            print(f"   ✅ Retrieved {len(properties)} device properties")
            # Show some interesting properties
            interesting_props = [
                'ro.product.model',
                'ro.product.manufacturer',
                'ro.build.version.release',
                'ro.build.version.sdk'
            ]
            for prop in interesting_props:
                if prop in properties:
                    print(f"     {prop}: {properties[prop]}")
        else:
            print(f"   ❌ Failed to retrieve device properties")
    
    # Test monitoring (short test)
    if devices:
        print("\n4. Testing device monitoring (5 seconds)...")
        device_manager.start_monitoring(interval=2)
        await asyncio.sleep(5)
        device_manager.stop_monitoring()
        print("   ✅ Monitoring test completed")
    
    print("\n=== Test completed ===")
    logger.info("Device discovery test completed")


async def test_specific_functions():
    """Test specific device manager functions."""
    logger = get_logger(__name__)
    device_manager = DeviceManager()
    
    print("\n=== Testing Specific Functions ===")
    
    # Test device info retrieval
    devices = await device_manager.discover_devices()
    if devices:
        device_id = devices[0].id
        print(f"\n5. Testing device info retrieval for {device_id}...")
        
        device_info = await device_manager.get_device_info(device_id)
        if device_info:
            print(f"   ✅ Successfully retrieved device info")
            print(f"     Display Name: {device_info.display_name}")
        else:
            print(f"   ❌ Failed to retrieve device info")
        
        # Test connection check
        print(f"\n6. Testing connection check for {device_id}...")
        is_connected = await device_manager.is_device_connected(device_id)
        print(f"   Device connected: {is_connected}")
        
        # Test getting connected devices
        print(f"\n7. Testing get connected devices...")
        connected = device_manager.get_connected_devices()
        print(f"   Connected devices: {len(connected)}")
        
        # Test device lookup
        print(f"\n8. Testing device lookup...")
        found_device = device_manager.get_device_by_id(device_id)
        if found_device:
            print(f"   ✅ Found device: {found_device.display_name}")
        else:
            print(f"   ❌ Device not found in connected devices")


if __name__ == "__main__":
    try:
        asyncio.run(test_device_discovery())
        asyncio.run(test_specific_functions())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
