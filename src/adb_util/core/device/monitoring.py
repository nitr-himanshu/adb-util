"""
Device monitoring functionality.

This module handles continuous monitoring of device connection status.
"""

from typing import List, Dict, Callable, Optional
import asyncio
from datetime import datetime

from ...models.device import Device
from ...utils.logger import get_logger
from ...utils.constants import DEVICE_MONITORING_INTERVAL


class DeviceMonitoring:
    """Handles continuous monitoring of device connections."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable[[List[Device]], None]] = []
    
    def start_monitoring(self, interval: int = DEVICE_MONITORING_INTERVAL, 
                        callback: Optional[Callable[[List[Device]], None]] = None):
        """Start monitoring device connections."""
        if self._monitoring:
            self.logger.warning("Device monitoring is already running")
            return
        
        if callback:
            self._callbacks.append(callback)
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_devices(interval))
        self.logger.info(f"Device monitoring started with {interval}s interval")
    
    def stop_monitoring(self):
        """Stop monitoring device connections."""
        if not self._monitoring:
            return
        
        self._monitoring = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
        
        self.logger.info("Device monitoring stopped")
    
    def add_callback(self, callback: Callable[[List[Device]], None]):
        """Add a callback function to be called when devices change."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[List[Device]], None]):
        """Remove a callback function."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    async def _monitor_devices(self, interval: int):
        """Monitor device connections in a loop."""
        previous_devices: Dict[str, Device] = {}
        
        while self._monitoring:
            try:
                # This would typically call the discovery service
                # For now, we'll just simulate the monitoring
                current_devices = {}  # Would be populated by discovery
                
                # Check for changes
                if current_devices != previous_devices:
                    device_list = list(current_devices.values())
                    await self._notify_callbacks(device_list)
                    previous_devices = current_devices.copy()
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                self.logger.info("Device monitoring cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in device monitoring: {e}")
                await asyncio.sleep(interval)
    
    async def _notify_callbacks(self, devices: List[Device]):
        """Notify all registered callbacks of device changes."""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(devices)
                else:
                    callback(devices)
            except Exception as e:
                self.logger.error(f"Error in device monitoring callback: {e}")
    
    @property
    def is_monitoring(self) -> bool:
        """Check if monitoring is currently active."""
        return self._monitoring
