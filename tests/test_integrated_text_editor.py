"""
Test the integrated text editor functionality.

This test verifies the integrated text editor works correctly
with file operations and provides expected functionality.
"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from src.adb.file_operations import FileInfo, FileOperations
from src.gui.integrated_text_editor import IntegratedTextEditor, FileDownloadWorker, FileUploadWorker


class TestIntegratedTextEditor:
    """Test cases for the integrated text editor."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment."""
        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()
            
        self.file_info = FileInfo(
            name="test.txt",
            path="/sdcard/test.txt",
            is_directory=False,
            size=100
        )
        
        self.mock_file_ops = Mock(spec=FileOperations)
        self.test_content = "Hello World!\nThis is a test file.\nLine 3"
    
    def test_editor_initialization(self):
        """Test that the editor initializes correctly."""
        editor = IntegratedTextEditor(self.file_info, self.mock_file_ops)
        
        assert editor.file_info == self.file_info
        assert editor.file_ops == self.mock_file_ops
        assert editor.content_modified == False
        assert editor.original_content == ""
        assert editor.windowTitle() == "Edit: test.txt"
    
    def test_editor_ui_components(self):
        """Test that UI components are created correctly."""
        editor = IntegratedTextEditor(self.file_info, self.mock_file_ops)
        
        # Check that editor has the necessary components
        assert hasattr(editor, 'editor')
        assert hasattr(editor, 'status_label')
        assert hasattr(editor, 'cursor_label')
        assert hasattr(editor, 'auto_save_checkbox')
        assert hasattr(editor, 'auto_save_timer')
        
        # Check editor properties
        assert editor.editor is not None
        assert editor.auto_save_timer.interval() == 30000  # 30 seconds
    
    def test_content_modification_tracking(self):
        """Test content modification tracking."""
        editor = IntegratedTextEditor(self.file_info, self.mock_file_ops)
        
        # Simulate content loaded
        editor.original_content = self.test_content
        editor.editor.setPlainText(self.test_content)
        editor.content_modified = False
        
        # Modify content
        editor.editor.setPlainText(self.test_content + "\nNew line")
        editor.on_content_changed()
        
        assert editor.content_modified == True
        assert "test.txt *" in editor.windowTitle()
    
    def test_cursor_position_update(self):
        """Test cursor position updates."""
        editor = IntegratedTextEditor(self.file_info, self.mock_file_ops)
        editor.editor.setPlainText("Line 1\nLine 2\nLine 3")
        
        # Move cursor to line 2, column 3
        cursor = editor.editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Down)  # Move to line 2
        cursor.movePosition(cursor.MoveOperation.Right)  # Move right 3 positions
        cursor.movePosition(cursor.MoveOperation.Right)
        cursor.movePosition(cursor.MoveOperation.Right)
        editor.editor.setTextCursor(cursor)
        
        editor.update_cursor_position()
        assert "Line 2" in editor.cursor_label.text()
    
    def test_auto_save_toggle(self):
        """Test auto-save functionality toggle."""
        editor = IntegratedTextEditor(self.file_info, self.mock_file_ops)
        
        # Initially enabled
        assert editor.auto_save_timer.isActive()
        
        # Disable auto-save
        editor.auto_save_checkbox.setChecked(False)
        editor.toggle_auto_save(Qt.CheckState.Unchecked.value)
        assert not editor.auto_save_timer.isActive()
        
        # Re-enable auto-save
        editor.auto_save_checkbox.setChecked(True)
        editor.toggle_auto_save(Qt.CheckState.Checked.value)
        assert editor.auto_save_timer.isActive()


class TestFileDownloadWorker:
    """Test cases for file download worker."""
    
    def setup_method(self):
        """Set up test environment."""
        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()
            
        self.file_info = FileInfo(
            name="test.txt",
            path="/sdcard/test.txt",
            is_directory=False,
            size=100
        )
        
        self.mock_file_ops = Mock(spec=FileOperations)
        self.test_content = "Hello World!\nThis is a test file."
    
    @pytest.mark.asyncio
    async def test_successful_download(self):
        """Test successful file download."""
        # Mock successful pull_file
        self.mock_file_ops.pull_file = AsyncMock(return_value=True)
        
        worker = FileDownloadWorker(self.file_info, self.mock_file_ops)
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp, \
             patch('builtins.open', mock_open(read_data=self.test_content)) as mock_file, \
             patch('os.unlink'):
            
            mock_temp.return_value.__enter__.return_value.name = "/tmp/test_file"
            
            # Connect signal handler
            content_received = None
            def on_content_loaded(content):
                nonlocal content_received
                content_received = content
            
            worker.content_loaded.connect(on_content_loaded)
            
            # Run worker
            worker.run()
            
            # Verify
            assert content_received == self.test_content
            self.mock_file_ops.pull_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_failed_download(self):
        """Test failed file download."""
        # Mock failed pull_file
        self.mock_file_ops.pull_file = AsyncMock(return_value=False)
        
        worker = FileDownloadWorker(self.file_info, self.mock_file_ops)
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp, \
             patch('os.unlink'):
            
            mock_temp.return_value.__enter__.return_value.name = "/tmp/test_file"
            
            # Connect signal handler
            error_received = None
            def on_error(error):
                nonlocal error_received
                error_received = error
            
            worker.error_occurred.connect(on_error)
            
            # Run worker
            worker.run()
            
            # Verify
            assert error_received == "Failed to download file from device"
            self.mock_file_ops.pull_file.assert_called_once()


class TestFileUploadWorker:
    """Test cases for file upload worker."""
    
    def setup_method(self):
        """Set up test environment."""
        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()
            
        self.mock_file_ops = Mock(spec=FileOperations)
        self.test_content = "Hello World!\nThis is a test file."
        self.device_path = "/sdcard/test.txt"
    
    @pytest.mark.asyncio
    async def test_successful_upload(self):
        """Test successful file upload."""
        # Mock successful push_file
        self.mock_file_ops.push_file = AsyncMock(return_value=True)
        
        worker = FileUploadWorker(self.test_content, self.device_path, self.mock_file_ops)
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp, \
             patch('os.unlink'):
            
            mock_temp.return_value.__enter__.return_value.name = "/tmp/test_upload"
            
            # Connect signal handler
            upload_result = None
            def on_upload_completed(success, message):
                nonlocal upload_result
                upload_result = (success, message)
            
            worker.upload_completed.connect(on_upload_completed)
            
            # Run worker
            worker.run()
            
            # Verify
            assert upload_result == (True, "File uploaded successfully")
            self.mock_file_ops.push_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_failed_upload(self):
        """Test failed file upload."""
        # Mock failed push_file
        self.mock_file_ops.push_file = AsyncMock(return_value=False)
        
        worker = FileUploadWorker(self.test_content, self.device_path, self.mock_file_ops)
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp, \
             patch('os.unlink'):
            
            mock_temp.return_value.__enter__.return_value.name = "/tmp/test_upload"
            
            # Connect signal handler
            upload_result = None
            def on_upload_completed(success, message):
                nonlocal upload_result
                upload_result = (success, message)
            
            worker.upload_completed.connect(on_upload_completed)
            
            # Run worker
            worker.run()
            
            # Verify
            assert upload_result == (False, "Failed to upload file to device")
            self.mock_file_ops.push_file.assert_called_once()


# Helper function for testing
def mock_open(read_data=''):
    """Create a mock for open() function."""
    from unittest.mock import mock_open as mock_open_builtin
    return mock_open_builtin(read_data=read_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
