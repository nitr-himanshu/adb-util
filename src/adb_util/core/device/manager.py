"""
Device manager - coordinates device discovery and monitoring.

This module provides the main interface for device management, combining
discovery and monitoring functionality.
"""

from typing import List, Optional, Dict
from datetime import datetime

from ...models.device import Device
from ...utils.logger import get_logger
from .discovery import DeviceDiscovery
from .monitoring import DeviceMonitoring


class DeviceManager:
    """Main device manager that coordinates discovery and monitoring."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.devices: List[Device] = []
        self.connected_devices: Dict[str, Device] = {}
        
        # Initialize components
        self.discovery = DeviceDiscovery()
        self.monitoring = DeviceMonitoring()
        
        self.logger.info("Device manager initialized")
    
    async def discover_devices(self) -> List[Device]:
        """Discover all available ADB devices."""
        devices = await self.discovery.discover_devices()
        self.devices = devices
        self.connected_devices = {d.id: d for d in devices if d.is_online}
        return devices
    
    async def get_device_info(self, device_id: str) -> Optional[Device]:
        """Get detailed information for a specific device."""
        return await self.discovery.get_device_info(device_id)
    
    async def is_device_connected(self, device_id: str) -> bool:
        """Check if a device is currently connected."""
        return device_id in self.connected_devices
    
    def start_monitoring(self, interval: int = 5):
        """Start monitoring device connections."""
        self.monitoring.start_monitoring(interval, self._on_devices_changed)
    
    def stop_monitoring(self):
        """Stop monitoring device connections."""
        self.monitoring.stop_monitoring()
    
    def get_connected_devices(self) -> List[Device]:
        """Get list of currently connected devices."""
        return list(self.connected_devices.values())
    
    def get_device_by_id(self, device_id: str) -> Optional[Device]:
        """Get a device by its ID."""
        return self.connected_devices.get(device_id)
    
    def _on_devices_changed(self, devices: List[Device]):
        """Callback for when device list changes."""
        self.devices = devices
        self.connected_devices = {d.id: d for d in devices if d.is_online}
        self.logger.info(f"Device list updated: {len(devices)} total, {len(self.connected_devices)} connected")
