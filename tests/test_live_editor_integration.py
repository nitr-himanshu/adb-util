"""
Test Live Editor Integration

Tests the integration of live editing in the file manager.
"""

import pytest
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.gui.file_manager import FileManager, LiveEditWorker
from src.adb.file_operations import FileInfo, FileOperations
from src.services.live_editor import LiveEditorService


class TestLiveEditorIntegration:
    """Test cases for live editor integration in file manager."""
    
    @classmethod
    def setup_class(cls):
        """Set up Qt application for tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setup_method(self):
        """Set up test environment."""
        # Create mock file operations
        self.mock_file_ops = Mock(spec=FileOperations)
        self.mock_file_ops.pull_file = AsyncMock(return_value=True)
        self.mock_file_ops.push_file = AsyncMock(return_value=True)
        
        # Create file manager with mock
        with patch('src.gui.file_manager.FileOperations') as mock_file_ops_class:
            mock_file_ops_class.return_value = self.mock_file_ops
            self.file_manager = FileManager("test_device")
        
        # Test file info
        self.test_file_info = FileInfo(
            name="test.txt",
            path="/sdcard/test.txt",
            is_directory=False,
            size=100
        )
    
    def teardown_method(self):
        """Clean up after test."""
        if hasattr(self, 'file_manager'):
            self.file_manager.cleanup()
    
    def test_file_manager_has_live_editor(self):
        """Test that file manager has live editor service."""
        assert hasattr(self.file_manager, 'live_editor')
        assert isinstance(self.file_manager.live_editor, LiveEditorService)
    
    def test_context_menu_includes_open_with(self):
        """Test that context menu includes 'Open with...' option."""
        # This is more of a UI test, but we can check the method exists
        assert hasattr(self.file_manager, 'open_device_file_with_editor')
        assert hasattr(self.file_manager, 'show_device_context_menu')
    
    @patch('src.gui.file_manager.QMessageBox')
    def test_open_file_with_editor_no_selection(self, mock_msgbox):
        """Test opening file with editor when no file is selected."""
        # Mock no selection
        with patch.object(self.file_manager, 'get_selected_device_files', return_value=[]):
            self.file_manager.open_device_file_with_editor()
            
        # Should show information message
        mock_msgbox.information.assert_called_once()
    
    @patch('src.gui.file_manager.QMessageBox')
    def test_open_directory_with_editor(self, mock_msgbox):
        """Test opening directory with editor (should fail)."""
        # Mock directory selection
        directory_info = FileInfo("test_dir", "/sdcard/test_dir", is_directory=True)
        with patch.object(self.file_manager, 'get_selected_device_files', return_value=[directory_info]):
            self.file_manager.open_device_file_with_editor()
            
        # Should show information message about directories
        mock_msgbox.information.assert_called_once()
    
    @patch('src.gui.file_manager.QMessageBox')
    def test_open_already_editing_file(self, mock_msgbox):
        """Test opening file that's already being edited."""
        # Mock file selection and active session
        with patch.object(self.file_manager, 'get_selected_device_files', return_value=[self.test_file_info]):
            with patch.object(self.file_manager.live_editor, 'is_session_active', return_value=True):
                self.file_manager.open_device_file_with_editor()
        
        # Should show information message about already editing
        mock_msgbox.information.assert_called_once()
    
    def test_start_live_edit_worker(self):
        """Test starting live edit worker."""
        # Mock successful worker creation
        with patch('src.gui.file_manager.LiveEditWorker') as mock_worker_class:
            mock_worker = Mock()
            mock_worker_class.return_value = mock_worker
            
            self.file_manager.start_live_edit_worker(self.test_file_info)
            
            # Worker should be created and started
            mock_worker_class.assert_called_once()
            mock_worker.start.assert_called_once()
    
    def test_live_edit_callbacks(self):
        """Test live edit callback methods."""
        # Test successful start callback
        self.file_manager.on_live_edit_worker_started("/sdcard/test.txt")
        # Should update progress label (we can't easily test this without UI)
        
        # Test failed start callback
        with patch('src.gui.file_manager.QMessageBox') as mock_msgbox:
            self.file_manager.on_live_edit_worker_failed("/sdcard/test.txt", "Test error")
            mock_msgbox.critical.assert_called_once()


class TestLiveEditWorker:
    """Test cases for LiveEditWorker."""
    
    def setup_method(self):
        """Set up test environment."""
        self.mock_file_ops = Mock(spec=FileOperations)
        self.mock_live_editor = Mock(spec=LiveEditorService)
        self.test_file_info = FileInfo(
            name="test.txt",
            path="/sdcard/test.txt",
            is_directory=False,
            size=100
        )
    
    def test_worker_creation(self):
        """Test creating a LiveEditWorker."""
        worker = LiveEditWorker(
            self.test_file_info,
            self.mock_file_ops,
            self.mock_live_editor
        )
        
        assert worker.file_info == self.test_file_info
        assert worker.file_ops == self.mock_file_ops
        assert worker.live_editor == self.mock_live_editor
    
    @patch('asyncio.new_event_loop')
    @patch('asyncio.set_event_loop')
    def test_worker_run_success(self, mock_set_loop, mock_new_loop):
        """Test successful worker run."""
        # Setup mocks
        mock_loop = Mock()
        mock_new_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = True
        
        # Create worker
        worker = LiveEditWorker(
            self.test_file_info,
            self.mock_file_ops,
            self.mock_live_editor
        )
        
        # Mock signals
        worker.session_started = Mock()
        worker.session_failed = Mock()
        
        # Run worker
        worker.run()
        
        # Check that success signal was emitted
        worker.session_started.emit.assert_called_once_with("/sdcard/test.txt")
        worker.session_failed.emit.assert_not_called()
    
    @patch('asyncio.new_event_loop')
    @patch('asyncio.set_event_loop')
    def test_worker_run_failure(self, mock_set_loop, mock_new_loop):
        """Test failed worker run."""
        # Setup mocks
        mock_loop = Mock()
        mock_new_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = False
        
        # Create worker
        worker = LiveEditWorker(
            self.test_file_info,
            self.mock_file_ops,
            self.mock_live_editor
        )
        
        # Mock signals
        worker.session_started = Mock()
        worker.session_failed = Mock()
        
        # Run worker
        worker.run()
        
        # Check that failure signal was emitted
        worker.session_failed.emit.assert_called_once_with("/sdcard/test.txt", "Failed to start editing session")
        worker.session_started.emit.assert_not_called()
    
    @patch('asyncio.new_event_loop')
    @patch('asyncio.set_event_loop')
    def test_worker_run_exception(self, mock_set_loop, mock_new_loop):
        """Test worker run with exception."""
        # Setup mocks to raise exception
        mock_loop = Mock()
        mock_new_loop.return_value = mock_loop
        mock_loop.run_until_complete.side_effect = Exception("Test exception")
        
        # Create worker
        worker = LiveEditWorker(
            self.test_file_info,
            self.mock_file_ops,
            self.mock_live_editor
        )
        
        # Mock signals
        worker.session_started = Mock()
        worker.session_failed = Mock()
        
        # Run worker
        worker.run()
        
        # Check that failure signal was emitted with exception
        worker.session_failed.emit.assert_called_once()
        args = worker.session_failed.emit.call_args[0]
        assert args[0] == "/sdcard/test.txt"
        assert "Test exception" in args[1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
