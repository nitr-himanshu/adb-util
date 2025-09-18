"""
Unit Tests for Script Manager Service

Tests the ScriptManager service including CRUD operations, execution management,
import/export functionality, and script lifecycle management.
"""

import pytest
import json
import uuid
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime

from services.script_manager import (
    ScriptManager, 
    Script, 
    ScriptType, 
    ScriptStatus,
    ScriptExecution,
    ScriptExecutionWorker
)


class TestScriptManagerInitialization:
    """Test ScriptManager initialization and setup."""
    
    def test_script_manager_init_default_config(self, mock_logger):
        """Test ScriptManager initialization with default configuration."""
        with patch('services.script_manager.get_logger', return_value=mock_logger):
            manager = ScriptManager()
            
            assert isinstance(manager.config_dir, Path)
            assert manager.config_dir == Path.home() / ".adb-util"
            assert manager.scripts_file == manager.config_dir / "scripts.json"
            assert manager.executions_file == manager.config_dir / "script_executions.json"
            assert isinstance(manager.scripts, dict)
            assert isinstance(manager.executions, dict)
            assert isinstance(manager.active_workers, dict)
            assert len(manager.scripts) == 0
    
    def test_script_manager_init_custom_config_dir(self, mock_config_dir, mock_logger):
        """Test ScriptManager initialization with custom config directory."""
        with patch('services.script_manager.get_logger', return_value=mock_logger):
            manager = ScriptManager(config_dir=mock_config_dir)
            
            assert manager.config_dir == mock_config_dir
            assert manager.scripts_file == mock_config_dir / "scripts.json"
    
    def test_ensure_config_dir_creation(self, temp_dir, mock_logger):
        """Test that config directory is created if it doesn't exist."""
        config_dir = temp_dir / "new_config"
        
        with patch('services.script_manager.get_logger', return_value=mock_logger):
            manager = ScriptManager(config_dir=config_dir)
            
            assert config_dir.exists()
            assert config_dir.is_dir()


class TestScriptCRUDOperations:
    """Test script CRUD (Create, Read, Update, Delete) operations."""
    
    @pytest.fixture
    def script_manager(self, mock_config_dir, mock_logger):
        """Create a ScriptManager instance for testing."""
        with patch('services.script_manager.get_logger', return_value=mock_logger):
            return ScriptManager(config_dir=mock_config_dir)
    
    def test_add_script_success(self, script_manager):
        """Test adding a new script successfully."""
        script_id = script_manager.add_script(
            name="Test Script",
            script_type=ScriptType.HOST_WINDOWS,
            script_path="test.bat",
            description="A test script"
        )
        
        assert script_id is not None
        assert script_id in script_manager.scripts
        
        script = script_manager.scripts[script_id]
        assert script.name == "Test Script"
        assert script.script_type == ScriptType.HOST_WINDOWS
        assert script.script_path == "test.bat"
        assert script.description == "A test script"
        assert script.run_count == 0
        assert script.is_visible is True
    
    def test_add_script_duplicate_name(self, script_manager):
        """Test adding script with duplicate name."""
        # Add first script
        script_id1 = script_manager.add_script(
            name="Duplicate Name",
            script_type=ScriptType.HOST_WINDOWS,
            script_path="script1.bat"
        )
        
        # Add second script with same name (should be allowed)
        script_id2 = script_manager.add_script(
            name="Duplicate Name",
            script_type=ScriptType.HOST_LINUX,
            script_path="script2.sh"
        )
        
        assert script_id1 != script_id2
        assert script_id1 in script_manager.scripts
        assert script_id2 in script_manager.scripts
    
    def test_remove_script_success(self, script_manager):
        """Test removing a script successfully."""
        # Add script first
        script_id = script_manager.add_script(
            name="To Be Removed",
            script_type=ScriptType.DEVICE,
            script_path="remove_me.sh"
        )
        
        assert script_id in script_manager.scripts
        
        # Remove script
        success = script_manager.remove_script(script_id)
        
        assert success is True
        assert script_id not in script_manager.scripts
    
    def test_remove_script_nonexistent(self, script_manager):
        """Test removing a nonexistent script."""
        fake_id = "nonexistent-script-id"
        success = script_manager.remove_script(fake_id)
        
        assert success is False
    
    def test_update_script_success(self, script_manager):
        """Test updating a script successfully."""
        # Add script first
        script_id = script_manager.add_script(
            name="Original Name",
            script_type=ScriptType.HOST_WINDOWS,
            script_path="original.bat"
        )
        
        # Update script
        success = script_manager.update_script(
            script_id,
            name="Updated Name",
            description="Updated description"
        )
        
        assert success is True
        
        script = script_manager.scripts[script_id]
        assert script.name == "Updated Name"
        assert script.description == "Updated description"
        assert script.script_path == "original.bat"  # Unchanged
    
    def test_update_script_nonexistent(self, script_manager):
        """Test updating a nonexistent script."""
        fake_id = "nonexistent-script-id"
        success = script_manager.update_script(fake_id, name="New Name")
        
        assert success is False
    
    def test_get_script_success(self, script_manager):
        """Test getting a script successfully."""
        script_id = script_manager.add_script(
            name="Get Me",
            script_type=ScriptType.HOST_LINUX,
            script_path="get_me.sh"
        )
        
        script = script_manager.get_script(script_id)
        
        assert script is not None
        assert script.name == "Get Me"
        assert script.id == script_id
    
    def test_get_script_nonexistent(self, script_manager):
        """Test getting a nonexistent script."""
        fake_id = "nonexistent-script-id"
        script = script_manager.get_script(fake_id)
        
        assert script is None
    
    def test_get_all_scripts(self, script_manager):
        """Test getting all scripts."""
        # Add multiple scripts
        script_ids = []
        for i in range(3):
            script_id = script_manager.add_script(
                name=f"Script {i}",
                script_type=ScriptType.HOST_WINDOWS,
                script_path=f"script_{i}.bat"
            )
            script_ids.append(script_id)
        
        all_scripts = script_manager.get_all_scripts()
        
        assert len(all_scripts) == 3
        assert all(isinstance(script, Script) for script in all_scripts)
    
    def test_get_scripts_by_type(self, script_manager):
        """Test getting scripts filtered by type."""
        # Add scripts of different types
        windows_id = script_manager.add_script(
            name="Windows Script",
            script_type=ScriptType.HOST_WINDOWS,
            script_path="windows.bat"
        )
        linux_id = script_manager.add_script(
            name="Linux Script",
            script_type=ScriptType.HOST_LINUX,
            script_path="linux.sh"
        )
        device_id = script_manager.add_script(
            name="Device Script",
            script_type=ScriptType.DEVICE,
            script_path="device.sh"
        )
        
        # Get Windows scripts
        windows_scripts = script_manager.get_scripts_by_type(ScriptType.HOST_WINDOWS)
        assert len(windows_scripts) == 1
        assert windows_scripts[0].id == windows_id
        
        # Get Linux scripts
        linux_scripts = script_manager.get_scripts_by_type(ScriptType.HOST_LINUX)
        assert len(linux_scripts) == 1
        assert linux_scripts[0].id == linux_id


