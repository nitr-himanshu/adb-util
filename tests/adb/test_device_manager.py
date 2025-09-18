"""
Unit Tests for Device Manager

Tests the DeviceManager class including device discovery, connection management,
and status monitoring with mocked ADB commands.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, call
from datetime import datetime

from adb.device_manager import DeviceManager
from models.device import Device
from utils.constants import (
    ADB_DEVICES_COMMAND,
    DEVICE_DISCOVERY_TIMEOUT,
    DEVICE_STATE_DEVICE,
    CONNECTION_USB,
    CONNECTION_TCPIP
)


class TestDeviceManager:
    """Test cases for DeviceManager class."""
    
    def test_device_manager_initialization(self):
        """Test DeviceManager initialization."""
        manager = DeviceManager()
        
        assert isinstance(manager.devices, list)
        assert len(manager.devices) == 0
        assert isinstance(manager.connected_devices, dict)
        assert len(manager.connected_devices) == 0
        assert manager._monitoring is False
        assert manager._monitor_task is None
    
    @pytest.mark.asyncio
    async def test_discover_devices_success(self, mock_subprocess, sample_adb_devices_output):
        """Test successful device discovery."""
        # Configure mock subprocess
        mock_subprocess['run'].return_value.stdout = sample_adb_devices_output
        mock_subprocess['run'].return_value.returncode = 0
        
        manager = DeviceManager()
        
        with patch.object(manager, '_execute_adb_command') as mock_exec:
            mock_exec.return_value = (sample_adb_devices_output, "", 0)
            
            devices = await manager.discover_devices()
            
            assert len(devices) >= 2  # Should find at least emulator and IP device
            
            # Check if devices are properly parsed
            device_ids = [d.id for d in devices]
            assert "emulator-5554" in device_ids
            assert "192.168.1.100:5555" in device_ids
            
            # Verify command was called correctly
            mock_exec.assert_called_once_with(
                ADB_DEVICES_COMMAND, 
                timeout=DEVICE_DISCOVERY_TIMEOUT
            )
    
    @pytest.mark.asyncio
    async def test_discover_devices_command_failure(self, mock_subprocess):
        """Test device discovery when ADB command fails."""
        manager = DeviceManager()
        
        with patch.object(manager, '_execute_adb_command') as mock_exec:
            mock_exec.return_value = None  # Simulate command failure
            
            devices = await manager.discover_devices()
            
            assert len(devices) == 0
            assert len(manager.devices) == 0
    
    @pytest.mark.asyncio
    async def test_discover_devices_no_devices(self, mock_subprocess):
        """Test device discovery when no devices are connected."""
        empty_output = "List of devices attached\n\n"
        
        manager = DeviceManager()
        
        with patch.object(manager, '_execute_adb_command') as mock_exec:
            mock_exec.return_value = (empty_output, "", 0)
            
            devices = await manager.discover_devices()
            
            assert len(devices) == 0
    
    @pytest.mark.asyncio
    async def test_discover_devices_parsing_edge_cases(self, mock_subprocess):
        """Test device discovery with various edge case outputs."""
        edge_case_outputs = [
            # Malformed output
            "Some random text\nNot the expected format",
            # Empty lines
            "List of devices attached\n\n\n\n",
            # Device with extra info
            "List of devices attached\nemulator-5554\tdevice product:sdk_gphone64_x86_64",
            # Unusual device IDs
            "List of devices attached\ndevice:with:colons\tdevice\n"
        ]
        
        manager = DeviceManager()
        
        for output in edge_case_outputs:
            with patch.object(manager, '_execute_adb_command') as mock_exec:
                mock_exec.return_value = (output, "", 0)
                
                devices = await manager.discover_devices()
                # Should not crash, might return empty list or parsed devices
                assert isinstance(devices, list)
    
    @pytest.mark.asyncio
    async def test_get_device_properties_success(self, mock_subprocess, sample_device_properties):
        """Test getting device properties successfully."""
        manager = DeviceManager()
        device_id = "emulator-5554"
        
        # Mock the properties output
        props_output = "\n".join([f"[{key}]: [{value}]" for key, value in sample_device_properties.items()])
        
        with patch.object(manager, '_execute_adb_command') as mock_exec:
            mock_exec.return_value = (props_output, "", 0)
            
            properties = await manager.get_device_properties(device_id)
            
            assert isinstance(properties, dict)
            assert properties["ro.product.manufacturer"] == "Samsung"
            assert properties["ro.product.model"] == "Galaxy S21"
            assert properties["ro.build.version.release"] == "13"
    
    @pytest.mark.asyncio
    async def test_get_device_properties_failure(self, mock_subprocess):
        """Test getting device properties when command fails."""
        manager = DeviceManager()
        device_id = "nonexistent-device"
        
        with patch.object(manager, '_execute_adb_command') as mock_exec:
            mock_exec.return_value = ("", "error: device not found", 1)
            
            properties = await manager.get_device_properties(device_id)
            
            assert properties == {}
    
    @pytest.mark.asyncio
    async def test_execute_adb_command_success(self, mock_subprocess):
        """Test successful ADB command execution."""
        manager = DeviceManager()
        
        # Configure mock
        expected_stdout = "command output"
        expected_stderr = ""
        expected_returncode = 0
        
        mock_subprocess['run'].return_value.stdout = expected_stdout
        mock_subprocess['run'].return_value.stderr = expected_stderr
        mock_subprocess['run'].return_value.returncode = expected_returncode
        
        result = await manager._execute_adb_command(["adb", "devices"])
        
        assert result is not None
        stdout, stderr, returncode = result
        assert stdout == expected_stdout
        assert stderr == expected_stderr
        assert returncode == expected_returncode
    
    @pytest.mark.asyncio
    async def test_execute_adb_command_timeout(self, mock_subprocess):
        """Test ADB command execution timeout."""
        manager = DeviceManager()
        
        # Configure mock to raise TimeoutExpired
        from subprocess import TimeoutExpired
        mock_subprocess['run'].side_effect = TimeoutExpired("adb", 5)
        
        result = await manager._execute_adb_command(["adb", "devices"], timeout=1)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_execute_adb_command_exception(self, mock_subprocess):
        """Test ADB command execution with general exception."""
        manager = DeviceManager()
        
        # Configure mock to raise exception
        mock_subprocess['run'].side_effect = FileNotFoundError("adb not found")
        
        result = await manager._execute_adb_command(["adb", "devices"])
        
        assert result is None
    
    def test_parse_devices_output_typical(self):
        """Test parsing typical adb devices output."""
        manager = DeviceManager()
        output = """List of devices attached
