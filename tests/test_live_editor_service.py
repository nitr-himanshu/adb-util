"""
Test Live Editor Service

Comprehensive tests for live editing functionality and file monitoring.
"""

import pytest
import tempfile
import asyncio
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from services.live_editor import LiveEditor, LiveEditSession


@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace for live editing."""
    workspace = tmp_path / "live_editor_workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing."""
    mock_ops = Mock()
    mock_ops.download_file = AsyncMock(return_value=True)
    mock_ops.upload_file = AsyncMock(return_value=True)
    mock_ops.file_exists = AsyncMock(return_value=True)
    mock_ops.get_file_info = AsyncMock(return_value={
        "name": "test.txt",
        "size": 1024,
        "permissions": "rw-r--r--",
        "modified": "2024-01-01 10:00:00"
    })
    return mock_ops


@pytest.fixture
def live_editor(temp_workspace, mock_file_operations):
    """Create LiveEditor instance."""
    return LiveEditor(
        workspace_dir=str(temp_workspace),
        file_operations=mock_file_operations
    )


@pytest.fixture
def sample_device_file():
    """Sample device file path."""
    return "/sdcard/Documents/test_file.txt"


@pytest.fixture
def sample_editor_command():
    """Sample editor command."""
    return "notepad.exe" if os.name == 'nt' else "nano"


class TestLiveEditSession:
    """Test cases for LiveEditSession."""

    def test_session_initialization(self, temp_workspace, mock_file_operations):
        """Test live edit session initialization."""
        device_path = "/sdcard/test.txt"
        local_path = temp_workspace / "test.txt"
        editor_cmd = "notepad"
        
        session = LiveEditSession(
            device_file_path=device_path,
            local_temp_path=local_path,
            editor_command=editor_cmd,
            file_ops=mock_file_operations
        )
        
        assert session.device_file_path == device_path
        assert session.local_temp_path == local_path
        assert session.editor_command == editor_cmd
        assert session.is_active is False
        assert session.process is None

    def test_session_start_editor_success(self, temp_workspace, mock_file_operations):
        """Test starting editor process successfully."""
        local_path = temp_workspace / "test.txt"
        local_path.write_text("test content")
        
        session = LiveEditSession(
            "/sdcard/test.txt",
            local_path,
            "echo",  # Use simple command for testing
            mock_file_operations
        )
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process
            
            result = session.start_editor()
            
            assert result is True
            assert session.process is not None
            assert session.editor_pid == 12345
            assert session.is_active is True

    def test_session_start_editor_failure(self, temp_workspace, mock_file_operations):
        """Test handling editor start failure."""
        local_path = temp_workspace / "test.txt"
        local_path.write_text("test content")
        
        session = LiveEditSession(
            "/sdcard/test.txt",
            local_path,
            "nonexistent_editor",
            mock_file_operations
        )
        
        result = session.start_editor()
        assert result is False
        assert session.is_active is False

    def test_session_is_editor_running(self, temp_workspace, mock_file_operations):
        """Test checking if editor is still running."""
        session = LiveEditSession(
            "/sdcard/test.txt",
            temp_workspace / "test.txt",
            "notepad",
            mock_file_operations
        )
        
        # No process running
        assert session.is_editor_running() is False
        
        # Mock running process
        session.process = Mock()
        session.process.poll.return_value = None  # Still running
        assert session.is_editor_running() is True
        
        # Process finished
        session.process.poll.return_value = 0  # Finished
        assert session.is_editor_running() is False

    def test_session_has_file_changed(self, temp_workspace, mock_file_operations):
        """Test detecting file changes."""
        local_path = temp_workspace / "test.txt"
        local_path.write_text("initial content")
        
        session = LiveEditSession(
            "/sdcard/test.txt",
            local_path,
            "notepad",
            mock_file_operations
        )
        
        # Initial state
        session.last_modified = local_path.stat().st_mtime
        assert session.has_file_changed() is False
        
        # Modify file
        import time
        time.sleep(0.1)  # Ensure timestamp difference
        local_path.write_text("modified content")
        assert session.has_file_changed() is True

    @pytest.mark.asyncio
    async def test_session_upload_changes(self, temp_workspace, mock_file_operations):
        """Test uploading file changes to device."""
        local_path = temp_workspace / "test.txt"
        local_path.write_text("modified content")
        
        session = LiveEditSession(
            "/sdcard/test.txt",
            local_path,
            "notepad",
            mock_file_operations
        )
        
        result = await session.upload_changes()
        
        assert result is True
        mock_file_operations.upload_file.assert_called_once_with(
            str(local_path), 
            "/sdcard/test.txt"
        )

    def test_session_cleanup(self, temp_workspace, mock_file_operations):
        """Test session cleanup."""
        local_path = temp_workspace / "test.txt"
        local_path.write_text("test content")
        
        session = LiveEditSession(
            "/sdcard/test.txt",
            local_path,
            "notepad",
            mock_file_operations
        )
        
        # Mock running process
        session.process = Mock()
        session.is_active = True
        
        session.cleanup()
        
        # Should terminate process and clean up
        session.process.terminate.assert_called_once()
        assert session.is_active is False


