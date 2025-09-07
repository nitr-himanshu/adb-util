"""
Live Editor Service

Manages live editing of device files in external editors.
When a file is opened with an external editor, it:
1. Downloads the file to a temporary location
2. Opens it with the specified editor
3. Monitors the file for changes
4. Automatically uploads changes back to the device when editor closes
"""

import os
import os
import sys
import tempfile
import subprocess
import asyncio
import shutil
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime
import time

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QFileSystemWatcher
from PyQt6.QtWidgets import QMessageBox, QInputDialog, QApplication

from src.adb.file_operations import FileOperations, FileInfo
from src.utils.logger import get_logger
from src.services.config_manager import ConfigManager


class LiveEditSession:
    """Represents a live editing session for a device file."""
    
    def __init__(self, device_file_path: str, local_temp_path: Path, 
                 editor_command: str, file_ops: FileOperations):
        self.device_file_path = device_file_path
        self.local_temp_path = local_temp_path
        self.editor_command = editor_command
        self.file_ops = file_ops
        self.process: Optional[subprocess.Popen] = None
        self.editor_pid: Optional[int] = None
        self.last_modified: Optional[float] = None
        self.is_active = False
        self.upload_pending = False
        
    def start_editor(self) -> bool:
        """Start the external editor process and track its PID."""
        try:
            editor_cmd = self.editor_command
            is_vscode = False
            if 'code' in editor_cmd.lower():
                is_vscode = True
            if sys.platform == "win32":
                if is_vscode:
                    command = f'{editor_cmd} --new-window "{self.local_temp_path}"'
                elif self.editor_command.startswith('"') and self.editor_command.endswith('"'):
                    command = f'{self.editor_command} "{self.local_temp_path}"'
                elif ' ' in self.editor_command and not self.editor_command.startswith('"'):
                    command = f'"{self.editor_command}" "{self.local_temp_path}"'
                else:
                    command = f'{self.editor_command} "{self.local_temp_path}"'
                self.process = subprocess.Popen(command, shell=True)
            else:
                if is_vscode:
                    self.process = subprocess.Popen([editor_cmd, '--new-window', str(self.local_temp_path)])
                else:
                    self.process = subprocess.Popen([editor_cmd, str(self.local_temp_path)])
            self.is_active = True
            self.update_last_modified()
            if self.process:
                self.editor_pid = self.process.pid
            return True
        except Exception as e:
            self.logger.error(f"Failed to start editor '{self.editor_command}': {e}")
            return False
    
    def is_editor_running(self) -> bool:
        """Check if the editor process is still running by PID."""
        if not self.process or not self.editor_pid:
            return False
        # Check process status
        poll_result = self.process.poll()
        if poll_result is None:
            return True
        # Double-check by PID (in case of shell wrappers)
        try:
            import psutil
            return psutil.pid_exists(self.editor_pid)
        except ImportError:
            # Fallback: rely on process.poll()
            return False
    
    def update_last_modified(self):
        """Update the last modified timestamp."""
        try:
            if self.local_temp_path.exists():
                self.last_modified = self.local_temp_path.stat().st_mtime
        except Exception:
            self.last_modified = None
    
    def has_changes(self) -> bool:
        """Check if the file has been modified since last check."""
        try:
            if not self.local_temp_path.exists():
                return False
            
            current_modified = self.local_temp_path.stat().st_mtime
            if self.last_modified is None:
                return True
            
            return current_modified > self.last_modified
        except Exception:
            return False
    
    def cleanup(self):
        """Clean up temporary files and processes. (Do not delete temp file)"""
        try:
            # Terminate process if still running
            if self.process and self.is_editor_running():
                self.process.terminate()
                time.sleep(0.5)
                if self.is_editor_running():
                    self.process.kill()
            # Do NOT delete the temp file; keep it persisted in %temp%
        except Exception:
            pass  # Ignore cleanup errors


