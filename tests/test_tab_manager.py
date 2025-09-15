"""
Test Tab Manager Service

Comprehensive tests for tab creation, management, and lifecycle.
"""

import pytest
from unittest.mock import Mock, patch

from services.tab_manager import TabManager


@pytest.fixture
def tab_manager():
    """Create TabManager instance."""
    return TabManager()


@pytest.fixture
def sample_device_ids():
    """Sample device IDs for testing."""
    return ["device_001", "device_002", "emulator-5554"]


@pytest.fixture
def sample_modes():
    """Sample modes for testing."""
    return ["logcat", "shell", "file_manager"]


class TestTabManager:
    """Test cases for TabManager."""

    def test_init_empty_state(self, tab_manager):
        """Test initialization creates empty state."""
        assert tab_manager.active_tabs == {}
        assert tab_manager.tab_counter == 0

    def test_create_tab_basic(self, tab_manager):
        """Test creating a basic tab."""
        tab_id = tab_manager.create_tab("device_001", "logcat")
        
        assert tab_id is not None
        assert tab_id in tab_manager.active_tabs
        assert tab_manager.active_tabs[tab_id]["device_id"] == "device_001"
        assert tab_manager.active_tabs[tab_id]["mode"] == "logcat"

    def test_create_tab_increments_counter(self, tab_manager):
        """Test that creating tabs increments counter."""
        initial_counter = tab_manager.tab_counter
        
        tab_id1 = tab_manager.create_tab("device_001", "logcat")
        assert tab_manager.tab_counter == initial_counter + 1
        
        tab_id2 = tab_manager.create_tab("device_002", "shell")
        assert tab_manager.tab_counter == initial_counter + 2

    def test_create_tab_unique_ids(self, tab_manager):
        """Test that each tab gets a unique ID."""
        tab_id1 = tab_manager.create_tab("device_001", "logcat")
        tab_id2 = tab_manager.create_tab("device_001", "logcat")  # Same device/mode
        
        assert tab_id1 != tab_id2

    def test_create_multiple_tabs_same_device(self, tab_manager):
        """Test creating multiple tabs for same device with different modes."""
        logcat_tab = tab_manager.create_tab("device_001", "logcat")
        shell_tab = tab_manager.create_tab("device_001", "shell")
        
        assert logcat_tab != shell_tab
        assert len(tab_manager.active_tabs) == 2

    def test_create_multiple_tabs_different_devices(self, tab_manager):
        """Test creating tabs for different devices."""
        tab1 = tab_manager.create_tab("device_001", "logcat")
        tab2 = tab_manager.create_tab("device_002", "logcat")
        
        assert tab1 != tab2
        assert len(tab_manager.active_tabs) == 2

    def test_close_tab_existing(self, tab_manager):
        """Test closing existing tab."""
        tab_id = tab_manager.create_tab("device_001", "logcat")
        
        result = tab_manager.close_tab(tab_id)
        assert result is True
        assert tab_id not in tab_manager.active_tabs

    def test_close_tab_nonexistent(self, tab_manager):
        """Test closing non-existent tab."""
        result = tab_manager.close_tab("nonexistent_tab_id")
        assert result is False

    def test_get_tab_title_format(self, tab_manager):
        """Test tab title generation format."""
        title = tab_manager.get_tab_title("device_123", "logcat")
        assert title == "device_123-logcat"

    @pytest.mark.parametrize("device_id,mode,expected_title", [
        ("device_001", "logcat", "device_001-logcat"),
        ("emulator-5554", "shell", "emulator-5554-shell"),
        ("192.168.1.100", "file_manager", "192.168.1.100-file_manager"),
        ("long_device_name_123", "mode", "long_device_name_123-mode"),
    ])
    def test_get_tab_title_various_inputs(self, tab_manager, device_id, mode, expected_title):
        """Test tab title generation with various device IDs and modes."""
        title = tab_manager.get_tab_title(device_id, mode)
        assert title == expected_title

    def test_get_active_tabs_empty(self, tab_manager):
        """Test getting active tabs when none exist."""
        tabs = tab_manager.get_active_tabs()
        assert tabs == []

    def test_get_active_tabs_multiple(self, tab_manager):
        """Test getting active tabs when multiple exist."""
        tab1 = tab_manager.create_tab("device_001", "logcat")
        tab2 = tab_manager.create_tab("device_002", "shell")
        
        tabs = tab_manager.get_active_tabs()
        assert len(tabs) == 2
        
        tab_ids = [tab["id"] for tab in tabs]
        assert tab1 in tab_ids
        assert tab2 in tab_ids

    def test_save_tab_state(self, tab_manager):
        """Test saving tab state."""
        tab_id = tab_manager.create_tab("device_001", "logcat")
        state = {
            "scroll_position": 1000,
            "filter_text": "error",
            "log_level": "debug"
        }
        
        tab_manager.save_tab_state(tab_id, state)
        
        # Verify state is stored
        assert tab_manager.active_tabs[tab_id]["state"] == state

    def test_save_tab_state_nonexistent_tab(self, tab_manager):
        """Test saving state for non-existent tab."""
        state = {"test": "value"}
        # Should handle gracefully without error
        tab_manager.save_tab_state("nonexistent_tab", state)

    def test_restore_tab_state_existing(self, tab_manager):
        """Test restoring state for existing tab."""
        tab_id = tab_manager.create_tab("device_001", "logcat")
        original_state = {"setting1": "value1", "setting2": 42}
        
        tab_manager.save_tab_state(tab_id, original_state)
        restored_state = tab_manager.restore_tab_state(tab_id)
        
        assert restored_state == original_state

    def test_restore_tab_state_nonexistent(self, tab_manager):
        """Test restoring state for non-existent tab."""
        restored_state = tab_manager.restore_tab_state("nonexistent_tab")
        assert restored_state == {}

    def test_tab_lifecycle_complete(self, tab_manager):
        """Test complete tab lifecycle: create, save state, restore state, close."""
        # Create tab
        tab_id = tab_manager.create_tab("device_001", "logcat")
        assert tab_id in tab_manager.active_tabs
        
        # Save state
        state = {"filter": "error", "paused": False}
        tab_manager.save_tab_state(tab_id, state)
        
        # Restore state
        restored_state = tab_manager.restore_tab_state(tab_id)
        assert restored_state == state
        
        # Close tab
        result = tab_manager.close_tab(tab_id)
        assert result is True
        assert tab_id not in tab_manager.active_tabs

    def test_multiple_tabs_independent_states(self, tab_manager):
        """Test that multiple tabs have independent states."""
        tab1 = tab_manager.create_tab("device_001", "logcat")
        tab2 = tab_manager.create_tab("device_002", "shell")
        
        state1 = {"filter": "debug", "line_count": 100}
        state2 = {"command_history": ["ls", "pwd"], "current_dir": "/sdcard"}
        
        tab_manager.save_tab_state(tab1, state1)
        tab_manager.save_tab_state(tab2, state2)
        
        restored_state1 = tab_manager.restore_tab_state(tab1)
        restored_state2 = tab_manager.restore_tab_state(tab2)
        
        assert restored_state1 == state1
        assert restored_state2 == state2

    def test_tab_info_structure(self, tab_manager):
        """Test that tab info contains expected structure."""
        tab_id = tab_manager.create_tab("device_001", "logcat")
        tab_info = tab_manager.active_tabs[tab_id]
        
        # Check required fields
        assert "device_id" in tab_info
        assert "mode" in tab_info
        assert "created_at" in tab_info
        assert tab_info["device_id"] == "device_001"
        assert tab_info["mode"] == "logcat"

    def test_concurrent_tab_operations(self, tab_manager):
        """Test concurrent tab operations."""
        import threading
        created_tabs = []
        
        def worker(worker_id):
            tab_id = tab_manager.create_tab(f"device_{worker_id}", "logcat")
            created_tabs.append(tab_id)
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All tabs should be created and unique
        assert len(created_tabs) == 5
        assert len(set(created_tabs)) == 5  # All unique
        assert len(tab_manager.active_tabs) == 5