class TestLiveEditor:
    """Test cases for LiveEditor."""

    def test_init_creates_workspace(self, temp_workspace, mock_file_operations):
        """Test initialization creates workspace directory."""
        workspace_path = temp_workspace / "new_workspace"
        
        editor = LiveEditor(
            workspace_dir=str(workspace_path),
            file_operations=mock_file_operations
        )
        
        assert workspace_path.exists()
        assert editor.workspace_dir == Path(workspace_path)

    @pytest.mark.asyncio
    async def test_start_editing_new_session(self, live_editor, sample_device_file):
        """Test starting new editing session."""
        editor_cmd = "notepad" if os.name == 'nt' else "nano"
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process
            
            session_id = await live_editor.start_editing(
                sample_device_file,
                editor_cmd
            )
            
            assert session_id is not None
            assert session_id in live_editor.active_sessions
            
            # Verify file was downloaded
            live_editor.file_operations.download_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_editing_existing_session(self, live_editor, sample_device_file):
        """Test starting editing session for file already being edited."""
        # Create existing session
        session_id1 = "existing_session"
        mock_session = Mock()
        mock_session.is_active = True
        mock_session.device_file_path = sample_device_file
        live_editor.active_sessions[session_id1] = mock_session
        
        session_id2 = await live_editor.start_editing(
            sample_device_file,
            "notepad"
        )
        
        # Should return existing session
        assert session_id2 == session_id1

    def test_stop_editing_existing_session(self, live_editor):
        """Test stopping existing editing session."""
        session_id = "test_session"
        mock_session = Mock()
        live_editor.active_sessions[session_id] = mock_session
        
        result = live_editor.stop_editing(session_id)
        
        assert result is True
        mock_session.cleanup.assert_called_once()
        assert session_id not in live_editor.active_sessions

    def test_stop_editing_nonexistent_session(self, live_editor):
        """Test stopping non-existent editing session."""
        result = live_editor.stop_editing("nonexistent_session")
        assert result is False

    def test_get_active_sessions(self, live_editor):
        """Test getting list of active sessions."""
        # Add mock sessions
        session1 = Mock()
        session1.device_file_path = "/sdcard/file1.txt"
        session1.is_active = True
        
        session2 = Mock()
        session2.device_file_path = "/sdcard/file2.txt"
        session2.is_active = True
        
        live_editor.active_sessions = {
            "session1": session1,
            "session2": session2
        }
        
        sessions = live_editor.get_active_sessions()
        assert len(sessions) == 2

    def test_is_file_being_edited(self, live_editor, sample_device_file):
        """Test checking if file is currently being edited."""
        # File not being edited
        assert live_editor.is_file_being_edited(sample_device_file) is False
        
        # Add session for file
        mock_session = Mock()
        mock_session.device_file_path = sample_device_file
        mock_session.is_active = True
        live_editor.active_sessions["session1"] = mock_session
        
        assert live_editor.is_file_being_edited(sample_device_file) is True

    @pytest.mark.asyncio
    async def test_monitor_sessions_loop(self, live_editor):
        """Test session monitoring loop."""
        # Create mock session
        session_id = "test_session"
        mock_session = Mock()
        mock_session.is_editor_running.return_value = False  # Editor closed
        mock_session.has_file_changed.return_value = True  # File changed
        mock_session.upload_changes = AsyncMock(return_value=True)
        mock_session.is_active = True
        mock_session.device_file_path = "/sdcard/test.txt"
        
        live_editor.active_sessions[session_id] = mock_session
        
        # Run one iteration of monitoring
        await live_editor._monitor_single_session(session_id)
        
        # Should upload changes and clean up
        mock_session.upload_changes.assert_called_once()
        mock_session.cleanup.assert_called_once()

    def test_get_temp_file_path(self, live_editor, sample_device_file):
        """Test generating temporary file path."""
        temp_path = live_editor._get_temp_file_path(sample_device_file)
        
        assert temp_path.parent == live_editor.workspace_dir
        assert temp_path.name == "test_file.txt"
        assert temp_path.exists() is False

    def test_get_available_editors(self, live_editor):
        """Test getting list of available editors."""
        with patch('shutil.which') as mock_which:
            mock_which.side_effect = lambda cmd: cmd if cmd in ['notepad', 'code'] else None
            
            editors = live_editor.get_available_editors()
            
            # Should find available editors
            assert len(editors) > 0

    def test_validate_editor_command_valid(self, live_editor):
        """Test validating valid editor command."""
        with patch('shutil.which', return_value='/usr/bin/nano'):
            result = live_editor.validate_editor_command('nano')
            assert result is True

    def test_validate_editor_command_invalid(self, live_editor):
        """Test validating invalid editor command."""
        with patch('shutil.which', return_value=None):
            result = live_editor.validate_editor_command('nonexistent_editor')
            assert result is False

    @pytest.mark.asyncio
    async def test_force_upload_all_changes(self, live_editor):
        """Test force uploading all pending changes."""
        # Create sessions with changes
        session1 = Mock()
        session1.has_file_changed.return_value = True
        session1.upload_changes = AsyncMock(return_value=True)
        session1.is_active = True
        
        session2 = Mock()
        session2.has_file_changed.return_value = False
        session2.upload_changes = AsyncMock(return_value=True)
        session2.is_active = True
        
        live_editor.active_sessions = {
            "session1": session1,
            "session2": session2
        }
        
        uploaded_count = await live_editor.force_upload_all_changes()
        
        assert uploaded_count == 1  # Only session1 had changes
        session1.upload_changes.assert_called_once()
        session2.upload_changes.assert_not_called()

    def test_cleanup_all_sessions(self, live_editor):
        """Test cleaning up all active sessions."""
        # Create mock sessions
        session1 = Mock()
        session2 = Mock()
        
        live_editor.active_sessions = {
            "session1": session1,
            "session2": session2
        }
        
        live_editor.cleanup_all_sessions()
        
        # Should clean up all sessions
        session1.cleanup.assert_called_once()
        session2.cleanup.assert_called_once()
        assert len(live_editor.active_sessions) == 0


