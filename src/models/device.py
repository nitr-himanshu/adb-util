"""
Device Data Model

Data model for Android devices connected via ADB.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class Device:
    """Represents an Android device connected via ADB."""
    
    id: str
    name: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    android_version: Optional[str] = None
    api_level: Optional[int] = None
    status: str = "unknown"  # online, offline, unauthorized, etc.
    connection_type: str = "usb"  # usb, tcpip
    ip_address: Optional[str] = None
    last_seen: Optional[datetime] = None
    properties: Dict[str, str] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
        if self.last_seen is None:
            self.last_seen = datetime.now()
    
    @property
    def is_online(self) -> bool:
        """Check if device is online and accessible."""
        return self.status == "device"
    
    @property
    def display_name(self) -> str:
        """Get display name for the device."""
        if self.name:
            return f"{self.name} ({self.id})"
        elif self.model:
            return f"{self.model} ({self.id})"
        else:
            return self.id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert device to dictionary."""
        # TODO: Implement dictionary conversion
        pass
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Device':
        """Create device from dictionary."""
        # TODO: Implement device creation from dict
        pass
