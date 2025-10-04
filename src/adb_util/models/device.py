"""
Device Data Model

Data model for Android devices connected via ADB.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

from ..utils.constants import (
    DEVICE_STATE_DEVICE,
    DEVICE_STATE_UNKNOWN,
    CONNECTION_USB
)


@dataclass
class Device:
    """Represents an Android device connected via ADB."""
    
    id: str
    name: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    android_version: Optional[str] = None
    api_level: Optional[int] = None
    status: str = DEVICE_STATE_UNKNOWN  # online, offline, unauthorized, etc.
    connection_type: str = CONNECTION_USB  # usb, tcpip
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
        return self.status == DEVICE_STATE_DEVICE
    
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
        return {
            'id': self.id,
            'name': self.name,
            'model': self.model,
            'manufacturer': self.manufacturer,
            'android_version': self.android_version,
            'api_level': self.api_level,
            'status': self.status,
            'connection_type': self.connection_type,
            'ip_address': self.ip_address,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'properties': self.properties
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Device':
        """Create device from dictionary."""
        last_seen = None
        if data.get('last_seen'):
            try:
                last_seen = datetime.fromisoformat(data['last_seen'])
            except ValueError:
                last_seen = datetime.now()
        
        return cls(
            id=data['id'],
            name=data.get('name'),
            model=data.get('model'),
            manufacturer=data.get('manufacturer'),
            android_version=data.get('android_version'),
            api_level=data.get('api_level'),
            status=data.get('status', DEVICE_STATE_UNKNOWN),
            connection_type=data.get('connection_type', CONNECTION_USB),
            ip_address=data.get('ip_address'),
            last_seen=last_seen,
            properties=data.get('properties', {})
        )