class LiveEditorService(QObject):
    """Service for managing live editing sessions."""
    
    # Signals
    session_started = pyqtSignal(str)  # device_file_path
    session_ended = pyqtSignal(str, bool)  # device_file_path, success
    file_uploaded = pyqtSignal(str)  # device_file_path
    error_occurred = pyqtSignal(str, str)  # device_file_path, error_message
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.config = ConfigManager()
        self.sessions: Dict[str, LiveEditSession] = {}
        self.temp_dir = Path(tempfile.gettempdir()) / "adb-util-live-edit"
        self.temp_dir.mkdir(exist_ok=True)
        
        # File system watcher for monitoring changes
        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.fileChanged.connect(self.on_file_changed)
        
        # Timer for periodic checks
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_sessions)
        self.check_timer.start(2000)  # Check every 2 seconds
        
        # Default editors
        self.default_editors = self.get_default_editors()
    
    def get_default_editors(self) -> Dict[str, str]:
        """Get default editors for different platforms."""
        if sys.platform == "win32":
            # Try to find VS Code in common locations
            vscode_paths = [
                "code",  # Try PATH first
                r"C:\Program Files\Microsoft VS Code\bin\code.cmd",
                r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd".format(os.environ.get('USERNAME', '')),
                r"C:\Program Files (x86)\Microsoft VS Code\bin\code.cmd"
            ]
            
            vscode_cmd = "code"
            for path in vscode_paths:
                if path == "code":
                    # Check if code is in PATH
                    if self.is_command_in_path("code"):
                        vscode_cmd = "code"
                        break
                else:
                    # Check if file exists
                    if os.path.exists(path):
                        vscode_cmd = f'"{path}"'
                        break
            
            return {
                "vscode": vscode_cmd,
                "notepad++": "notepad++",
                "notepad": "notepad",
                "wordpad": "write"
            }
        elif sys.platform == "darwin":  # macOS
            return {
                "vscode": "code",
                "textedit": "open -a TextEdit",
                "nano": "nano",
                "vim": "vim"
            }
        else:  # Linux
            return {
                "vscode": "code",
                "gedit": "gedit",
                "nano": "nano",
                "vim": "vim"
            }
    
    def get_available_editors(self) -> List[Dict[str, str]]:
        """Get list of available editors on the system."""
        available = []
        
        for name, command in self.default_editors.items():
            if self.is_editor_available(command):
                available.append({"name": name.title(), "command": command})
        
        # Add custom editors from config
        custom_editors = self.config.get_setting("custom_editors", [])
        for editor in custom_editors:
            if self.is_editor_available(editor.get("command", "")):
                available.append(editor)
        
        return available
    
    def is_command_in_path(self, command: str) -> bool:
        """Check if a command is available in PATH."""
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["where", command], 
                    capture_output=True, 
                    text=True,
                    shell=True
                )
                return result.returncode == 0
            else:
                result = subprocess.run(
                    ["which", command], 
                    capture_output=True, 
                    text=True
                )
                return result.returncode == 0
        except Exception:
            return False
    
    def is_editor_available(self, command: str) -> bool:
        """Check if an editor command is available on the system."""
        try:
            # Handle quoted commands (remove quotes for testing)
            test_command = command.strip('"\'')
            
            # If it's a full path, check if file exists
            if os.path.isabs(test_command):
                return os.path.exists(test_command)
            
            # Extract the main command (first word)
            main_command = test_command.split()[0]
            
            return self.is_command_in_path(main_command)
        except Exception:
            return False
    
    async def start_live_edit_session(self, device_file: FileInfo, 
                                    file_ops: FileOperations, 
                                    editor_command: str = None) -> bool:
        """Start a live editing session for a device file."""
        try:
            # Check if session already exists
            if device_file.path in self.sessions:
                self.logger.warning(f"Live edit session already exists for {device_file.path}")
                return False
            
            # If no editor specified, use default or first available
            if not editor_command:
                editor_command = self.get_default_editor_command()
                if not editor_command:
                    self.logger.error("No editor available for live editing")
                    return False
            
            # Create temporary file
            temp_file = self.create_temp_file(device_file.name)
            if not temp_file:
                self.error_occurred.emit(device_file.path, "Failed to create temporary file")
                return False
            
            # Download file from device
            self.logger.info(f"Downloading {device_file.path} for live editing")
            success = await file_ops.pull_file(device_file.path, temp_file)
            if not success:
                temp_file.unlink(missing_ok=True)
                self.error_occurred.emit(device_file.path, "Failed to download file from device")
                return False
            
            # Create live edit session
            session = LiveEditSession(device_file.path, temp_file, editor_command, file_ops)
            
            # Start the editor
            if not session.start_editor():
                session.cleanup()
                self.error_occurred.emit(device_file.path, f"Failed to start editor: {editor_command}")
                return False
            
            # Store session and start monitoring
            self.sessions[device_file.path] = session
            self.file_watcher.addPath(str(temp_file))
            
            self.logger.info(f"Started live edit session for {device_file.path}")
            self.session_started.emit(device_file.path)
            
            # Simple approach: Just open the editor and let user manually end session
            # The session will stay active until manually stopped
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting live edit session: {e}")
            self.error_occurred.emit(device_file.path, f"Error: {str(e)}")
            return False
    
    def get_default_editor_command(self) -> Optional[str]:
        """Get the default editor command to use."""
        # Check if user has set a default editor
        default_editor = self.config.get_default_editor()
        if default_editor and self.is_editor_available(default_editor):
            return default_editor
        
        # Otherwise, find the first available editor
        available_editors = self.get_available_editors()
        if available_editors:
            return available_editors[0]["command"]
        
        return None
    
    def prompt_for_editor(self) -> Optional[str]:
        """Prompt user to select an editor."""
        available_editors = self.get_available_editors()
        if not available_editors:
            QMessageBox.warning(
                None, 
                "No Editors Found", 
                "No supported editors found on your system.\n"
                "Please install VS Code, Notepad++, or another text editor."
            )
            return None
        
        # Create list of editor names
        editor_names = [editor["name"] for editor in available_editors]
        
        # Add option for custom command
        editor_names.append("Custom Command...")
        
        # Show selection dialog
        from PyQt6.QtWidgets import QInputDialog
        choice, ok = QInputDialog.getItem(
            None,
            "Select Editor",
            "Choose an editor to open the file:",
            editor_names,
            0,
            False
        )
        
        if not ok:
            return None
        
        if choice == "Custom Command...":
            # Prompt for custom command
            command, ok = QInputDialog.getText(
                None,
                "Custom Editor Command",
                "Enter the command to open files:"
            )
            return command if ok else None
        else:
            # Find selected editor command
            for editor in available_editors:
                if editor["name"] == choice:
                    return editor["command"]
        
        return None
    
    def create_temp_file(self, filename: str) -> Optional[Path]:
        """Create a temporary file for editing."""
        try:
            # Create unique filename to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_filename = f"{timestamp}_{filename}"
            temp_path = self.temp_dir / temp_filename
            
            # Create empty file
            temp_path.touch()
            return temp_path
            
        except Exception as e:
            self.logger.error(f"Error creating temporary file: {e}")
            return None
    
    def on_file_changed(self, file_path: str):
        """Handle file change notifications."""
        try:
            # Find the session for this file
            session = None
            for device_path, sess in self.sessions.items():
                if str(sess.local_temp_path) == file_path:
                    session = sess
                    break
            
            if not session:
                return
            
            # Mark for upload
            session.upload_pending = True
            self.logger.info(f"File change detected for {session.device_file_path}")
            
        except Exception as e:
            self.logger.error(f"Error handling file change: {e}")
    
    def check_sessions(self):
        """Periodically check active sessions - DISABLED for VS Code live editing."""
        # Disabled automatic session checking since VS Code monitoring is handled separately
        pass
    
    async def upload_file_changes(self, device_path: str):
        """Upload file changes to device."""
        try:
            session = self.sessions.get(device_path)
            if not session or not session.local_temp_path.exists():
                return
            
            # Upload the file
            success = await session.file_ops.push_file(
                session.local_temp_path, 
                session.device_file_path
            )
            
            if success:
                session.upload_pending = False
                session.update_last_modified()
                self.file_uploaded.emit(device_path)
                self.logger.info(f"Uploaded changes for {device_path}")
            else:
                self.logger.error(f"Failed to upload changes for {device_path}")
                
        except Exception as e:
            self.logger.error(f"Error uploading file changes: {e}")
    
    async def upload_and_finish_session(self, device_path: str):
        """Upload final changes and finish the session."""
        try:
            session = self.sessions.get(device_path)
            if not session:
                return
            
            success = True
            if session.local_temp_path.exists():
                # Upload the file one final time
                success = await session.file_ops.push_file(
                    session.local_temp_path, 
                    session.device_file_path
                )
                
                if success:
                    self.file_uploaded.emit(device_path)
                    self.logger.info(f"Final upload completed for {device_path}")
            
            self.finish_session(device_path, success)
            
        except Exception as e:
            self.logger.error(f"Error in upload and finish: {e}")
            self.finish_session(device_path, False)
    
    def finish_session(self, device_path: str, success: bool):
        """Finish and clean up a live edit session."""
        try:
            session = self.sessions.get(device_path)
            if session:
                # Remove from file watcher
                if session.local_temp_path.exists():
                    self.file_watcher.removePath(str(session.local_temp_path))
                
                # Clean up session
                session.cleanup()
                
                # Remove from active sessions
                del self.sessions[device_path]
                
                self.session_ended.emit(device_path, success)
                self.logger.info(f"Live edit session ended for {device_path} (success: {success})")
        
        except Exception as e:
            self.logger.error(f"Error finishing session: {e}")
    
    def stop_session(self, device_path: str):
        """Manually stop a live edit session."""
        if device_path in self.sessions:
            import asyncio
            try:
                # Run upload and finish in the current thread
                loop = None
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    pass
                if loop and loop.is_running():
                    loop.create_task(self.upload_and_finish_session(device_path))
                else:
                    asyncio.run(self.upload_and_finish_session(device_path))
            except Exception as e:
                self.logger.error(f"Error stopping session: {e}")
                # Force cleanup even if upload fails
                self.finish_session(device_path, False)
    
    def manual_upload_session(self, device_path: str):
        """Manually upload changes for an active session without ending it."""
        session = self.sessions.get(device_path)
        if session and session.local_temp_path.exists():
            import asyncio
            try:
                loop = None
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    pass
                if loop and loop.is_running():
                    loop.create_task(self.upload_file_changes(device_path))
                else:
                    asyncio.run(self.upload_file_changes(device_path))
            except Exception as e:
                self.logger.error(f"Error manually uploading session: {e}")
    
    def stop_all_sessions(self):
        """Stop all active live edit sessions."""
        device_paths = list(self.sessions.keys())
        for device_path in device_paths:
            self.stop_session(device_path)
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session device paths."""
        return list(self.sessions.keys())
    
    def is_session_active(self, device_path: str) -> bool:
        """Check if a session is active for the given device path."""
        return device_path in self.sessions
    
    def cleanup(self):
        """Clean up the service."""
        try:
            self.check_timer.stop()
            self.stop_all_sessions()
            
            # Clean up temp directory
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