class TestScriptPersistence:
    """Test script persistence (save/load) functionality."""
    
    @pytest.fixture
    def script_manager(self, mock_config_dir, mock_logger):
        """Create ScriptManager with mocked file operations."""
        with patch('services.script_manager.get_logger', return_value=mock_logger):
            return ScriptManager(config_dir=mock_config_dir)
    
    def test_save_scripts_success(self, script_manager, mock_config_dir):
        """Test saving scripts to file successfully."""
        # Add a test script
        script_manager.add_script(
            name="Test Save",
            script_type=ScriptType.HOST_WINDOWS,
            script_path="test_save.bat"
        )
        
        # Mock file writing
        with patch('builtins.open', mock_open()) as mock_file:
            script_manager._save_scripts()
            
            # Verify file was opened for writing
            mock_file.assert_called_once_with(
                script_manager.scripts_file, 'w', encoding='utf-8'
            )
    
    def test_load_scripts_success(self, script_manager):
        """Test loading scripts from file successfully."""
        # Create sample script data
        sample_scripts = {
            "script-123": {
                "id": "script-123",
                "name": "Loaded Script",
                "script_type": "host_windows",
                "script_path": "loaded.bat",
                "description": "Loaded from file",
                "created_at": "2024-01-01T12:00:00",
                "last_run": "",
                "run_count": 5,
                "is_template": False,
                "is_visible": True
            }
        }
        
        # Mock file reading
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_scripts))):
            with patch.object(script_manager.scripts_file, 'exists', return_value=True):
                script_manager._load_scripts()
        
        assert len(script_manager.scripts) == 1
        assert "script-123" in script_manager.scripts
        
        script = script_manager.scripts["script-123"]
        assert script.name == "Loaded Script"
        assert script.run_count == 5
    
    def test_load_scripts_file_not_exists(self, script_manager):
        """Test loading scripts when file doesn't exist."""
        with patch.object(script_manager.scripts_file, 'exists', return_value=False):
            script_manager._load_scripts()
        
        # Should not crash and scripts should be empty
        assert len(script_manager.scripts) == 0
    
    def test_load_scripts_invalid_json(self, script_manager):
        """Test loading scripts with invalid JSON."""
        invalid_json = "{ invalid json content"
        
        with patch('builtins.open', mock_open(read_data=invalid_json)):
            with patch.object(script_manager.scripts_file, 'exists', return_value=True):
                script_manager._load_scripts()  # Should not crash
        
        assert len(script_manager.scripts) == 0