@pytest.mark.integration
class TestTabManagerIntegration:
    """Integration tests for TabManager."""

    def test_realistic_usage_scenario(self, tab_manager):
        """Test realistic usage scenario with multiple devices and modes."""
        devices = ["device_001", "device_002", "emulator-5554"]
        modes = ["logcat", "shell", "file_manager"]
        
        created_tabs = []
        
        # Create tabs for different device-mode combinations
        for device in devices:
            for mode in modes:
                tab_id = tab_manager.create_tab(device, mode)
                created_tabs.append(tab_id)
                
                # Save some state
                state = {
                    "device": device,
                    "mode": mode,
                    "timestamp": "2024-01-01T10:00:00"
                }
                tab_manager.save_tab_state(tab_id, state)
        
        # Verify all tabs created
        assert len(created_tabs) == 9  # 3 devices × 3 modes
        assert len(tab_manager.active_tabs) == 9
        
        # Close some tabs
        tabs_to_close = created_tabs[:3]
        for tab_id in tabs_to_close:
            result = tab_manager.close_tab(tab_id)
            assert result is True
        
        # Verify remaining tabs
        assert len(tab_manager.active_tabs) == 6
        
        # Verify states are preserved for remaining tabs
        remaining_tabs = [t for t in created_tabs if t not in tabs_to_close]
        for tab_id in remaining_tabs:
            state = tab_manager.restore_tab_state(tab_id)
            assert "device" in state
            assert "mode" in state

    def test_memory_management(self, tab_manager):
        """Test that closed tabs don't leak memory."""
        # Create many tabs
        tab_ids = []
        for i in range(100):
            tab_id = tab_manager.create_tab(f"device_{i}", "logcat")
            tab_ids.append(tab_id)
        
        assert len(tab_manager.active_tabs) == 100
        
        # Close all tabs
        for tab_id in tab_ids:
            tab_manager.close_tab(tab_id)
        
        # Verify cleanup
        assert len(tab_manager.active_tabs) == 0

    def test_state_persistence_edge_cases(self, tab_manager):
        """Test state persistence with edge case data."""
        tab_id = tab_manager.create_tab("device_001", "logcat")
        
        edge_case_states = [
            {},  # Empty state
            {"unicode": "测试数据"},  # Unicode data
            {"nested": {"deep": {"value": 42}}},  # Nested objects
            {"list": [1, 2, 3, {"inner": "value"}]},  # Complex lists
            {"null_value": None},  # Null values
            {"boolean": True, "false_bool": False},  # Booleans
        ]
        
        for state in edge_case_states:
            tab_manager.save_tab_state(tab_id, state)
            restored = tab_manager.restore_tab_state(tab_id)
            assert restored == state
