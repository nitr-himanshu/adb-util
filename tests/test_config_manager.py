"""
Test Config Manager Service

Comprehensive tests for configuration management functionality.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, mock_open

from services.config_manager import ConfigManager


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory."""
    config_dir = tmp_path / ".adb-util"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def config_manager(temp_config_dir):
    """Create ConfigManager with temporary config file."""
    config_file = temp_config_dir / "test_config.json"
    return ConfigManager(config_file=str(config_file))


@pytest.fixture
def sample_config():
    """Sample configuration data."""
    return {
        "app": {
            "theme": "dark",
            "last_device": "test_device_123",
            "window_geometry": {"width": 1024, "height": 768}
        },
        "logging": {
            "default_buffer": "main",
            "auto_scroll": True,
            "max_lines": 10000
        }
    }


class TestConfigManager:
    """Test cases for ConfigManager."""

    def test_init_creates_default_config(self, temp_config_dir):
        """Test that initialization creates default config when file doesn't exist."""
        config_file = temp_config_dir / "new_config.json"
        manager = ConfigManager(config_file=str(config_file))
        
        assert manager.config is not None
        assert config_file.exists()

    def test_init_loads_existing_config(self, temp_config_dir, sample_config):
        """Test that initialization loads existing config file."""
        config_file = temp_config_dir / "existing_config.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        manager = ConfigManager(config_file=str(config_file))
        assert manager.config == sample_config

    def test_get_existing_key(self, config_manager, sample_config):
        """Test getting existing configuration value."""
        config_manager.config = sample_config
        assert config_manager.get("app.theme") == "dark"

    def test_get_missing_key_with_default(self, config_manager):
        """Test getting missing key returns default value."""
        result = config_manager.get("missing.key", "default_value")
        assert result == "default_value"

    def test_get_missing_key_without_default(self, config_manager):
        """Test getting missing key returns None."""
        result = config_manager.get("missing.key")
        assert result is None

    def test_set_new_key(self, config_manager):
        """Test setting new configuration value."""
        config_manager.set("new.key", "new_value")
        assert config_manager.get("new.key") == "new_value"

    def test_set_existing_key(self, config_manager, sample_config):
        """Test updating existing configuration value."""
        config_manager.config = sample_config.copy()
        config_manager.set("app.theme", "light")
        assert config_manager.get("app.theme") == "light"

    def test_save_config_creates_directory(self, tmp_path):
        """Test that save_config creates directory if it doesn't exist."""
        config_dir = tmp_path / "new_dir" / ".adb-util"
        config_file = config_dir / "config.json"
        
        manager = ConfigManager(config_file=str(config_file))
        manager.set("test.key", "test_value")
        manager.save_config()
        
        assert config_dir.exists()
        assert config_file.exists()

    def test_save_config_writes_data(self, config_manager, sample_config):
        """Test that save_config writes data correctly."""
        config_manager.config = sample_config
        config_manager.save_config()
        
        # Read file and verify content
        with open(config_manager.config_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == sample_config

    def test_load_config_handles_invalid_json(self, temp_config_dir):
        """Test that load_config handles invalid JSON gracefully."""
        config_file = temp_config_dir / "invalid.json"
        with open(config_file, 'w') as f:
            f.write("invalid json content")
        
        manager = ConfigManager(config_file=str(config_file))
        # Should fall back to default config
        assert manager.config is not None

    def test_nested_key_access(self, config_manager, sample_config):
        """Test accessing nested configuration keys."""
        config_manager.config = sample_config
        
        # Test dot notation access (if implemented)
        if hasattr(config_manager, 'get_nested'):
            assert config_manager.get_nested("app.theme") == "dark"
            assert config_manager.get_nested("logging.auto_scroll") is True

    @pytest.mark.parametrize("config_data,key,expected", [
        ({"simple": "value"}, "simple", "value"),
        ({"nested": {"key": "value"}}, "nested", {"key": "value"}),
        ({"list": [1, 2, 3]}, "list", [1, 2, 3]),
        ({"boolean": True}, "boolean", True),
        ({"number": 42}, "number", 42),
    ])
    def test_various_data_types(self, config_manager, config_data, key, expected):
        """Test handling various data types in configuration."""
        config_manager.config = config_data
        assert config_manager.get(key) == expected

    def test_concurrent_access(self, config_manager):
        """Test concurrent access to configuration."""
        # This would be important for thread-safe access
        import threading
        results = []
        
        def worker():
            config_manager.set("thread.test", "value")
            results.append(config_manager.get("thread.test"))
        
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 5
        assert all(r == "value" for r in results)


@pytest.mark.integration
class TestConfigManagerIntegration:
    """Integration tests for ConfigManager."""

    def test_full_lifecycle(self, temp_config_dir):
        """Test complete configuration lifecycle."""
        config_file = temp_config_dir / "lifecycle_config.json"
        
        # Create and configure
        manager1 = ConfigManager(config_file=str(config_file))
        manager1.set("test.value", "original")
        manager1.save_config()
        
        # Load in new instance
        manager2 = ConfigManager(config_file=str(config_file))
        assert manager2.get("test.value") == "original"
        
        # Update and save
        manager2.set("test.value", "updated")
        manager2.save_config()
        
        # Verify persistence
        manager3 = ConfigManager(config_file=str(config_file))
        assert manager3.get("test.value") == "updated"

    def test_file_permissions_error(self, temp_config_dir):
        """Test handling of file permission errors."""
        config_file = temp_config_dir / "readonly_config.json"
        
        # Create config
        manager = ConfigManager(config_file=str(config_file))
        manager.set("test.key", "test_value")
        manager.save_config()
        
        # Make file readonly (on Windows, this might not fully work)
        try:
            config_file.chmod(0o444)
            
            # Try to save - should handle error gracefully
            manager.set("another.key", "another_value")
            # Should not raise exception
            manager.save_config()
        finally:
            # Restore permissions for cleanup
            config_file.chmod(0o666)
