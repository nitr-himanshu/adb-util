"""
Test Configuration

Configuration and fixtures for pytest tests.
"""

import pytest
import asyncio
from pathlib import Path


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary configuration directory for tests."""
    config_dir = tmp_path / ".adb-util"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def mock_device_id():
    """Mock device ID for testing."""
    return "test_device_123"


@pytest.fixture
def sample_device_data():
    """Sample device data for testing."""
    return {
        "id": "test_device_123",
        "name": "Test Device",
        "model": "Test Model",
        "manufacturer": "Test Manufacturer",
        "android_version": "11",
        "api_level": 30,
        "status": "device"
    }


@pytest.fixture
def sample_command_data():
    """Sample command data for testing."""
    return {
        "name": "List Files",
        "command": "ls -la",
        "category": "File Operations",
        "description": "List all files with details"
    }