emulator-5554\tdevice
192.168.1.100:5555\tdevice
ABC123\toffline
DEF456\tunauthorized

"""
        
        devices = manager._parse_devices_output(output)
        
        assert len(devices) == 4
        
        # Check emulator device
        emulator = next(d for d in devices if d.id == "emulator-5554")
        assert emulator.status == "device"
        assert emulator.is_online
        
        # Check IP device  
        ip_device = next(d for d in devices if d.id == "192.168.1.100:5555")
        assert ip_device.status == "device"
        assert ip_device.connection_type == CONNECTION_TCPIP
        
        # Check offline device
        offline_device = next(d for d in devices if d.id == "ABC123")
        assert offline_device.status == "offline"
        assert not offline_device.is_online
    
    def test_parse_devices_output_empty(self):
        """Test parsing empty devices output."""
        manager = DeviceManager()
        output = "List of devices attached\n\n"
        
        devices = manager._parse_devices_output(output)
        
        assert len(devices) == 0
    
    def test_parse_devices_output_malformed(self):
        """Test parsing malformed devices output."""
        manager = DeviceManager()
        malformed_outputs = [
            "",
            "Random text",
            "List of devices attached\nmalformed line",
            "List of devices attached\ndevice_id_only",
        ]
        
        for output in malformed_outputs:
            devices = manager._parse_devices_output(output)
            assert isinstance(devices, list)  # Should not crash
    
    def test_is_tcpip_device(self):
        """Test TCP/IP device detection."""
        manager = DeviceManager()
        
        # TCP/IP devices (IP:port format)
        assert manager._is_tcpip_device("192.168.1.100:5555") is True
        assert manager._is_tcpip_device("10.0.0.1:5555") is True
        assert manager._is_tcpip_device("localhost:5555") is True
        
        # USB devices
        assert manager._is_tcpip_device("emulator-5554") is False
        assert manager._is_tcpip_device("ABC123DEF456") is False
        assert manager._is_tcpip_device("device_serial") is False
    
    def test_extract_ip_from_device_id(self):
        """Test IP address extraction from device ID."""
        manager = DeviceManager()
        
        # Valid IP:port combinations
        assert manager._extract_ip_from_device_id("192.168.1.100:5555") == "192.168.1.100"
        assert manager._extract_ip_from_device_id("10.0.0.1:5555") == "10.0.0.1"
        
        # Invalid formats should return None
        assert manager._extract_ip_from_device_id("emulator-5554") is None
        assert manager._extract_ip_from_device_id("invalid") is None
        assert manager._extract_ip_from_device_id("") is None
    
    @pytest.mark.asyncio
    async def test_refresh_devices(self, mock_subprocess, sample_adb_devices_output):
        """Test device list refresh functionality."""
        manager = DeviceManager()
        
        with patch.object(manager, 'discover_devices') as mock_discover:
            mock_devices = [
                Device(id="device1", status="device"),
                Device(id="device2", status="offline")
            ]
            mock_discover.return_value = mock_devices
            
            await manager.refresh_devices()
            
            assert manager.devices == mock_devices
            assert len(manager.connected_devices) == 1  # Only online device
            assert "device1" in manager.connected_devices
    
    def test_get_online_devices(self):
        """Test getting only online devices."""
        manager = DeviceManager()
        
        # Set up test devices
        manager.devices = [
            Device(id="online1", status=DEVICE_STATE_DEVICE),
            Device(id="offline1", status="offline"),
            Device(id="online2", status=DEVICE_STATE_DEVICE),
            Device(id="unauthorized1", status="unauthorized")
        ]
        
        online_devices = manager.get_online_devices()
        
        assert len(online_devices) == 2
        online_ids = [d.id for d in online_devices]
        assert "online1" in online_ids
        assert "online2" in online_ids
        assert "offline1" not in online_ids
        assert "unauthorized1" not in online_ids
    
    def test_get_device_by_id(self):
        """Test getting device by ID."""
        manager = DeviceManager()
        
        test_device = Device(id="test-device", status="device")
        manager.devices = [test_device]
        
        # Found device
        found_device = manager.get_device_by_id("test-device")
        assert found_device == test_device
        
        # Not found device
        not_found = manager.get_device_by_id("nonexistent")
        assert not_found is None
    
    @pytest.mark.asyncio
    async def test_device_monitoring_lifecycle(self):
        """Test device monitoring start/stop lifecycle."""
        manager = DeviceManager()
        
        # Mock the monitoring coroutine
        with patch.object(manager, '_monitor_devices') as mock_monitor:
            mock_monitor.return_value = AsyncMock()
            
            # Start monitoring
            await manager.start_monitoring()
            assert manager._monitoring is True
            assert manager._monitor_task is not None
            
            # Stop monitoring
            await manager.stop_monitoring()
            assert manager._monitoring is False


class TestDeviceManagerIntegration:
    """Integration-style tests for DeviceManager with realistic scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_device_discovery_workflow(self, mock_subprocess):
        """Test complete device discovery workflow."""
        manager = DeviceManager()
        
        # Setup complex ADB output
        adb_output = """List of devices attached
emulator-5554\tdevice
192.168.1.100:5555\tdevice
physical_device\tdevice
offline_device\toffline
unauthorized_device\tunauthorized

"""
        
        props_outputs = {
            "emulator-5554": "[ro.product.manufacturer]: [Google]\n[ro.product.model]: [Android SDK Emulator]",
            "192.168.1.100:5555": "[ro.product.manufacturer]: [Samsung]\n[ro.product.model]: [Galaxy S21]",
            "physical_device": "[ro.product.manufacturer]: [OnePlus]\n[ro.product.model]: [OnePlus 9]"
        }
        
        with patch.object(manager, '_execute_adb_command') as mock_exec:
            def mock_command(*args, **kwargs):
                command = args[0]
                if command == ADB_DEVICES_COMMAND:
                    return (adb_output, "", 0)
                elif "getprop" in " ".join(command):
                    device_id = command[2]  # Extract device ID from command
                    return (props_outputs.get(device_id, ""), "", 0)
                return ("", "", 0)
            
            mock_exec.side_effect = mock_command
            
            # Discover devices
            devices = await manager.discover_devices()
            
            # Verify results
            assert len(devices) == 5
            online_devices = [d for d in devices if d.is_online]
            assert len(online_devices) == 3
            
            # Check device properties were populated for online devices
            emulator = next(d for d in devices if d.id == "emulator-5554")
            assert emulator.manufacturer == "Google"
            assert emulator.model == "Android SDK Emulator"
    
    @pytest.mark.asyncio
    async def test_error_handling_resilience(self, mock_subprocess):
        """Test that manager handles various error conditions gracefully."""
        manager = DeviceManager()
        
        error_scenarios = [
            # ADB not found
            FileNotFoundError("adb command not found"),
            # Permission denied
            PermissionError("Permission denied"),
            # Command timeout
            asyncio.TimeoutError("Command timed out"),
            # Generic exception
            RuntimeError("Unknown error")
        ]
        
        for exception in error_scenarios:
            with patch.object(manager, '_execute_adb_command') as mock_exec:
                mock_exec.side_effect = exception
                
                # Should not crash, should return empty list
                devices = await manager.discover_devices()
                assert isinstance(devices, list)
                assert len(devices) == 0