@pytest.mark.integration
class TestLiveEditorIntegration:
    """Integration tests for LiveEditor."""

    @pytest.mark.asyncio
    async def test_complete_edit_workflow(self, temp_workspace, mock_file_operations):
        """Test complete editing workflow from start to finish."""
        editor = LiveEditor(
            workspace_dir=str(temp_workspace),
            file_operations=mock_file_operations
        )
        
        device_file = "/sdcard/test_document.txt"
        editor_cmd = "echo"  # Simple command for testing
        
        # Start editing
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.pid = 12345
            mock_process.poll.return_value = 0  # Process finished
            mock_popen.return_value = mock_process
            
            session_id = await editor.start_editing(device_file, editor_cmd)
            assert session_id is not None
            
            # Verify session is active
            assert editor.is_file_being_edited(device_file)
            
            # Simulate file change and editor closing
            session = editor.active_sessions[session_id]
            session.has_file_changed = Mock(return_value=True)
            session.is_editor_running = Mock(return_value=False)
            
            # Monitor should detect changes and upload
            await editor._monitor_single_session(session_id)
            
            # Verify upload was attempted
            mock_file_operations.upload_file.assert_called()

    def test_multiple_concurrent_sessions(self, temp_workspace, mock_file_operations):
        """Test handling multiple concurrent editing sessions."""
        editor = LiveEditor(
            workspace_dir=str(temp_workspace),
            file_operations=mock_file_operations
        )
        
        files = ["/sdcard/file1.txt", "/sdcard/file2.txt", "/sdcard/file3.txt"]
        sessions = []
        
        for file_path in files:
            session_id = f"session_{len(sessions)}"
            mock_session = Mock()
            mock_session.device_file_path = file_path
            mock_session.is_active = True
            
            editor.active_sessions[session_id] = mock_session
            sessions.append(session_id)
        
        # Verify all sessions are tracked
        active_sessions = editor.get_active_sessions()
        assert len(active_sessions) == 3
        
        # Stop one session
        editor.stop_editing(sessions[0])
        assert len(editor.active_sessions) == 2
        
        # Cleanup all
        editor.cleanup_all_sessions()
        assert len(editor.active_sessions) == 0

    def test_error_recovery(self, temp_workspace, mock_file_operations):
        """Test error recovery in various failure scenarios."""
        editor = LiveEditor(
            workspace_dir=str(temp_workspace),
            file_operations=mock_file_operations
        )
        
        # Test download failure
        mock_file_operations.download_file.side_effect = Exception("Download failed")
        
        async def test_download_failure():
            session_id = await editor.start_editing("/sdcard/test.txt", "notepad")
            assert session_id is None  # Should handle failure gracefully
        
        # Test upload failure
        mock_file_operations.upload_file.side_effect = Exception("Upload failed")
        
        session = LiveEditSession(
            "/sdcard/test.txt",
            temp_workspace / "test.txt",
            "notepad",
            mock_file_operations
        )
        
        async def test_upload_failure():
            result = await session.upload_changes()
            assert result is False  # Should handle failure gracefully