class TestScriptExecution:
    """Test script execution functionality."""
    
    @pytest.fixture
    def script_manager(self, mock_config_dir, mock_logger):
        """Create ScriptManager for execution testing."""
        with patch('services.script_manager.get_logger', return_value=mock_logger):
            return ScriptManager(config_dir=mock_config_dir)
    
    def test_execute_script_success(self, script_manager):
        """Test executing a script successfully."""
        # Add a test script
        script_id = script_manager.add_script(
            name="Execute Me",
            script_type=ScriptType.HOST_WINDOWS,
            script_path="execute_me.bat"
        )
        
        # Mock the execution worker
        with patch('services.script_manager.ScriptExecutionWorker') as MockWorker:
            mock_worker = Mock()
            MockWorker.return_value = mock_worker
            
            execution_id = script_manager.execute_script(script_id)
            
            assert execution_id is not None
            assert execution_id in script_manager.executions
            assert execution_id in script_manager.active_workers
            
            # Verify worker was created and started
            MockWorker.assert_called_once()
            mock_worker.start.assert_called_once()
    
    def test_execute_script_nonexistent(self, script_manager):
        """Test executing a nonexistent script."""
        fake_id = "nonexistent-script-id"
        execution_id = script_manager.execute_script(fake_id)
        
        assert execution_id is None
    
    def test_execute_script_device_type_no_device(self, script_manager):
        """Test executing device script without specifying device."""
        script_id = script_manager.add_script(
            name="Device Script",
            script_type=ScriptType.DEVICE,
            script_path="device_script.sh"
        )
        
        execution_id = script_manager.execute_script(script_id)
        
        # Should fail without device specified
        assert execution_id is None
    
    def test_cancel_script_execution(self, script_manager):
        """Test canceling script execution."""
        script_id = script_manager.add_script(
            name="Cancel Me",
            script_type=ScriptType.HOST_WINDOWS,
            script_path="cancel_me.bat"
        )
        
        with patch('services.script_manager.ScriptExecutionWorker') as MockWorker:
            mock_worker = Mock()
            MockWorker.return_value = mock_worker
            
            execution_id = script_manager.execute_script(script_id)
            
            # Cancel the execution
            success = script_manager.cancel_execution(execution_id)
            
            assert success is True
            mock_worker.cancel.assert_called_once()
    
    def test_get_execution_status(self, script_manager):
        """Test getting execution status."""
        script_id = script_manager.add_script(
            name="Status Check",
            script_type=ScriptType.HOST_LINUX,
            script_path="status.sh"
        )
        
        with patch('services.script_manager.ScriptExecutionWorker'):
            execution_id = script_manager.execute_script(script_id)
            
            # Check initial status
            status = script_manager.get_execution_status(execution_id)
            assert status == ScriptStatus.RUNNING
            
            # Test nonexistent execution
            fake_id = "fake-execution-id"
            status = script_manager.get_execution_status(fake_id)
            assert status is None


