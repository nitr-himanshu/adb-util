#!/usr/bin/env python3
"""
Comprehensive test for logcat collection feature
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch

from src.adb.logcat_handler import LogcatHandler, LogEntry
from src.gui.logging import LogcatWorker


class TestLogcatCollection:
    """Test suite for logcat collection feature."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.device_id = "test_device_123"
        self.handler = LogcatHandler(self.device_id)
    
    def test_log_entry_creation(self):
        """Test LogEntry object creation."""
        raw_line = "01-01 12:00:00.123  1234  5678 I TestTag: Test message"
        entry = LogEntry(
            timestamp="01-01 12:00:00.123",
            pid="1234",
            tid="5678",
            level="I",
            tag="TestTag",
            message="Test message",
            raw_line=raw_line
        )
        
        assert entry.timestamp == "01-01 12:00:00.123"
        assert entry.level == "I"
        assert entry.pid == "1234"
        assert entry.tid == "5678"
        assert entry.tag == "TestTag"
        assert entry.message == "Test message"
        assert entry.raw_line == raw_line
    
    def test_log_parsing_various_formats(self):
        """Test parsing different logcat formats."""
        test_cases = [
            # Standard format
            ("01-01 12:00:00.123  1234  5678 I TestTag: Test message", True),
            # Brief format
            ("I/TestTag( 1234): Test message", True),
            # Time format
            ("01-01 12:00:00.123 I/TestTag( 1234): Test message", True),
            # Invalid format
            ("Invalid log line", False),
            # Empty line
            ("", False),
        ]
        
        for log_line, should_parse in test_cases:
            entry = self.handler.parse_log_line(log_line)
            if should_parse:
                assert entry is not None, f"Failed to parse: {log_line}"
                assert entry.level in ['V', 'D', 'I', 'W', 'E', 'F']
                assert entry.tag
                assert entry.message
            else:
                assert entry is None, f"Should not parse: {log_line}"
    
    def test_log_filtering(self):
        """Test log filtering functionality."""
        # Create test entries
        entries = [
            LogEntry("01-01 12:00:00.123", "1234", "5678", "I", "App", "Info message", "raw1"),
            LogEntry("01-01 12:00:01.456", "2345", "6789", "E", "App", "Error message", "raw2"),
            LogEntry("01-01 12:00:02.789", "3456", "7890", "D", "System", "Debug message", "raw3"),
            LogEntry("01-01 12:00:03.012", "4567", "8901", "W", "Network", "Warning message", "raw4"),
        ]
        
        # Test level filtering
        filtered = self.handler.filter_entries(entries, level_filter=['I', 'E'])
        assert len(filtered) == 2
        assert all(entry.level in ['I', 'E'] for entry in filtered)
        
        # Test tag filtering
        filtered = self.handler.filter_entries(entries, tag_filter='App')
        assert len(filtered) == 2
        assert all(entry.tag == 'App' for entry in filtered)
        
        # Test message filtering
        filtered = self.handler.filter_entries(entries, message_filter='Error')
        assert len(filtered) == 1
        assert 'Error' in filtered[0].message
        
        # Test regex filtering
        filtered = self.handler.filter_entries(entries, message_filter=r'.*age$', use_regex=True)
        assert len(filtered) == 4  # All end with 'age'
    
    def test_export_functionality(self):
        """Test log export functionality."""
        # Create test entries
        entries = [
            LogEntry("01-01 12:00:00.123", "1234", "5678", "I", "App", "Info message", "raw1"),
            LogEntry("01-01 12:00:01.456", "2345", "6789", "E", "App", "Error message", "raw2"),
        ]
        
        # Test export to file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_filename = temp_file.name
        
        try:
            success = self.handler.export_logs(temp_filename, entries)
            assert success
            
            # Verify file contents
            with open(temp_filename, 'r') as f:
                content = f.read()
                assert "raw1" in content
                assert "raw2" in content
                assert "test_device_123" in content
        finally:
            os.unlink(temp_filename)
    
    def test_buffer_management(self):
        """Test log buffer management."""
        # Add entries beyond default buffer
        for i in range(5):
            entry = LogEntry(f"01-01 12:00:0{i}.123", "1234", "5678", "I", "Test", f"Message {i}", f"raw{i}")
            self.handler.log_entries.append(entry)
        
        # Verify entries were added
        assert len(self.handler.log_entries) == 5
        assert self.handler.log_entries[-1].message == "Message 4"
        assert self.handler.log_entries[0].message == "Message 0"
    
    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_shell')
    async def test_clear_logcat(self, mock_subprocess):
        """Test logcat clearing functionality."""
        # Mock successful process
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b'', b''))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        
        result = await self.handler.clear_logcat()
        assert result is True
        
        # Verify command was called
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert f"adb -s {self.device_id} logcat -c" in call_args
    
    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_shell')
    async def test_start_logcat_stream(self, mock_subprocess):
        """Test logcat streaming functionality."""
        # Mock process that yields log lines
        mock_process = Mock()
        mock_process.stdout.readline = AsyncMock(side_effect=[
            b"01-01 12:00:00.123  1234  5678 I TestTag: Test message 1\n",
            b"01-01 12:00:01.456  2345  6789 E ErrorTag: Test message 2\n",
            b"",  # End of stream
        ])
        mock_subprocess.return_value = mock_process
        
        # Set up callbacks
        received_entries = []
        
        def on_entry(entry):
            received_entries.append(entry)
        
        # Start streaming
        self.handler.on_log_entry = on_entry
        
        # Run for a short time
        async for entry in self.handler.start_logcat_stream():
            if len(received_entries) >= 2:
                break
        
        # Verify entries were received
        assert len(received_entries) >= 2
        assert received_entries[0].tag == "TestTag"
        assert received_entries[1].tag == "ErrorTag"


class TestLogcatWorker:
    """Test suite for LogcatWorker GUI integration."""
    
    def test_worker_initialization(self):
        """Test LogcatWorker initialization."""
        device_id = "test_device"
        worker = LogcatWorker(device_id)
        
        assert worker.device_id == device_id
        assert worker.logcat_handler is not None
        assert worker.should_stop is False
    
    @patch('asyncio.run')
    def test_worker_run(self, mock_asyncio_run):
        """Test LogcatWorker run method."""
        device_id = "test_device"
        worker = LogcatWorker(device_id)
        worker.run()
        
        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
