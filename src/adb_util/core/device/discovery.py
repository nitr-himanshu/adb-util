"""
Device discovery functionality.

This module handles the discovery and enumeration of ADB devices.
"""

from typing import List, Optional, Dict
import asyncio
import subprocess
import re
from datetime import datetime

from ...models.device import Device
from ...utils.logger import get_logger, log_device_operation
from ...utils.constants import (
    ADB_DEVICES_COMMAND, 
    DEVICE_DISCOVERY_TIMEOUT,
    COMMAND_TIMEOUT,
    CONNECTION_TCPIP,
    CONNECTION_USB,
)


class DeviceDiscovery:
    """Handles ADB device discovery and enumeration."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def discover_devices(self) -> List[Device]:
        """Discover all available ADB devices."""
        self.logger.info("Starting device discovery...")
        
        try:
            # Execute adb devices command
            result = await self._execute_adb_command(ADB_DEVICES_COMMAND, timeout=DEVICE_DISCOVERY_TIMEOUT)
            
            if result is None:
                self.logger.error("Failed to execute adb devices command")
                return []
            
            stdout, stderr, return_code = result
            
            if return_code != 0:
                self.logger.error(f"ADB devices command failed: {stderr}")
                return []
            
            # Parse device list
            devices = self._parse_device_list(stdout)
            
            # Get detailed info for each device
            for device in devices:
                try:
                    await self._populate_device_info(device)
                except Exception as e:
                    self.logger.warning(f"Failed to get info for device {device.id}: {e}")
            
            self.logger.info(f"Device discovery completed. Found {len(devices)} devices")
            log_device_operation("all", "discover", f"Found {len(devices)} devices")
            
            return devices
            
        except Exception as e:
            self.logger.error(f"Device discovery failed: {e}")
            return []
    
    async def get_device_info(self, device_id: str) -> Optional[Device]:
        """Get detailed information for a specific device."""
        try:
            # Create a temporary device object
            device = Device(id=device_id, status="device")
            await self._populate_device_info(device)
            return device
        except Exception as e:
            self.logger.error(f"Failed to get device info for {device_id}: {e}")
            return None
    
    async def _execute_adb_command(self, command: str, timeout: int = COMMAND_TIMEOUT) -> Optional[tuple]:
        """Execute an ADB command and return the result."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            return (
                stdout.decode('utf-8', errors='ignore').strip(),
                stderr.decode('utf-8', errors='ignore').strip(),
                process.returncode
            )
            
        except asyncio.TimeoutError:
            self.logger.error(f"ADB command timeout: {command}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to execute ADB command '{command}': {e}")
            return None
    
    def _parse_device_list(self, output: str) -> List[Device]:
        """Parse the output of 'adb devices' command."""
        devices = []
        lines = output.strip().split('\n')[1:]  # Skip header line
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split('\t')
            if len(parts) >= 2:
                device_id = parts[0]
                status = parts[1]
                
                # Determine connection type
                connection_type = CONNECTION_USB
                if ':' in device_id and '.' in device_id:
                    connection_type = CONNECTION_TCPIP
                
                device = Device(
                    id=device_id,
                    status=status,
                    connection_type=connection_type,
                    discovered_at=datetime.now()
                )
                devices.append(device)
        
        return devices
    
    async def _populate_device_info(self, device: Device):
        """Populate detailed device information."""
        if not device.is_online:
            return
        
        # Get device properties
        properties_cmd = f"adb -s {device.id} shell getprop"
        result = await self._execute_adb_command(properties_cmd)
        
        if result and result[2] == 0:
            properties = self._parse_device_properties(result[0])
            device.model = properties.get('ro.product.model', 'Unknown')
            device.brand = properties.get('ro.product.brand', 'Unknown')
            device.android_version = properties.get('ro.build.version.release', 'Unknown')
            device.api_level = properties.get('ro.build.version.sdk', 'Unknown')
            device.manufacturer = properties.get('ro.product.manufacturer', 'Unknown')
            device.serial = properties.get('ro.serialno', device.id)
        
        # Get battery info
        battery_cmd = f"adb -s {device.id} shell dumpsys battery"
        result = await self._execute_adb_command(battery_cmd)
        
        if result and result[2] == 0:
            battery_info = self._extract_battery_info(result[0])
            device.battery_level = battery_info.get('level', 'Unknown')
            device.battery_status = battery_info.get('status', 'Unknown')
    
    def _parse_device_properties(self, output: str) -> Dict[str, str]:
        """Parse device properties from getprop output."""
        properties = {}
        for line in output.split('\n'):
            line = line.strip()
            if ':' in line:
                try:
                    key, value = line.split(':', 1)
                    key = key.strip('[]')
                    value = value.strip('[]')
                    properties[key] = value
                except ValueError:
                    continue
        return properties
    
    def _extract_battery_info(self, output: str) -> Dict[str, str]:
        """Extract battery information from dumpsys battery output."""
        battery_info = {}
        for line in output.split('\n'):
            line = line.strip()
            if ':' in line:
                try:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if key == 'level':
                        battery_info['level'] = f"{value}%"
                    elif key == 'status':
                        battery_info['status'] = value
                except ValueError:
                    continue
        return battery_info
