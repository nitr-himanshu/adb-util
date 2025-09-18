"""
Test Configuration and Shared Fixtures

Provides common fixtures, test utilities, and configuration for the ADB-UTIL test suite.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import Generator, Dict, Any, List
import pytest
import json
from datetime import datetime

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# PyQt6 imports
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    import pytest_qt
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    pytest_qt = None


# ============================================================================
# Application Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for GUI tests."""
    if not PYQT6_AVAILABLE:
        pytest.skip("PyQt6 not available")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_config_dir(temp_dir) -> Path:
    """Provide a temporary configuration directory."""
    config_dir = temp_dir / "adb-util-config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture
def sample_config_data() -> Dict[str, Any]:
    """Provide sample configuration data."""
    return {
        "theme": "dark",
        "auto_refresh": True,
        "refresh_interval": 5000,
        "window_geometry": {
            "width": 1200,
            "height": 800,
            "x": 100,
            "y": 100
        },
        "log_level": "INFO",
        "adb_path": "adb",
        "max_log_lines": 1000
    }


@pytest.fixture
def config_file(mock_config_dir, sample_config_data) -> Path:
    """Create a sample configuration file."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, 'w') as f:
        json.dump(sample_config_data, f, indent=2)
    return config_path


# ============================================================================
# ADB Mocking Fixtures
# ============================================================================

@pytest.fixture
def mock_subprocess():
    """Mock subprocess calls for ADB commands."""
    with patch('subprocess.run') as mock_run, \
         patch('subprocess.Popen') as mock_popen:
        
        # Configure default successful response
        mock_run.return_value = Mock(
            stdout="",
            stderr="",
            returncode=0
        )
        
        # Configure Popen for streaming operations
        mock_process = Mock()
        mock_process.stdout.readline.return_value = b""
        mock_process.poll.return_value = None
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        yield {
            'run': mock_run,
            'popen': mock_popen,
            'process': mock_process
        }


@pytest.fixture
def sample_adb_devices_output() -> str:
    """Sample ADB devices command output."""
    return """List of devices attached
emulator-5554\tdevice
192.168.1.100:5555\tdevice
ABC123\toffline
DEF456\tunauthorized

"""


@pytest.fixture
def sample_device_properties() -> Dict[str, str]:
    """Sample device properties."""
    return {
        "ro.product.manufacturer": "Samsung",
        "ro.product.model": "Galaxy S21",
        "ro.build.version.release": "13",
        "ro.build.version.sdk": "33",
        "ro.product.name": "beyond1qlteue"
    }


# ============================================================================
# Model Fixtures
# ============================================================================

@pytest.fixture
def sample_device_data():
    """Sample device data for testing."""
    return {
        "id": "emulator-5554",
        "name": "Test Emulator",
        "model": "Android SDK Emulator",
        "manufacturer": "Google",
        "android_version": "13",
        "api_level": 33,
        "status": "device",
        "connection_type": "usb",
        "ip_address": None,
        "properties": {
            "ro.product.manufacturer": "Google",
            "ro.product.model": "Android SDK Emulator"
        }
    }


@pytest.fixture
def sample_script_data():
    """Sample script data for testing."""
    return {
        "id": "test-script-123",
        "name": "Test Script",
        "script_type": "host_windows",
        "script_path": "test_script.bat",
        "description": "A test script for unit testing",
        "created_at": "2024-01-01T12:00:00",
        "last_run": "",
        "run_count": 0,
        "is_template": False,
        "is_visible": True
    }


# ============================================================================
# Service Mocking Fixtures  
# ============================================================================

@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    return Mock()


@pytest.fixture
def mock_script_manager():
    """Mock script manager service."""
    manager = Mock()
    manager.scripts = {}
    manager.executions = {}
    manager.active_workers = {}
    return manager


@pytest.fixture
def mock_config_manager(sample_config_data):
    """Mock configuration manager."""
    manager = Mock()
    manager.config = sample_config_data.copy()
    manager.get.side_effect = lambda key, default=None: manager.config.get(key, default)
    manager.set.side_effect = lambda key, value: manager.config.__setitem__(key, value)
    return manager


# ============================================================================
# File Operation Fixtures
# ============================================================================

@pytest.fixture
def sample_file_list_output():
    """Sample ls command output for file operations."""
    return """total 64
