"""
Device Utilities

Utility functions for device operations and management.
"""

import subprocess
import re
from typing import List, Optional, Dict, Tuple
from datetime import datetime

from models.device import Device
from utils.logger import get_logger
from utils.constants import (
    ADB_DEVICES_COMMAND, 
    CONNECTION_TCPIP, 
    CONNECTION_USB,
    DEVICE_STATE_DEVICE,
    COMMAND_TIMEOUT
)


class DeviceUtils:
    """Utility class for device operations."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def is_adb_available(self) -> bool:
        """Check if ADB is available in the system."""
        try:
            result = subprocess.run(
                ["adb", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_adb_version(self) -> Optional[str]:
        """Get ADB version string."""
        try:
            result = subprocess.run(
                ["adb", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Extract version from output like "Android Debug Bridge version 1.0.41"
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'version' in line.lower():
                        return line.strip()
            return None
        except Exception:
            return None
    
    def discover_devices_sync(self) -> List[Device]:
        """Synchronously discover devices."""
        devices = []
        
        try:
            # Execute adb devices command
            result = subprocess.run(
                ADB_DEVICES_COMMAND,
                shell=True,
                capture_output=True,
                text=True,
                timeout=COMMAND_TIMEOUT
            )
            
            if result.returncode != 0:
                self.logger.error(f"ADB devices command failed: {result.stderr}")
                return []
            
            # Parse device list
            devices = self._parse_device_list(result.stdout)
            
            # Get detailed info for online devices
            for device in devices:
                if device.is_online:
                    try:
                        self._populate_device_info_sync(device)
                    except Exception as e:
                        self.logger.warning(f"Failed to get info for device {device.id}: {e}")
            
            self.logger.info(f"Discovered {len(devices)} devices")
            return devices
            
        except Exception as e:
            self.logger.error(f"Device discovery failed: {e}")
            return []
    
    def get_device_info_sync(self, device_id: str) -> Optional[Device]:
        """Get device information synchronously."""
        try:
            # First check if device exists
            devices = self.discover_devices_sync()
            device = next((d for d in devices if d.id == device_id), None)
            
            if not device:
                self.logger.warning(f"Device {device_id} not found")
                return None
            
            return device
            
        except Exception as e:
            self.logger.error(f"Failed to get device info for {device_id}: {e}")
            return None
    
    def is_device_online(self, device_id: str) -> bool:
        """Check if a specific device is online."""
        try:
            result = subprocess.run(
                f"adb -s {device_id} get-state",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 and result.stdout.strip() == "device"
        except Exception:
            return False
    
    def execute_adb_command(self, device_id: str, command: str, timeout: int = COMMAND_TIMEOUT) -> Tuple[str, str, int]:
        """Execute ADB command on specific device."""
        full_command = f"adb -s {device_id} {command}"
        
        try:
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return (
                result.stdout,
                result.stderr,
                result.returncode
            )
            
        except subprocess.TimeoutExpired:
            return "", f"Command timeout after {timeout}s", -1
        except Exception as e:
            return "", str(e), -1
    
    def execute_shell_command(self, device_id: str, command: str, timeout: int = COMMAND_TIMEOUT) -> Tuple[str, str, int]:
        """Execute shell command on device."""
        return self.execute_adb_command(device_id, f"shell {command}", timeout)
    
    def get_device_properties(self, device_id: str) -> Dict[str, str]:
        """Get device properties."""
        stdout, stderr, return_code = self.execute_shell_command(device_id, "getprop")
        
        if return_code != 0:
            self.logger.error(f"Failed to get device properties: {stderr}")
            return {}
        
        return self._parse_properties(stdout)
    
    def get_device_info_quick(self, device_id: str) -> Dict[str, str]:
        """Get quick device info (model, manufacturer, version)."""
        properties = self.get_device_properties(device_id)
        
        return {
            'model': properties.get('ro.product.model', 'Unknown'),
            'manufacturer': properties.get('ro.product.manufacturer', 'Unknown'),
            'android_version': properties.get('ro.build.version.release', 'Unknown'),
            'api_level': properties.get('ro.build.version.sdk', 'Unknown'),
            'device_name': properties.get('ro.product.device', 'Unknown'),
            'build_id': properties.get('ro.build.id', 'Unknown'),
            'serial': properties.get('ro.serialno', device_id)
        }
    
    def restart_adb_server(self) -> bool:
        """Restart ADB server."""
        try:
            # Kill server
            subprocess.run(["adb", "kill-server"], capture_output=True, timeout=10)
            # Start server
            result = subprocess.run(["adb", "start-server"], capture_output=True, timeout=10)
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Failed to restart ADB server: {e}")
            return False
    
    def connect_tcpip_device(self, ip_address: str, port: int = 5555) -> bool:
        """Connect to device over TCP/IP."""
        try:
            result = subprocess.run(
                f"adb connect {ip_address}:{port}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0 and "connected" in result.stdout.lower()
        except Exception as e:
            self.logger.error(f"Failed to connect to {ip_address}:{port}: {e}")
            return False
    
    def disconnect_tcpip_device(self, device_id: str) -> bool:
        """Disconnect TCP/IP device."""
        try:
            result = subprocess.run(
                f"adb disconnect {device_id}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Failed to disconnect {device_id}: {e}")
            return False
    
    def _parse_device_list(self, output: str) -> List[Device]:
        """Parse output from 'adb devices' command."""
        devices = []
        lines = output.strip().split('\n')
        
        # Skip the header line "List of devices attached"
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            # Parse device line format: "device_id    status"
            parts = line.split('\t')
            if len(parts) >= 2:
                device_id = parts[0].strip()
                status = parts[1].strip()
                
                # Create device object
                device = Device(
                    id=device_id,
                    status=status,
                    last_seen=datetime.now()
                )
                
                # Determine connection type
                if ':' in device_id and device_id.count(':') == 1:
                    device.connection_type = CONNECTION_TCPIP
                    device.ip_address = device_id.split(':')[0]
                else:
                    device.connection_type = CONNECTION_USB
                
                devices.append(device)
                self.logger.debug(f"Found device: {device_id} ({status})")
        
        return devices
    
    def _populate_device_info_sync(self, device: Device):
        """Populate detailed device information synchronously."""
        if not device.is_online:
            return
        
        try:
            properties = self.get_device_properties(device.id)
            device.properties.update(properties)
            
            # Extract common properties
            device.name = properties.get('ro.product.model', device.name)
            device.model = properties.get('ro.product.device', device.model)
            device.manufacturer = properties.get('ro.product.manufacturer', device.manufacturer)
            device.android_version = properties.get('ro.build.version.release', device.android_version)
            
            # Parse API level
            api_level_str = properties.get('ro.build.version.sdk')
            if api_level_str and api_level_str.isdigit():
                device.api_level = int(api_level_str)
            
            self.logger.debug(f"Updated device info for {device.id}: {device.display_name}")
        
        except Exception as e:
            self.logger.warning(f"Failed to populate info for device {device.id}: {e}")
    
    def _parse_properties(self, output: str) -> Dict[str, str]:
        """Parse device properties from getprop output."""
        properties = {}
        
        # Pattern matches: [property.name]: [value]
        pattern = r'\[([^\]]+)\]:\s*\[([^\]]*)\]'
        
        for match in re.finditer(pattern, output):
            prop_name = match.group(1)
            prop_value = match.group(2)
            properties[prop_name] = prop_value
        
        return properties


# Global device utils instance
device_utils = DeviceUtils()


# Convenience functions
def is_adb_available() -> bool:
    """Check if ADB is available."""
    return device_utils.is_adb_available()


def get_adb_version() -> Optional[str]:
    """Get ADB version."""
    return device_utils.get_adb_version()


def discover_devices() -> List[Device]:
    """Discover all devices."""
    return device_utils.discover_devices_sync()


def get_device_info(device_id: str) -> Optional[Device]:
    """Get device information."""
    return device_utils.get_device_info_sync(device_id)


def is_device_online(device_id: str) -> bool:
    """Check if device is online."""
    return device_utils.is_device_online(device_id)


def get_device_quick_info(device_id: str) -> Dict[str, str]:
    """Get quick device info."""
    return device_utils.get_device_info_quick(device_id)


def restart_adb() -> bool:
    """Restart ADB server."""
    return device_utils.restart_adb_server()
