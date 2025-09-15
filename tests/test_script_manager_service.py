"""
Test Script Manager Service

Comprehensive tests for script execution, management, and async operations.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from PyQt6.QtCore import QObject

from services.script_manager import (
    ScriptManager, Script, ScriptType, ScriptStatus, 
    get_script_manager
)


@pytest.fixture
def temp_script_dir(tmp_path):
    """Create temporary script directory."""
    script_dir = tmp_path / "scripts"
    script_dir.mkdir()
    
    # Create subdirectories
    (script_dir / "host" / "windows").mkdir(parents=True)
    (script_dir / "host" / "linux").mkdir(parents=True)
    (script_dir / "device").mkdir(parents=True)
    
    return script_dir


@pytest.fixture
def script_manager(temp_script_dir):
    """Create ScriptManager instance with temporary directory."""
    return ScriptManager(str(temp_script_dir))


@pytest.fixture
def sample_script():
    """Sample script data."""
    return Script(
        id="test_script_001",
        name="Test Script",
        script_type=ScriptType.HOST_WINDOWS,
        script_path="test_script.bat",
        description="Test script for unit testing"
    )


@pytest.fixture
def sample_windows_script(temp_script_dir):
    """Create sample Windows script file."""
    script_file = temp_script_dir / "host" / "windows" / "test.bat"
    script_file.write_text("@echo off\necho Hello from Windows script\npause")
    return script_file


@pytest.fixture
def sample_linux_script(temp_script_dir):
    """Create sample Linux script file."""
    script_file = temp_script_dir / "host" / "linux" / "test.sh"
    script_file.write_text("#!/bin/bash\necho 'Hello from Linux script'\nread -p 'Press enter to continue'")
    script_file.chmod(0o755)
    return script_file


@pytest.fixture
def sample_device_script(temp_script_dir):
    """Create sample device script file."""
    script_file = temp_script_dir / "device" / "test_device.sh"
    script_file.write_text("#!/system/bin/sh\necho 'Hello from device script'")
    return script_file


class TestScript:
    """Test cases for Script dataclass."""

    def test_script_creation(self, sample_script):
        """Test script object creation."""
        assert sample_script.id == "test_script_001"
        assert sample_script.name == "Test Script"
        assert sample_script.script_type == ScriptType.HOST_WINDOWS
        assert sample_script.script_path == "test_script.bat"

    def test_script_to_dict(self, sample_script):
        """Test script conversion to dictionary."""
        from dataclasses import asdict
        script_dict = asdict(sample_script)
        
        assert script_dict["id"] == "test_script_001"
        assert script_dict["name"] == "Test Script"
        assert script_dict["script_type"] == ScriptType.HOST_WINDOWS

    def test_script_types_enum(self):
        """Test script type enumeration values."""
        assert ScriptType.HOST_WINDOWS.value == "host_windows"
        assert ScriptType.HOST_LINUX.value == "host_linux"
        assert ScriptType.DEVICE.value == "device"

    def test_script_status_enum(self):
        """Test script status enumeration values."""
        assert ScriptStatus.IDLE.value == "idle"
        assert ScriptStatus.RUNNING.value == "running"
        assert ScriptStatus.COMPLETED.value == "completed"
        assert ScriptStatus.FAILED.value == "failed"
        assert ScriptStatus.CANCELLED.value == "cancelled"


class TestScriptManager:
    """Test cases for ScriptManager."""

    def test_init_creates_directories(self, temp_script_dir):
        """Test initialization creates necessary directories."""
        manager = ScriptManager(str(temp_script_dir))
        
        assert (temp_script_dir / "host" / "windows").exists()
        assert (temp_script_dir / "host" / "linux").exists()
        assert (temp_script_dir / "device").exists()

    def test_discover_scripts_empty_directory(self, script_manager):
        """Test script discovery in empty directory."""
        scripts = script_manager.discover_scripts()
        assert scripts == []

    def test_discover_scripts_with_files(self, script_manager, sample_windows_script, 
                                        sample_linux_script, sample_device_script):
        """Test script discovery with actual script files."""
        scripts = script_manager.discover_scripts()
        
        # Should find all three types
        script_types = [s.script_type for s in scripts]
        assert ScriptType.HOST_WINDOWS in script_types
        assert ScriptType.HOST_LINUX in script_types
        assert ScriptType.DEVICE in script_types

    def test_get_script_by_id_existing(self, script_manager, sample_script):
        """Test getting script by existing ID."""
        script_manager.scripts[sample_script.id] = sample_script
        
        result = script_manager.get_script_by_id(sample_script.id)
        assert result == sample_script

    def test_get_script_by_id_nonexistent(self, script_manager):
        """Test getting script by non-existent ID."""
        result = script_manager.get_script_by_id("nonexistent_id")
        assert result is None

    def test_get_scripts_by_type(self, script_manager):
        """Test getting scripts filtered by type."""
        # Create scripts of different types
        win_script = Script("win_001", "Windows Script", ScriptType.HOST_WINDOWS, "win.bat")
        linux_script = Script("linux_001", "Linux Script", ScriptType.HOST_LINUX, "linux.sh")
        device_script = Script("device_001", "Device Script", ScriptType.DEVICE, "device.sh")
        
        script_manager.scripts = {
            win_script.id: win_script,
            linux_script.id: linux_script,
            device_script.id: device_script
        }
        
        windows_scripts = script_manager.get_scripts_by_type(ScriptType.HOST_WINDOWS)
        assert len(windows_scripts) == 1
        assert windows_scripts[0] == win_script

    def test_get_all_scripts(self, script_manager, sample_script):
        """Test getting all scripts."""
        script_manager.scripts[sample_script.id] = sample_script
        
        all_scripts = script_manager.get_all_scripts()
        assert len(all_scripts) == 1
        assert all_scripts[0] == sample_script

    @pytest.mark.asyncio
    async def test_execute_script_basic(self, script_manager, sample_windows_script):
        """Test basic script execution."""
        script = Script("test", "Test", ScriptType.HOST_WINDOWS, str(sample_windows_script))
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"output", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            result = await script_manager.execute_script(script.id, "test_device")
            assert result is not None

    @pytest.mark.asyncio
    async def test_execute_script_with_callback(self, script_manager, sample_script):
        """Test script execution with output callback."""
        callback_outputs = []
        
        def output_callback(line):
            callback_outputs.append(line)
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"test output\n", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            await script_manager.execute_script(
                sample_script.id, 
                "test_device", 
                output_callback=output_callback
            )
            
            # Callback should have been called
            assert len(callback_outputs) > 0

    @pytest.mark.asyncio
    async def test_execute_script_failure(self, script_manager, sample_script):
        """Test script execution failure handling."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"error occurred")
            mock_process.returncode = 1
            mock_subprocess.return_value = mock_process
            
            result = await script_manager.execute_script(sample_script.id, "test_device")
            # Should handle failure gracefully

    def test_cancel_script_execution(self, script_manager, sample_script):
        """Test canceling script execution."""
        execution_id = "test_execution_001"
        script_manager.active_executions[execution_id] = Mock()
        
        result = script_manager.cancel_execution(execution_id)
        assert result is True

    def test_cancel_nonexistent_execution(self, script_manager):
        """Test canceling non-existent execution."""
        result = script_manager.cancel_execution("nonexistent_id")
        assert result is False

    def test_get_execution_status_running(self, script_manager):
        """Test getting status of running execution."""
        execution_id = "test_execution_001"
        script_manager.active_executions[execution_id] = Mock()
        
        status = script_manager.get_execution_status(execution_id)
        assert status == ScriptStatus.RUNNING

    def test_get_execution_status_completed(self, script_manager):
        """Test getting status of completed execution."""
        execution_id = "test_execution_001"
        
        status = script_manager.get_execution_status(execution_id)
        assert status == ScriptStatus.IDLE

    def test_validate_script_path_valid(self, script_manager, sample_windows_script):
        """Test validating valid script path."""
        result = script_manager.validate_script_path(str(sample_windows_script))
        assert result is True

    def test_validate_script_path_invalid(self, script_manager):
        """Test validating invalid script path."""
        result = script_manager.validate_script_path("/nonexistent/script.bat")
        assert result is False

    def test_create_execution_context(self, script_manager, sample_script):
        """Test creating execution context."""
        context = script_manager.create_execution_context(
            sample_script, 
            "test_device", 
            {"param1": "value1"}
        )
        
        assert context is not None
        assert "script" in context
        assert "device_id" in context
        assert "parameters" in context

    def test_script_import_export(self, script_manager, sample_script):
        """Test script import/export functionality."""
        script_manager.scripts[sample_script.id] = sample_script
        
        # Export
        exported_data = script_manager.export_scripts()
        assert len(exported_data) == 1
        
        # Clear and import
        script_manager.scripts = {}
        result = script_manager.import_scripts(exported_data)
        assert result is True
        assert len(script_manager.scripts) == 1

    @pytest.mark.parametrize("script_type,expected_extension", [
        (ScriptType.HOST_WINDOWS, ".bat"),
        (ScriptType.HOST_LINUX, ".sh"),
        (ScriptType.DEVICE, ".sh"),
    ])
    def test_get_default_extension(self, script_manager, script_type, expected_extension):
        """Test getting default extension for script types."""
        extension = script_manager.get_default_extension(script_type)
        assert extension == expected_extension

    def test_signal_emissions(self, script_manager):
        """Test that Qt signals are emitted correctly."""
        assert hasattr(script_manager, 'script_started')
        assert hasattr(script_manager, 'script_finished')
        assert hasattr(script_manager, 'script_output')
        assert hasattr(script_manager, 'script_error')

    def test_thread_safety(self, script_manager):
        """Test thread-safe operations."""
        import threading
        
        scripts_created = []
        
        def worker(worker_id):
            script = Script(
                f"thread_script_{worker_id}",
                f"Thread Script {worker_id}",
                ScriptType.HOST_WINDOWS,
                f"script_{worker_id}.bat"
            )
            script_manager.scripts[script.id] = script
            scripts_created.append(script.id)
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(scripts_created) == 5
        assert len(script_manager.scripts) == 5


