"""
Device Manager

Device discovery, connection management, and status monitoring.
"""

from typing import List, Optional, Dict
import asyncio
import subprocess
import re
from datetime import datetime

from models.device import Device
from utils.logger import get_logger, log_device_operation
from utils.constants import (
    ADB_DEVICES_COMMAND, 
    DEVICE_DISCOVERY_TIMEOUT,
    COMMAND_TIMEOUT,
    CONNECTION_TCPIP,
    CONNECTION_USB,
    DEVICE_MONITORING_INTERVAL
)


class DeviceManager:
    """Manages ADB device discovery and connections."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.devices: List[Device] = []
        self.connected_devices: Dict[str, Device] = {}
        self._monitoring = False
        self._monitor_task = None
        
        self.logger.info("Device manager initialized")
    
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
            
            self.devices = devices
            self.connected_devices = {d.id: d for d in devices if d.is_online}
            
            self.logger.info(f"Device discovery completed. Found {len(devices)} devices, {len(self.connected_devices)} online")
            log_device_operation("all", "discover", f"Found {len(devices)} devices")
            
            return devices
            
        except Exception as e:
            self.logger.error(f"Device discovery failed: {e}")
            return []
    
    async def get_device_info(self, device_id: str) -> Optional[Device]:
        """Get detailed information about a specific device."""
        self.logger.debug(f"Retrieving device info for: {device_id}")
        log_device_operation(device_id, "get_info", "Retrieving device information")
        
        try:
            # Check if device exists in our list
            device = next((d for d in self.devices if d.id == device_id), None)
            if not device:
                self.logger.warning(f"Device {device_id} not found in device list")
                return None
            
            # Refresh device information
            await self._populate_device_info(device)
            return device
            
        except Exception as e:
            self.logger.error(f"Failed to get device info for {device_id}: {e}")
            return None
    
    async def is_device_connected(self, device_id: str) -> bool:
        """Check if device is currently connected."""
        try:
            devices = await self.discover_devices()
            return any(d.id == device_id and d.is_online for d in devices)
        except Exception as e:
            self.logger.error(f"Failed to check connection for device {device_id}: {e}")
            return False
    
    def start_monitoring(self, interval: int = DEVICE_MONITORING_INTERVAL):
        """Start monitoring for device connect/disconnect events."""
        if self._monitoring:
            self.logger.warning("Device monitoring is already running")
            return
        
        self.logger.info(f"Starting device monitoring with {interval}s interval")
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_devices(interval))
    
    def stop_monitoring(self):
        """Stop monitoring for device events."""
        if not self._monitoring:
            return
        
        self.logger.info("Stopping device monitoring")
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
    
    async def _monitor_devices(self, interval: int):
        """Monitor devices for changes."""
        previous_devices = set()
        
        while self._monitoring:
            try:
                current_devices = await self.discover_devices()
                current_device_ids = set(d.id for d in current_devices if d.is_online)
                
                # Check for new devices
                new_devices = current_device_ids - previous_devices
                for device_id in new_devices:
                    self.logger.info(f"Device connected: {device_id}")
                    log_device_operation(device_id, "connect", "Device connected")
                
                # Check for disconnected devices
                disconnected_devices = previous_devices - current_device_ids
                for device_id in disconnected_devices:
                    self.logger.info(f"Device disconnected: {device_id}")
                    log_device_operation(device_id, "disconnect", "Device disconnected")
                
                previous_devices = current_device_ids
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error during device monitoring: {e}")
                await asyncio.sleep(interval)
    
    def get_connected_devices(self) -> List[Device]:
        """Get list of currently connected devices."""
        return list(self.connected_devices.values())
    
    def get_device_by_id(self, device_id: str) -> Optional[Device]:
        """Get device by ID from current device list."""
        return self.connected_devices.get(device_id)
    
    async def _execute_adb_command(self, command: str, timeout: int = COMMAND_TIMEOUT) -> Optional[tuple]:
        """Execute ADB command and return result."""
        try:
            self.logger.debug(f"Executing: {command}")
            
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
                stdout.decode('utf-8', errors='ignore'),
                stderr.decode('utf-8', errors='ignore'),
                process.returncode
            )
            
        except asyncio.TimeoutError:
            self.logger.error(f"Command timeout after {timeout}s: {command}")
            return None
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return None
    
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
    
    async def _populate_device_info(self, device: Device):
        """Populate detailed device information."""
        if not device.is_online:
            return
        
        try:
            # Get device properties
            props_result = await self._execute_adb_command(
                f"adb -s {device.id} shell getprop"
            )
            
            if props_result and props_result[2] == 0:
                properties = self._parse_device_properties(props_result[0])
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
    
    def _parse_device_properties(self, output: str) -> Dict[str, str]:
        """Parse device properties from getprop output."""
        properties = {}
        
        # Pattern matches: [property.name]: [value]
        pattern = r'\[([^\]]+)\]:\s*\[([^\]]*)\]'
        
        for match in re.finditer(pattern, output):
            prop_name = match.group(1)
            prop_value = match.group(2)
            properties[prop_name] = prop_value
        
        return properties
    
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
