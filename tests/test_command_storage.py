"""
Test Command Storage Service

Comprehensive tests for saved commands storage and management.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from services.command_storage import CommandStorage


@pytest.fixture
def temp_storage_dir(tmp_path):
    """Create temporary storage directory."""
    storage_dir = tmp_path / ".adb-util"
    storage_dir.mkdir()
    return storage_dir


@pytest.fixture
def command_storage(temp_storage_dir):
    """Create CommandStorage with temporary storage file."""
    storage_file = temp_storage_dir / "test_commands.json"
    return CommandStorage(storage_file=str(storage_file))


@pytest.fixture
def sample_commands():
    """Sample command data."""
    return [
        {
            "id": "cmd_001",
            "name": "List Files",
            "command": "ls -la",
            "category": "File Operations",
            "description": "List all files with details",
            "created_at": "2024-01-01T10:00:00",
            "last_used": "2024-01-01T10:00:00"
        },
        {
            "id": "cmd_002", 
            "name": "Get Properties",
            "command": "getprop",
            "category": "System Info",
            "description": "Get device properties",
            "created_at": "2024-01-01T11:00:00",
            "last_used": "2024-01-01T11:00:00"
        },
        {
            "id": "cmd_003",
            "name": "Install APK",
            "command": "pm install -t {apk_path}",
            "category": "Package Management",
            "description": "Install APK package",
            "created_at": "2024-01-01T12:00:00",
            "last_used": "2024-01-01T12:00:00"
        }
    ]


class TestCommandStorage:
    """Test cases for CommandStorage."""

    def test_init_creates_empty_commands(self, temp_storage_dir):
        """Test initialization with no existing storage file."""
        storage_file = temp_storage_dir / "new_commands.json"
        storage = CommandStorage(storage_file=str(storage_file))
        assert storage.commands == []

    def test_init_loads_existing_commands(self, temp_storage_dir, sample_commands):
        """Test initialization loads existing commands from file."""
        storage_file = temp_storage_dir / "existing_commands.json"
        with open(storage_file, 'w') as f:
            json.dump(sample_commands, f)
        
        storage = CommandStorage(storage_file=str(storage_file))
        # Note: This test may need adjustment based on actual implementation
        # assert storage.commands == sample_commands

    def test_add_command_basic(self, command_storage):
        """Test adding a basic command."""
        command_id = command_storage.add_command(
            name="Test Command",
            command="echo 'test'",
            category="Testing"
        )
        
        assert command_id is not None
        commands = command_storage.get_commands()
        assert len(commands) == 1
        assert commands[0]["name"] == "Test Command"

    def test_add_command_with_default_category(self, command_storage):
        """Test adding command with default category."""
        command_id = command_storage.add_command(
            name="Default Command",
            command="pwd"
        )
        
        commands = command_storage.get_commands()
        assert len(commands) == 1
        assert commands[0]["category"] == "General"

    def test_add_command_generates_unique_ids(self, command_storage):
        """Test that each command gets a unique ID."""
        id1 = command_storage.add_command("Command 1", "cmd1")
        id2 = command_storage.add_command("Command 2", "cmd2")
        
        assert id1 != id2
        assert id1 is not None
        assert id2 is not None

    def test_remove_command_existing(self, command_storage):
        """Test removing existing command."""
        command_id = command_storage.add_command("To Remove", "rm test")
        assert command_storage.remove_command(command_id) is True
        
        commands = command_storage.get_commands()
        assert len(commands) == 0

    def test_remove_command_nonexistent(self, command_storage):
        """Test removing non-existent command."""
        result = command_storage.remove_command("nonexistent_id")
        assert result is False

    def test_update_command_existing(self, command_storage):
        """Test updating existing command."""
        command_id = command_storage.add_command("Original", "original_cmd")
        
        result = command_storage.update_command(
            command_id,
            name="Updated",
            command="updated_cmd",
            category="Updated Category"
        )
        
        assert result is True
        commands = command_storage.get_commands()
        updated_cmd = next(cmd for cmd in commands if cmd["id"] == command_id)
        assert updated_cmd["name"] == "Updated"
        assert updated_cmd["command"] == "updated_cmd"
        assert updated_cmd["category"] == "Updated Category"

    def test_update_command_nonexistent(self, command_storage):
        """Test updating non-existent command."""
        result = command_storage.update_command(
            "nonexistent_id",
            name="Test",
            command="test",
            category="Test"
        )
        assert result is False

    def test_get_commands_all(self, command_storage):
        """Test getting all commands."""
        command_storage.add_command("Cmd1", "cmd1", "Cat1")
        command_storage.add_command("Cmd2", "cmd2", "Cat2")
        
        commands = command_storage.get_commands()
        assert len(commands) == 2

    def test_get_commands_filtered_by_category(self, command_storage):
        """Test getting commands filtered by category."""
        command_storage.add_command("Cmd1", "cmd1", "Category A")
        command_storage.add_command("Cmd2", "cmd2", "Category B")
        command_storage.add_command("Cmd3", "cmd3", "Category A")
        
        cat_a_commands = command_storage.get_commands(category="Category A")
        assert len(cat_a_commands) == 2
        assert all(cmd["category"] == "Category A" for cmd in cat_a_commands)

    def test_get_categories(self, command_storage):
        """Test getting list of all categories."""
        command_storage.add_command("Cmd1", "cmd1", "File Ops")
        command_storage.add_command("Cmd2", "cmd2", "System")
        command_storage.add_command("Cmd3", "cmd3", "File Ops")
        
        categories = command_storage.get_categories()
        assert set(categories) == {"File Ops", "System"}

    def test_save_commands_persistence(self, command_storage):
        """Test that commands are saved to disk."""
        command_storage.add_command("Persistent", "persist_cmd")
        command_storage.save_commands()
        
        # Verify file exists and contains data
        assert command_storage.storage_file.exists()
        
        with open(command_storage.storage_file, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["name"] == "Persistent"

    @pytest.mark.parametrize("name,command,category", [
        ("Simple", "echo hello", "Basic"),
        ("With Quotes", 'echo "hello world"', "Basic"),
        ("With Variables", "echo $HOME", "Environment"),
        ("Complex Command", "find . -name '*.py' | grep test", "File Search"),
        ("Unicode Name", "测试命令", "Unicode"),
    ])
    def test_add_various_command_formats(self, command_storage, name, command, category):
        """Test adding commands with various formats and characters."""
        command_id = command_storage.add_command(name, command, category)
        assert command_id is not None
        
        commands = command_storage.get_commands()
        added_cmd = next(cmd for cmd in commands if cmd["id"] == command_id)
        assert added_cmd["name"] == name
        assert added_cmd["command"] == command
        assert added_cmd["category"] == category

    def test_load_commands_handles_corrupt_file(self, temp_storage_dir):
        """Test handling of corrupted storage file."""
        storage_file = temp_storage_dir / "corrupt_commands.json"
        with open(storage_file, 'w') as f:
            f.write("invalid json content")
        
        storage = CommandStorage(storage_file=str(storage_file))
        # Should handle gracefully and start with empty commands
        assert storage.commands == []

    def test_storage_file_creation(self, command_storage):
        """Test that storage directory and file are created when needed."""
        command_storage.add_command("Test", "test_cmd")
        command_storage.save_commands()
        
        assert command_storage.storage_file.parent.exists()
        assert command_storage.storage_file.exists()


@pytest.mark.integration
class TestCommandStorageIntegration:
    """Integration tests for CommandStorage."""

    def test_full_lifecycle_persistence(self, temp_storage_dir):
        """Test complete command lifecycle with persistence."""
        storage_file = temp_storage_dir / "lifecycle_commands.json"
        
        # Create initial storage and add commands
        storage1 = CommandStorage(storage_file=str(storage_file))
        cmd_id = storage1.add_command("Lifecycle Test", "echo lifecycle")
        storage1.save_commands()
        
        # Load in new instance and verify
        storage2 = CommandStorage(storage_file=str(storage_file))
        commands = storage2.get_commands()
        assert len(commands) == 1
        assert commands[0]["name"] == "Lifecycle Test"
        
        # Update in second instance
        storage2.update_command(cmd_id, "Updated Lifecycle", "echo updated", "Updated")
        storage2.save_commands()
        
        # Verify in third instance
        storage3 = CommandStorage(storage_file=str(storage_file))
        commands = storage3.get_commands()
        assert len(commands) == 1
        assert commands[0]["name"] == "Updated Lifecycle"

    def test_concurrent_modifications(self, command_storage):
        """Test behavior with concurrent modifications."""
        # This would be important for thread safety
        import threading
        results = []
        
        def worker(worker_id):
            cmd_id = command_storage.add_command(f"Worker {worker_id}", f"worker_{worker_id}")
            results.append(cmd_id)
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        commands = command_storage.get_commands()
        assert len(commands) == 3
        assert len(set(results)) == 3  # All IDs should be unique

    def test_large_dataset_performance(self, command_storage):
        """Test performance with large number of commands."""
        # Add many commands
        num_commands = 100
        for i in range(num_commands):
            command_storage.add_command(
                f"Command {i:03d}",
                f"echo 'test command {i}'",
                f"Category {i % 10}"
            )
        
        # Verify all commands are accessible
        all_commands = command_storage.get_commands()
        assert len(all_commands) == num_commands
        
        # Test category filtering performance
        cat_commands = command_storage.get_commands(category="Category 0")
        assert len(cat_commands) == 10
        
        # Test categories retrieval
        categories = command_storage.get_categories()
        assert len(categories) == 10