class TestScriptImportExport:
    """Test script import/export functionality."""
    
    @pytest.fixture
    def script_manager(self, mock_config_dir, mock_logger):
        """Create ScriptManager for import/export testing."""
        with patch('services.script_manager.get_logger', return_value=mock_logger):
            return ScriptManager(config_dir=mock_config_dir)
    
    def test_export_scripts_to_json_all(self, script_manager, temp_dir):
        """Test exporting all scripts to JSON."""
        # Add test scripts
        for i in range(3):
            script_manager.add_script(
                name=f"Export Script {i}",
                script_type=ScriptType.HOST_WINDOWS,
                script_path=f"export_{i}.bat",
                description=f"Script {i} for export"
            )
        
        export_file = temp_dir / "export_all.json"
        
        with patch('builtins.open', mock_open()) as mock_file:
            success = script_manager.export_scripts_to_json(str(export_file))
            
            assert success is True
            mock_file.assert_called_once_with(str(export_file), 'w', encoding='utf-8')
    
    def test_export_scripts_to_json_selected(self, script_manager, temp_dir):
        """Test exporting selected scripts to JSON."""
        # Add test scripts
        script_ids = []
        for i in range(5):
            script_id = script_manager.add_script(
                name=f"Script {i}",
                script_type=ScriptType.HOST_WINDOWS,
                script_path=f"script_{i}.bat"
            )
            script_ids.append(script_id)
        
        # Export only first 2 scripts
        selected_ids = script_ids[:2]
        export_file = temp_dir / "export_selected.json"
        
        with patch('builtins.open', mock_open()) as mock_file:
            success = script_manager.export_scripts_to_json(str(export_file), selected_ids)
            
            assert success is True
    
    def test_import_scripts_from_json_success(self, script_manager, temp_dir):
        """Test importing scripts from JSON successfully."""
        import_data = [
            {
                "name": "Imported Script 1",
                "script_path": "imported1.bat",
                "type": "host_windows",
                "description": "First imported script",
                "isTemplate": False,
                "show": True,
                "content": "@echo off\necho Imported script 1"
            },
            {
                "name": "Imported Script 2",
                "script_path": "imported2.sh",
                "type": "host_linux",
                "description": "Second imported script",
                "isTemplate": True,
                "show": True,
                "content": "#!/bin/bash\necho 'Imported script 2'"
            }
        ]
        
        import_file = temp_dir / "import.json"
        
        with patch('builtins.open', mock_open(read_data=json.dumps(import_data))):
            with patch('os.chmod'):  # Mock file permission change
                with patch('pathlib.Path.mkdir'):  # Mock directory creation
                    imported_count, skipped_count = script_manager.import_scripts_from_json(
                        str(import_file), overwrite_existing=False
                    )
        
        assert imported_count == 2
        assert skipped_count == 0
    
    def test_import_scripts_from_json_invalid_file(self, script_manager):
        """Test importing from invalid JSON file."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            imported_count, skipped_count = script_manager.import_scripts_from_json(
                "nonexistent.json", overwrite_existing=False
            )
        
        assert imported_count == 0
        assert skipped_count == 0
    
    def test_import_scripts_from_json_malformed(self, script_manager):
        """Test importing from malformed JSON."""
        malformed_data = "{ invalid json }"
        
        with patch('builtins.open', mock_open(read_data=malformed_data)):
            imported_count, skipped_count = script_manager.import_scripts_from_json(
                "malformed.json", overwrite_existing=False
            )
        
        assert imported_count == 0
        assert skipped_count == 0


class TestScriptManagerEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def script_manager(self, mock_config_dir, mock_logger):
        """Create ScriptManager for edge case testing."""
        with patch('services.script_manager.get_logger', return_value=mock_logger):
            return ScriptManager(config_dir=mock_config_dir)
    
    def test_add_script_empty_name(self, script_manager):
        """Test adding script with empty name."""
        script_id = script_manager.add_script(
            name="",
            script_type=ScriptType.HOST_WINDOWS,
            script_path="empty_name.bat"
        )
        
        # Should still create script (validation is UI responsibility)
        assert script_id is not None
        assert script_manager.scripts[script_id].name == ""
    
    def test_add_script_very_long_name(self, script_manager):
        """Test adding script with very long name."""
        long_name = "x" * 1000
        script_id = script_manager.add_script(
            name=long_name,
            script_type=ScriptType.HOST_WINDOWS,
            script_path="long_name.bat"
        )
        
        assert script_id is not None
        assert script_manager.scripts[script_id].name == long_name
    
    def test_add_script_unicode_name(self, script_manager):
        """Test adding script with unicode characters."""
        unicode_name = "脚本测试 🚀"
        script_id = script_manager.add_script(
            name=unicode_name,
            script_type=ScriptType.HOST_WINDOWS,
            script_path="unicode.bat"
        )
        
        assert script_id is not None
        assert script_manager.scripts[script_id].name == unicode_name
    
    def test_cleanup_old_executions(self, script_manager):
        """Test cleanup of old execution records."""
        # Add some mock executions with different ages
        old_execution_id = "old-execution"
        recent_execution_id = "recent-execution"
        
        old_time = datetime(2020, 1, 1).isoformat()
        recent_time = datetime.now().isoformat()
        
        script_manager.executions[old_execution_id] = Mock()
        script_manager.executions[old_execution_id].start_time = old_time
        script_manager.executions[recent_execution_id] = Mock()
        script_manager.executions[recent_execution_id].start_time = recent_time
        
        # Cleanup old executions (older than 30 days)
        script_manager.cleanup_old_executions(max_age_days=30, max_count=100)
        
        # Old execution should be removed, recent should remain
        assert old_execution_id not in script_manager.executions
        assert recent_execution_id in script_manager.executions
    
    @pytest.mark.parametrize("invalid_type", [
        "invalid_type",
        "",
        None,
        123,
        []
    ])
    def test_add_script_invalid_type(self, script_manager, invalid_type):
        """Test adding script with invalid script type."""
        # This should raise an exception or handle gracefully
        with pytest.raises((ValueError, TypeError, AttributeError)):
            script_manager.add_script(
                name="Invalid Type Script",
                script_type=invalid_type,
                script_path="invalid.bat"
            )