drwxr-xr-x  2 root root  4096 Jan  1 12:00 .
drwxr-xr-x  3 root root  4096 Jan  1 11:00 ..
-rw-r--r--  1 root root   123 Jan  1 12:00 file1.txt
-rw-r--r--  1 root root   456 Jan  1 12:00 file2.log
drwxr-xr-x  2 root root  4096 Jan  1 12:00 subdir
-rwxr-xr-x  1 root root   789 Jan  1 12:00 script.sh
"""


@pytest.fixture
def mock_file_operations(mock_subprocess):
    """Mock file operations with subprocess."""
    with patch('adb.file_operations.FileOperations') as mock_class:
        instance = Mock()
        mock_class.return_value = instance
        
        # Configure common methods
        instance.list_files.return_value = []
        instance.push_file.return_value = True
        instance.pull_file.return_value = True
        instance.delete_file.return_value = True
        
        yield instance


# ============================================================================
# GUI Testing Utilities
# ============================================================================

@pytest.fixture
def qtbot_with_app(qtbot, qapp):
    """Provide qtbot with QApplication."""
    if not PYQT6_AVAILABLE:
        pytest.skip("PyQt6 not available")
    return qtbot


# ============================================================================
# Test Data Generators
# ============================================================================

def generate_device_list(count: int = 3) -> List[Dict[str, Any]]:
    """Generate a list of test devices."""
    devices = []
    for i in range(count):
        devices.append({
            "id": f"device-{i:03d}",
            "name": f"Test Device {i}",
            "model": f"Model {i}",
            "manufacturer": "TestCorp",
            "android_version": "13",
            "api_level": 33,
            "status": "device" if i % 2 == 0 else "offline",
            "connection_type": "usb"
        })
    return devices


def generate_script_list(count: int = 5) -> List[Dict[str, Any]]:
    """Generate a list of test scripts."""
    scripts = []
    script_types = ["host_windows", "host_linux", "device"]
    
    for i in range(count):
        scripts.append({
            "id": f"script-{i:03d}",
            "name": f"Test Script {i}",
            "script_type": script_types[i % len(script_types)],
            "script_path": f"test_script_{i}.bat",
            "description": f"Test script number {i}",
            "created_at": datetime.now().isoformat(),
            "is_template": i % 3 == 0,
            "is_visible": True
        })
    return scripts


# ============================================================================
# Async Testing Utilities
# ============================================================================

@pytest.fixture
def mock_async_result():
    """Mock async operation result."""
    async def async_operation(*args, **kwargs):
        return True
    return async_operation


# ============================================================================
# Integration Testing Support
# ============================================================================

@pytest.fixture
def integration_test_env(temp_dir, mock_subprocess, mock_config_dir):
    """Set up environment for integration tests."""
    return {
        'temp_dir': temp_dir,
        'config_dir': mock_config_dir,
        'subprocess_mock': mock_subprocess
    }


# ============================================================================
# Performance Testing Support
# ============================================================================

@pytest.fixture
def performance_timer():
    """Simple performance timer for tests."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.end_time - self.start_time
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0
    
    return Timer()


# ============================================================================
# Markers Configuration
# ============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests") 
    config.addinivalue_line("markers", "gui: GUI tests requiring PyQt6")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "adb: Tests requiring ADB mocking")
    config.addinivalue_line("markers", "file_ops: File operation tests")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on location."""
    for item in items:
        # Add markers based on test file location
        if "test_gui" in item.nodeid:
            item.add_marker(pytest.mark.gui)
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "adb" in item.nodeid:
            item.add_marker(pytest.mark.adb)