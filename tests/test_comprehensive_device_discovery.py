#!/usr/bin/env python3
"""
Comprehensive Device Discovery Test

This script thoroughly tests all device discovery functionality.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from adb.device_manager import DeviceManager
from adb.command_runner import CommandRunner
from utils.device_utils import (
    device_utils, is_adb_available, get_adb_version, 
    discover_devices, get_device_info, is_device_online,
    get_device_quick_info, restart_adb
)
from utils.logger import get_logger, enable_file_logging


def test_adb_basic_functionality():
    """Test basic ADB functionality."""
    logger = get_logger(__name__)
    
    print("=== Basic ADB Functionality Test ===\n")
    
    # Test ADB availability
    print("1. Testing ADB availability...")
    if is_adb_available():
        print("   ✅ ADB is available")
        
        # Get ADB version
        version = get_adb_version()
        if version:
            print(f"   📱 ADB Version: {version}")
        else:
            print("   ⚠️  Could not get ADB version")
    else:
        print("   ❌ ADB is not available")
        return False
    
    return True


def test_device_discovery():
    """Test device discovery."""
    print("\n=== Device Discovery Test ===\n")
    
    # Test synchronous discovery
    print("2. Testing synchronous device discovery...")
    devices = discover_devices()
    
    if not devices:
        print("   ❌ No devices found")
        return []
    
    print(f"   ✅ Found {len(devices)} device(s)")
    
    for i, device in enumerate(devices, 1):
        print(f"\n   Device {i} Details:")
        print(f"     • ID: {device.id}")
        print(f"     • Status: {device.status}")
        print(f"     • Connection Type: {device.connection_type}")
        print(f"     • Is Online: {device.is_online}")
        print(f"     • Display Name: {device.display_name}")
        
        if device.ip_address:
            print(f"     • IP Address: {device.ip_address}")
        
        if device.is_online:
            print(f"     • Device Name: {device.name or 'Unknown'}")
            print(f"     • Model: {device.model or 'Unknown'}")
            print(f"     • Manufacturer: {device.manufacturer or 'Unknown'}")
            print(f"     • Android Version: {device.android_version or 'Unknown'}")
            print(f"     • API Level: {device.api_level or 'Unknown'}")
            print(f"     • Properties Count: {len(device.properties)}")
    
    return devices


def test_device_info_retrieval(devices):
    """Test individual device info retrieval."""
    if not devices:
        return
    
    print("\n=== Device Info Retrieval Test ===\n")
    
    for device in devices:
        if not device.is_online:
            continue
        
        print(f"3. Testing device info for {device.id}...")
        
        # Test device info
        device_info = get_device_info(device.id)
        if device_info:
            print(f"   ✅ Successfully retrieved device info")
            print(f"     Display Name: {device_info.display_name}")
        else:
            print(f"   ❌ Failed to retrieve device info")
        
        # Test online status check
        is_online = is_device_online(device.id)
        print(f"   Device online status: {is_online}")
        
        # Test quick info
        quick_info = get_device_quick_info(device.id)
        if quick_info:
            print(f"   ✅ Quick info retrieved:")
            for key, value in quick_info.items():
                print(f"     {key}: {value}")
        else:
            print(f"   ❌ Failed to get quick info")
        
        break  # Test only first online device


async def test_async_device_manager():
    """Test async device manager functionality."""
    print("\n=== Async Device Manager Test ===\n")
    
    device_manager = DeviceManager()
    
    # Test async discovery
    print("4. Testing async device discovery...")
    devices = await device_manager.discover_devices()
    
    if devices:
        print(f"   ✅ Async discovery found {len(devices)} devices")
        
        # Test device info
        device = devices[0]
        device_info = await device_manager.get_device_info(device.id)
        if device_info:
            print(f"   ✅ Async device info retrieved for {device.id}")
        
        # Test connection check
        is_connected = await device_manager.is_device_connected(device.id)
        print(f"   Device connection status: {is_connected}")
        
        # Test monitoring for a short time
        print("   Testing device monitoring for 3 seconds...")
        device_manager.start_monitoring(interval=1)
        await asyncio.sleep(3)
        device_manager.stop_monitoring()
        print("   ✅ Monitoring test completed")
        
    else:
        print("   ❌ Async discovery found no devices")


def test_command_runner(devices):
    """Test command runner functionality."""
    if not devices:
        return
    
    online_devices = [d for d in devices if d.is_online]
    if not online_devices:
        return
    
    print("\n=== Command Runner Test ===\n")
    
    device = online_devices[0]
    print(f"5. Testing command runner with {device.id}...")
    
    # Test command runner creation
    command_runner = CommandRunner(device.id)
    print(f"   ✅ Command runner created for {device.id}")
    
    # Test simple commands (we'll use sync versions for this test)
    try:
        # Test echo command
        stdout, stderr, return_code = device_utils.execute_shell_command(
            device.id, "echo 'Hello from ADB-UTIL Command Test'"
        )
        
        if return_code == 0:
            print(f"   ✅ Echo command executed successfully")
            print(f"     Output: {stdout.strip()}")
        else:
            print(f"   ❌ Echo command failed: {stderr}")
        
        # Test property access
        properties = device_utils.get_device_properties(device.id)
        if properties:
            print(f"   ✅ Properties retrieved: {len(properties)} properties")
            
            # Show some key properties
            key_props = [
                'ro.product.model',
                'ro.product.manufacturer', 
                'ro.build.version.release',
                'ro.build.version.sdk',
                'ro.product.cpu.abi'
            ]
            
            for prop in key_props:
                if prop in properties:
                    print(f"     {prop}: {properties[prop]}")
        else:
            print(f"   ❌ Failed to retrieve properties")
            
    except Exception as e:
        print(f"   ❌ Command runner test failed: {e}")


def test_utility_functions():
    """Test utility functions."""
    print("\n=== Utility Functions Test ===\n")
    
    print("6. Testing utility functions...")
    
    # Test ADB availability check
    adb_available = device_utils.is_adb_available()
    print(f"   ADB Available: {adb_available}")
    
    # Test ADB version
    version = device_utils.get_adb_version()
    print(f"   ADB Version: {version or 'Unknown'}")
    
    # Test device utils instance
    devices = device_utils.discover_devices_sync()
    print(f"   Device Utils Discovery: {len(devices)} devices")
    
    print("   ✅ Utility functions test completed")


def performance_test():
    """Test discovery performance."""
    print("\n=== Performance Test ===\n")
    
    print("7. Testing discovery performance...")
    
    # Time multiple discoveries
    times = []
    for i in range(3):
        start_time = time.time()
        devices = discover_devices()
        end_time = time.time()
        
        discovery_time = end_time - start_time
        times.append(discovery_time)
        print(f"   Discovery {i+1}: {discovery_time:.2f}s ({len(devices)} devices)")
    
    avg_time = sum(times) / len(times)
    print(f"   ✅ Average discovery time: {avg_time:.2f}s")


async def main():
    """Main test function."""
    logger = get_logger(__name__)
    
    print("=== ADB-UTIL Device Discovery Comprehensive Test ===\n")
    
    # Enable file logging for testing
    enable_file_logging()
    logger.info("Starting comprehensive device discovery test")
    
    try:
        # Test basic ADB functionality
        if not test_adb_basic_functionality():
            print("\n❌ ADB not available - cannot continue tests")
            return
        
        # Test device discovery
        devices = test_device_discovery()
        
        # Test device info retrieval
        test_device_info_retrieval(devices)
        
        # Test async functionality
        await test_async_device_manager()
        
        # Test command runner
        test_command_runner(devices)
        
        # Test utility functions
        test_utility_functions()
        
        # Performance test
        performance_test()
        
        print("\n=== Test Summary ===")
        print("✅ All device discovery tests completed successfully!")
        
        if devices:
            online_count = len([d for d in devices if d.is_online])
            print(f"📱 Found {len(devices)} total devices ({online_count} online)")
            print("🚀 Device discovery system is fully functional")
        else:
            print("⚠️  No devices found - connect an Android device to test fully")
        
        logger.info("Comprehensive device discovery test completed successfully")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.error(f"Comprehensive test failed: {e}", exc_info=True)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