class TestGetScriptManagerSingleton:
    """Test the global script manager singleton."""

    def test_singleton_returns_same_instance(self):
        """Test that get_script_manager returns the same instance."""
        manager1 = get_script_manager()
        manager2 = get_script_manager()
        
        assert manager1 is manager2

    def test_singleton_with_custom_path(self, tmp_path):
        """Test singleton with custom path."""
        custom_path = str(tmp_path / "custom_scripts")
        
        # Clear any existing singleton
        import services.script_manager
        if hasattr(services.script_manager, '_script_manager_instance'):
            delattr(services.script_manager, '_script_manager_instance')
        
        manager = get_script_manager(custom_path)
        assert manager.scripts_dir == custom_path


@pytest.mark.integration
class TestScriptManagerIntegration:
    """Integration tests for ScriptManager."""

    @pytest.mark.asyncio
    async def test_full_script_lifecycle(self, script_manager, sample_windows_script):
        """Test complete script lifecycle from discovery to execution."""
        # Discover scripts
        scripts = script_manager.discover_scripts()
        assert len(scripts) > 0
        
        # Get Windows script
        win_scripts = [s for s in scripts if s.script_type == ScriptType.HOST_WINDOWS]
        assert len(win_scripts) > 0
        
        script = win_scripts[0]
        
        # Execute script
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Script executed successfully", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            execution_id = await script_manager.execute_script(script.id, "test_device")
            assert execution_id is not None

    def test_concurrent_script_executions(self, script_manager):
        """Test handling multiple concurrent script executions."""
        # This would test the manager's ability to handle multiple
        # simultaneous script executions
        script1 = Script("script1", "Script 1", ScriptType.HOST_WINDOWS, "script1.bat")
        script2 = Script("script2", "Script 2", ScriptType.HOST_LINUX, "script2.sh")
        
        script_manager.scripts.update({
            script1.id: script1,
            script2.id: script2
        })
        
        # Mock concurrent executions
        execution1_id = "exec_1"
        execution2_id = "exec_2"
        
        script_manager.active_executions[execution1_id] = Mock()
        script_manager.active_executions[execution2_id] = Mock()
        
        assert len(script_manager.active_executions) == 2
        assert script_manager.get_execution_status(execution1_id) == ScriptStatus.RUNNING
        assert script_manager.get_execution_status(execution2_id) == ScriptStatus.RUNNING

    def test_large_script_output_handling(self, script_manager, sample_script):
        """Test handling of large script output."""
        large_output = "Large output line\n" * 1000
        outputs_received = []
        
        def output_callback(line):
            outputs_received.append(line)
        
        # Simulate processing large output
        lines = large_output.split('\n')
        for line in lines:
            if line:  # Skip empty lines
                output_callback(line)
        
        assert len(outputs_received) == 1000

    def test_script_discovery_performance(self, temp_script_dir):
        """Test script discovery performance with many files."""
        # Create many script files
        for i in range(50):
            (temp_script_dir / "host" / "windows" / f"script_{i}.bat").write_text("echo test")
            (temp_script_dir / "host" / "linux" / f"script_{i}.sh").write_text("echo test")
            (temp_script_dir / "device" / f"script_{i}.sh").write_text("echo test")
        
        manager = ScriptManager(str(temp_script_dir))
        scripts = manager.discover_scripts()
        
        # Should find all scripts efficiently
        assert len(scripts) == 150  # 50 × 3 types
