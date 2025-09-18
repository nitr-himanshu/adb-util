"""
Unit Tests for Device Model

Tests the Device data model including initialization, properties, validation, and serialization.
"""

import pytest
from datetime import datetime
from unittest.mock import patch

from models.device import Device
from utils.constants import (
    DEVICE_STATE_DEVICE,
    DEVICE_STATE_UNKNOWN,
    CONNECTION_USB,
    CONNECTION_TCPIP
)


class TestDevice:
    """Test cases for Device model."""
    
    def test_device_initialization_minimal(self):
        """Test device initialization with minimal required data."""
        device = Device(id="test-device-123")
        
        assert device.id == "test-device-123"
        assert device.name is None
        assert device.model is None
        assert device.manufacturer is None
        assert device.android_version is None
        assert device.api_level is None
        assert device.status == DEVICE_STATE_UNKNOWN
        assert device.connection_type == CONNECTION_USB
        assert device.ip_address is None
        assert isinstance(device.last_seen, datetime)
        assert isinstance(device.properties, dict)
        assert len(device.properties) == 0
    
    def test_device_initialization_full_data(self, sample_device_data):
        """Test device initialization with complete data."""
        device = Device(**sample_device_data)
        
        assert device.id == "emulator-5554"
        assert device.name == "Test Emulator"
        assert device.model == "Android SDK Emulator"
        assert device.manufacturer == "Google"
        assert device.android_version == "13"
        assert device.api_level == 33
        assert device.status == "device"
        assert device.connection_type == "usb"
        assert device.ip_address is None
        assert device.properties["ro.product.manufacturer"] == "Google"
    
    def test_device_post_init(self):
        """Test __post_init__ method behavior."""
        # Test with None properties
        device = Device(id="test", properties=None)
        assert isinstance(device.properties, dict)
        assert len(device.properties) == 0
        
        # Test with existing properties
        props = {"key": "value"}
        device2 = Device(id="test2", properties=props)
        assert device2.properties == props
        
        # Test last_seen auto-assignment
        before = datetime.now()
        device3 = Device(id="test3")
        after = datetime.now()
        assert before <= device3.last_seen <= after
    
    def test_is_online_property(self):
        """Test is_online property logic."""
        # Online device
        online_device = Device(id="online", status=DEVICE_STATE_DEVICE)
        assert online_device.is_online is True
        
        # Offline device
        offline_device = Device(id="offline", status="offline")
        assert offline_device.is_online is False
        
        # Unauthorized device
        unauth_device = Device(id="unauth", status="unauthorized")
        assert unauth_device.is_online is False
        
        # Unknown state device
        unknown_device = Device(id="unknown", status=DEVICE_STATE_UNKNOWN)
        assert unknown_device.is_online is False
    
    def test_display_name_property(self):
        """Test display_name property with different scenarios."""
        # Device with name
        device_with_name = Device(
            id="ABC123", 
            name="My Phone",
            model="Galaxy S21"
        )
        assert device_with_name.display_name == "My Phone (ABC123)"
        
        # Device with model but no name
        device_with_model = Device(
            id="DEF456",
            model="Pixel 7"
        )
        assert device_with_model.display_name == "Pixel 7 (DEF456)"
        
        # Device with neither name nor model
        basic_device = Device(id="GHI789")
        assert basic_device.display_name == "GHI789"
    
    def test_device_equality(self):
        """Test device equality comparison."""
        device1 = Device(id="same-id", name="Device 1")
        device2 = Device(id="same-id", name="Device 2")
        device3 = Device(id="different-id", name="Device 1")
        
        # Devices should be equal if they have the same ID
        assert device1 == device2
        assert device1 != device3
    
    def test_device_string_representation(self):
        """Test string representation of device."""
        device = Device(
            id="test-123",
            name="Test Device",
            model="Test Model"
        )
        
        str_repr = str(device)
        assert "test-123" in str_repr
        assert "Test Device" in str_repr or "Test Model" in str_repr
    
    def test_device_properties_modification(self):
        """Test device properties can be modified after creation."""
        device = Device(id="test")
        
        # Add properties
        device.properties["new_key"] = "new_value"
        assert device.properties["new_key"] == "new_value"
        
        # Modify existing properties
        device.properties.update({"key1": "value1", "key2": "value2"})
        assert len(device.properties) == 3
        assert device.properties["key1"] == "value1"
    
    def test_device_connection_types(self):
        """Test different connection types."""
        # USB connection (default)
        usb_device = Device(id="usb")
        assert usb_device.connection_type == CONNECTION_USB
        
        # TCP/IP connection
        tcpip_device = Device(id="192.168.1.100:5555", connection_type=CONNECTION_TCPIP)
        assert tcpip_device.connection_type == CONNECTION_TCPIP
    
    def test_device_with_ip_address(self):
        """Test device with IP address."""
        ip_device = Device(
            id="192.168.1.100:5555",
            connection_type=CONNECTION_TCPIP,
            ip_address="192.168.1.100"
        )
        
        assert ip_device.ip_address == "192.168.1.100"
        assert ip_device.connection_type == CONNECTION_TCPIP
    
    @pytest.mark.parametrize("api_level,expected", [
        (30, 30),
        (33, 33), 
        (None, None),
        ("33", "33")  # String API levels should be preserved
    ])
    def test_device_api_levels(self, api_level, expected):
        """Test various API level values."""
        device = Device(id="test", api_level=api_level)
        assert device.api_level == expected
    
    def test_device_last_seen_custom(self):
        """Test device with custom last_seen timestamp."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        device = Device(id="test", last_seen=custom_time)
        assert device.last_seen == custom_time
    
    def test_device_status_values(self):
        """Test various device status values."""
        statuses = ["device", "offline", "unauthorized", "no permissions", "unknown"]
        
        for status in statuses:
            device = Device(id=f"test-{status}", status=status)
            assert device.status == status
            
            # Only "device" status should be online
            expected_online = (status == DEVICE_STATE_DEVICE)
            assert device.is_online == expected_online
    
    def test_device_immutable_id(self):
        """Test that device ID should not change after creation."""
        device = Device(id="original-id")
        original_id = device.id
        
        # Attempt to change ID (this is just a test of current behavior)
        device.id = "new-id"
        assert device.id == "new-id"  # Dataclass allows this, but it shouldn't in practice
        
        # In a real implementation, you might want to make id immutable
        # This test documents current behavior
    
    def test_device_with_special_characters(self):
        """Test device with special characters in fields."""
        device = Device(
            id="device:with:colons",
            name="Device (Special)",
            manufacturer="Manufacturer & Co.",
            model="Model-X_123"
        )
        
        assert device.id == "device:with:colons"
        assert device.name == "Device (Special)"
        assert device.manufacturer == "Manufacturer & Co."
        assert device.model == "Model-X_123"
    
    def test_device_properties_dict_behavior(self):
        """Test that properties behave as a proper dictionary."""
        device = Device(id="test")
        
        # Test dict methods
        device.properties["key1"] = "value1"
        assert "key1" in device.properties
        assert device.properties.get("key1") == "value1"
        assert device.properties.get("nonexistent", "default") == "default"
        
        # Test iteration
        device.properties["key2"] = "value2"
        keys = list(device.properties.keys())
        assert "key1" in keys
        assert "key2" in keys
        
        # Test clear
        device.properties.clear()
        assert len(device.properties) == 0


class TestDeviceEdgeCases:
    """Test edge cases and error conditions for Device model."""
    
    def test_device_empty_string_id(self):
        """Test device with empty string ID."""
        device = Device(id="")
        assert device.id == ""
        assert not device.is_online  # Empty ID should not be considered online
    
    def test_device_none_values(self):
        """Test device handles None values properly."""
        device = Device(
            id="test",
            name=None,
            model=None,
            manufacturer=None,
            android_version=None,
            api_level=None,
            ip_address=None,
            last_seen=None,
            properties=None
        )
        
        # All None values should be handled gracefully
        assert device.name is None
        assert device.model is None
        assert device.manufacturer is None
        assert device.android_version is None
        assert device.api_level is None
        assert device.ip_address is None
        assert isinstance(device.last_seen, datetime)  # Should be auto-assigned
        assert isinstance(device.properties, dict)     # Should be auto-assigned
    
    def test_device_very_long_strings(self):
        """Test device with very long string values."""
        long_string = "x" * 1000
        device = Device(
            id="test",
            name=long_string,
            model=long_string,
            manufacturer=long_string,
            android_version=long_string
        )
        
        assert len(device.name) == 1000
        assert len(device.model) == 1000
        assert len(device.manufacturer) == 1000
        assert len(device.android_version) == 1000
    
    def test_device_unicode_strings(self):
        """Test device with unicode characters."""
        device = Device(
            id="测试设备",
            name="Тест",
            model="デバイス",
            manufacturer="🏢 Company"
        )
        
        assert device.id == "测试设备"
        assert device.name == "Тест"
        assert device.model == "デバイス"
        assert device.manufacturer == "🏢 Company"
    
    @pytest.mark.parametrize("invalid_api_level", [
        -1, -10, 999, "invalid", [], {}, object()
    ])
    def test_device_invalid_api_levels(self, invalid_api_level):
        """Test device with potentially invalid API levels."""
        # The current implementation accepts any type for api_level
        # This test documents the current behavior
        device = Device(id="test", api_level=invalid_api_level)
        assert device.api_level == invalid_api_level
        
        # In a production system, you might want validation here