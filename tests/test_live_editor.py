"""
Test Live Editor Service

Tests for the live editing functionality.
"""

import pytest
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services.live_editor import LiveEditorService, LiveEditSession
from src.adb.file_operations import FileInfo, FileOperations


class TestLiveEditorService:
    """Test cases for LiveEditorService."""
    
    def setup_method(self):
        """Set up test environment."""
        self.service = LiveEditorService()
        self.mock_file_ops = Mock(spec=FileOperations)
        self.test_file_info = FileInfo(
            name="test.txt",
            path="/sdcard/test.txt",
            is_directory=False,
            size=100
        )
    
    def test_get_default_editors(self):
        """Test getting default editors for the current platform."""
        editors = self.service.get_default_editors()
        assert isinstance(editors, dict)
        assert len(editors) > 0
        
        # Should have at least notepad on Windows
        if sys.platform == "win32":
            assert "notepad" in editors
    
    def test_is_editor_available(self):
        """Test checking if an editor is available."""
        # Test with a command that should exist on Windows
        if sys.platform == "win32":
            assert self.service.is_editor_available("notepad")
            assert not self.service.is_editor_available("nonexistent_editor_xyz")
    
    def test_create_temp_file(self):
        """Test creating temporary files."""
        temp_file = self.service.create_temp_file("test.txt")
        assert temp_file is not None
        assert temp_file.exists()
        assert temp_file.name.endswith("test.txt")
        
        # Clean up
        temp_file.unlink(missing_ok=True)
    
    def test_session_management(self):
        """Test session management functionality."""
        device_path = "/sdcard/test.txt"
        
        # Initially no sessions
        assert not self.service.is_session_active(device_path)
        assert len(self.service.get_active_sessions()) == 0
        
        # Create a mock session
        temp_file = self.service.create_temp_file("test.txt")
        session = LiveEditSession(
            device_path, 
            temp_file, 
            "notepad", 
            self.mock_file_ops
        )
        
        # Add session manually for testing
        self.service.sessions[device_path] = session
        
        # Check session is active
        assert self.service.is_session_active(device_path)
        assert len(self.service.get_active_sessions()) == 1
        assert device_path in self.service.get_active_sessions()
        
        # Clean up
        session.cleanup()
        del self.service.sessions[device_path]
    
    def test_cleanup(self):
        """Test service cleanup."""
        # This should not raise any exceptions
        self.service.cleanup()


class TestLiveEditSession:
    """Test cases for LiveEditSession."""
    
    def setup_method(self):
        """Set up test environment."""
        self.mock_file_ops = Mock(spec=FileOperations)
        self.temp_file = Path(tempfile.mktemp(suffix=".txt"))
        self.temp_file.touch()  # Create the file
        
        self.session = LiveEditSession(
            "/sdcard/test.txt",
            self.temp_file,
            "notepad" if sys.platform == "win32" else "cat",
            self.mock_file_ops
        )
    
    def teardown_method(self):
        """Clean up after test."""
        self.session.cleanup()
        self.temp_file.unlink(missing_ok=True)
    
    def test_session_creation(self):
        """Test creating a live edit session."""
        assert self.session.device_file_path == "/sdcard/test.txt"
        assert self.session.local_temp_path == self.temp_file
        assert not self.session.is_active
        assert self.session.process is None
    
    def test_update_last_modified(self):
        """Test updating last modified timestamp."""
        self.session.update_last_modified()
        assert self.session.last_modified is not None
        
        initial_time = self.session.last_modified
        
        # Modify the file
        self.temp_file.write_text("new content")
        
        self.session.update_last_modified()
        assert self.session.last_modified > initial_time
    
    def test_has_changes(self):
        """Test detecting file changes."""
        # Initially no changes (no baseline)
        self.session.update_last_modified()
        
        # Modify the file
        import time
        time.sleep(0.1)  # Ensure timestamp difference
        self.temp_file.write_text("modified content")
        
        assert self.session.has_changes()
    
    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_start_editor_windows(self):
        """Test starting editor on Windows."""
        # Use a command that exists but won't actually open UI
        self.session.editor_command = "cmd /c echo test"
        
        result = self.session.start_editor()
        assert result is True
        assert self.session.is_active
        assert self.session.process is not None
        
        # Wait a moment for process to complete
        import time
        time.sleep(0.5)
        
        # Process should have finished
        assert not self.session.is_editor_running()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
