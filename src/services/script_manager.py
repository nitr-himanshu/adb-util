"""
Script Manager Service

Manages host and device script execution with async output capture.
Supports Windows .bat files and Linux .sh files for both host and device operations.
"""

import asyncio
import json
import os
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from adb.command_runner import ADBCommandRunner
from utils.logger import get_logger


class ScriptType(Enum):
    """Script type enumeration."""
    HOST_WINDOWS = "host_windows"
    HOST_LINUX = "host_linux"
    DEVICE = "device"


class ScriptStatus(Enum):
    """Script execution status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Script:
    """Script definition data class."""
    id: str
    name: str
    script_type: ScriptType
    script_path: str
    description: str = ""
    created_at: str = ""
    last_run: str = ""
    run_count: int = 0
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class ScriptExecution:
    """Script execution result data class."""
    script_id: str
    execution_id: str
    status: ScriptStatus
    start_time: str
    end_time: str = ""
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    device_id: str = ""  # For device scripts
    
    def __post_init__(self):
        if not self.start_time:
            self.start_time = datetime.now().isoformat()


class ScriptExecutionWorker(QThread):
    """Worker thread for script execution."""
    
    output_received = pyqtSignal(str, str)  # execution_id, output
    error_received = pyqtSignal(str, str)   # execution_id, error
    execution_finished = pyqtSignal(str, int)  # execution_id, exit_code
    execution_started = pyqtSignal(str)     # execution_id
    
    def __init__(self, script: Script, execution: ScriptExecution, device_id: str = None):
        super().__init__()
        self.script = script
        self.execution = execution
        self.device_id = device_id
        self.logger = get_logger(__name__)
        self.process = None
        self.cancelled = False
        
    def run(self):
        """Execute the script."""
        try:
            self.execution_started.emit(self.execution.execution_id)
            
            if self.script.script_type == ScriptType.DEVICE:
                self._execute_device_script()
            else:
                self._execute_host_script()
                
        except Exception as e:
            self.logger.error(f"Script execution error: {e}")
            self.error_received.emit(self.execution.execution_id, str(e))
            self.execution_finished.emit(self.execution.execution_id, -1)
    
    def _execute_host_script(self):
        """Execute host script (Windows .bat or Linux .sh)."""
        script_path = Path(self.script.script_path)
        
        if not script_path.exists():
            raise FileNotFoundError(f"Script file not found: {script_path}")
        
        # Determine command based on script type
        if self.script.script_type == ScriptType.HOST_WINDOWS:
            if os.name == 'nt':
                cmd = [str(script_path)]
            else:
                # Running Windows script on non-Windows (should not happen in normal use)
                raise RuntimeError("Cannot execute Windows batch file on non-Windows system")
        else:  # HOST_LINUX
            if os.name == 'nt':
                # Running Linux script on Windows (use WSL if available, or bash)
                cmd = ['bash', str(script_path)]
            else:
                cmd = ['bash', str(script_path)]
        
        # Execute the script
        self._run_process(cmd, cwd=script_path.parent)
    
    def _execute_device_script(self):
        """Execute device script by pushing to device and running."""
        if not self.device_id:
            raise ValueError("Device ID required for device script execution")
        
        script_path = Path(self.script.script_path)
        if not script_path.exists():
            raise FileNotFoundError(f"Script file not found: {script_path}")
        
        # Generate temporary device path
        device_script_path = f"/sdcard/adb_util_scripts/{script_path.name}"
        
        try:
            # Create ADB command runner
            adb_runner = ADBCommandRunner(self.device_id)
            
            # Create directory on device
            mkdir_result = adb_runner.run_command(['shell', 'mkdir', '-p', '/sdcard/adb_util_scripts'])
            if not mkdir_result.success:
                self.output_received.emit(self.execution.execution_id, 
                                        f"Warning: Could not create directory: {mkdir_result.stderr}")
            
            # Push script to device
            push_result = adb_runner.run_command(['push', str(script_path), device_script_path])
            if not push_result.success:
                raise RuntimeError(f"Failed to push script to device: {push_result.stderr}")
            
            self.output_received.emit(self.execution.execution_id, 
                                    f"Script pushed to device: {device_script_path}\n")
            
            # Make script executable
            chmod_result = adb_runner.run_command(['shell', 'chmod', '+x', device_script_path])
            if not chmod_result.success:
                self.output_received.emit(self.execution.execution_id, 
                                        f"Warning: Could not make script executable: {chmod_result.stderr}")
            
            # Execute script on device
            exec_cmd = ['shell', 'source', device_script_path]
            self._run_adb_process(adb_runner, exec_cmd)
            
            # Cleanup: remove script from device
            cleanup_result = adb_runner.run_command(['shell', 'rm', device_script_path])
            if not cleanup_result.success:
                self.output_received.emit(self.execution.execution_id, 
                                        f"Warning: Could not cleanup script: {cleanup_result.stderr}")
                
        except Exception as e:
            raise RuntimeError(f"Device script execution failed: {e}")
    
    def _run_process(self, cmd: List[str], cwd: Optional[Path] = None):
        """Run a process and capture output."""
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output in real-time
            while True:
                if self.cancelled:
                    self.process.terminate()
                    break
                
                output = self.process.stdout.readline()
                if output:
                    self.output_received.emit(self.execution.execution_id, output.rstrip())
                
                error = self.process.stderr.readline()
                if error:
                    self.error_received.emit(self.execution.execution_id, error.rstrip())
                
                # Check if process is done
                if self.process.poll() is not None:
                    # Read any remaining output
                    remaining_out, remaining_err = self.process.communicate()
                    if remaining_out:
                        self.output_received.emit(self.execution.execution_id, remaining_out.rstrip())
                    if remaining_err:
                        self.error_received.emit(self.execution.execution_id, remaining_err.rstrip())
                    break
            
            exit_code = self.process.returncode
            self.execution_finished.emit(self.execution.execution_id, exit_code)
            
        except Exception as e:
            self.logger.error(f"Process execution error: {e}")
            self.error_received.emit(self.execution.execution_id, str(e))
            self.execution_finished.emit(self.execution.execution_id, -1)
    
    def _run_adb_process(self, adb_runner: ADBCommandRunner, cmd: List[str]):
        """Run ADB process and capture output."""
        try:
            # For ADB commands, we'll use the command runner's execute method
            # and capture output differently
            result = adb_runner.run_command(cmd)
            
            if result.stdout:
                self.output_received.emit(self.execution.execution_id, result.stdout)
            
            if result.stderr:
                self.error_received.emit(self.execution.execution_id, result.stderr)
            
            exit_code = 0 if result.success else 1
            self.execution_finished.emit(self.execution.execution_id, exit_code)
            
        except Exception as e:
            self.logger.error(f"ADB process execution error: {e}")
            self.error_received.emit(self.execution.execution_id, str(e))
            self.execution_finished.emit(self.execution.execution_id, -1)
    
    def cancel(self):
        """Cancel script execution."""
        self.cancelled = True
        if self.process and self.process.poll() is None:
            self.process.terminate()


class ScriptManager(QObject):
    """Main script manager service."""
    
    # Signals
    script_added = pyqtSignal(str)      # script_id
    script_removed = pyqtSignal(str)    # script_id
    script_updated = pyqtSignal(str)    # script_id
    execution_started = pyqtSignal(str) # execution_id
    execution_finished = pyqtSignal(str, int)  # execution_id, exit_code
    output_received = pyqtSignal(str, str)     # execution_id, output
    error_received = pyqtSignal(str, str)      # execution_id, error
    
    def __init__(self, config_dir: Optional[Path] = None):
        super().__init__()
        self.logger = get_logger(__name__)
        
        # Configuration
        self.config_dir = config_dir or Path.home() / ".adb-util"
        self.scripts_file = self.config_dir / "scripts.json"
        self.executions_file = self.config_dir / "script_executions.json"
        
        # Data storage
        self.scripts: Dict[str, Script] = {}
        self.executions: Dict[str, ScriptExecution] = {}
        self.active_workers: Dict[str, ScriptExecutionWorker] = {}
        
        # Initialize
        self._ensure_config_dir()
        self._load_scripts()
        self._load_executions()
        
        self.logger.info("Script manager initialized")
    
    def _ensure_config_dir(self):
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_scripts(self):
        """Load scripts from configuration file."""
        try:
            if self.scripts_file.exists():
                with open(self.scripts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.scripts = {
                        script_id: Script(**script_data)
                        for script_id, script_data in data.items()
                    }
                    # Convert string enums back to enum objects
                    for script in self.scripts.values():
                        script.script_type = ScriptType(script.script_type)
        except Exception as e:
            self.logger.error(f"Error loading scripts: {e}")
            self.scripts = {}
    
    def _save_scripts(self):
        """Save scripts to configuration file."""
        try:
            data = {}
            for script_id, script in self.scripts.items():
                script_dict = asdict(script)
                script_dict['script_type'] = script.script_type.value
                data[script_id] = script_dict
            
            with open(self.scripts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving scripts: {e}")
    
    def _load_executions(self):
        """Load execution history from configuration file."""
        try:
            if self.executions_file.exists():
                with open(self.executions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.executions = {
                        exec_id: ScriptExecution(**exec_data)
                        for exec_id, exec_data in data.items()
                    }
                    # Convert string enums back to enum objects
                    for execution in self.executions.values():
                        execution.status = ScriptStatus(execution.status)
        except Exception as e:
            self.logger.error(f"Error loading executions: {e}")
            self.executions = {}
    
    def _save_executions(self):
        """Save execution history to configuration file."""
        try:
            data = {}
            for exec_id, execution in self.executions.items():
                exec_dict = asdict(execution)
                exec_dict['status'] = execution.status.value
                data[exec_id] = exec_dict
            
            with open(self.executions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving executions: {e}")
    
    def add_script(self, name: str, script_type: ScriptType, script_path: str, 
                   description: str = "") -> str:
        """Add a new script."""
        script_id = str(uuid.uuid4())
        script = Script(
            id=script_id,
            name=name,
            script_type=script_type,
            script_path=script_path,
            description=description
        )
        
        self.scripts[script_id] = script
        self._save_scripts()
        
        self.script_added.emit(script_id)
        self.logger.info(f"Script added: {name} ({script_id})")
        
        return script_id
    
    def remove_script(self, script_id: str) -> bool:
        """Remove a script."""
        if script_id in self.scripts:
            del self.scripts[script_id]
            self._save_scripts()
            
            self.script_removed.emit(script_id)
            self.logger.info(f"Script removed: {script_id}")
            return True
        return False
    
    def update_script(self, script_id: str, **kwargs) -> bool:
        """Update script properties."""
        if script_id not in self.scripts:
            return False
        
        script = self.scripts[script_id]
        for key, value in kwargs.items():
            if hasattr(script, key):
                setattr(script, key, value)
        
        self._save_scripts()
        self.script_updated.emit(script_id)
        self.logger.info(f"Script updated: {script_id}")
        
        return True
    
    def get_script(self, script_id: str) -> Optional[Script]:
        """Get script by ID."""
        return self.scripts.get(script_id)
    
    def get_all_scripts(self) -> List[Script]:
        """Get all scripts."""
        return list(self.scripts.values())
    
    def get_scripts_by_type(self, script_type: ScriptType) -> List[Script]:
        """Get scripts by type."""
        return [script for script in self.scripts.values() 
                if script.script_type == script_type]
    
    def execute_script(self, script_id: str, device_id: str = None) -> str:
        """Execute a script asynchronously."""
        if script_id not in self.scripts:
            raise ValueError(f"Script not found: {script_id}")
        
        script = self.scripts[script_id]
        
        # Validate device requirement
        if script.script_type == ScriptType.DEVICE and not device_id:
            raise ValueError("Device ID required for device script execution")
        
        # Create execution record
        execution_id = str(uuid.uuid4())
        execution = ScriptExecution(
            script_id=script_id,
            execution_id=execution_id,
            status=ScriptStatus.RUNNING,
            start_time=datetime.now().isoformat(),
            device_id=device_id or ""
        )
        
        self.executions[execution_id] = execution
        
        # Update script run count
        script.run_count += 1
        script.last_run = datetime.now().isoformat()
        self._save_scripts()
        
        # Create and start worker
        worker = ScriptExecutionWorker(script, execution, device_id)
        worker.output_received.connect(self._on_output_received)
        worker.error_received.connect(self._on_error_received)
        worker.execution_finished.connect(self._on_execution_finished)
        worker.execution_started.connect(self._on_execution_started)
        
        self.active_workers[execution_id] = worker
        worker.start()
        
        self.logger.info(f"Script execution started: {script.name} ({execution_id})")
        
        return execution_id
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel script execution."""
        if execution_id in self.active_workers:
            worker = self.active_workers[execution_id]
            worker.cancel()
            
            # Update execution status
            if execution_id in self.executions:
                self.executions[execution_id].status = ScriptStatus.CANCELLED
                self.executions[execution_id].end_time = datetime.now().isoformat()
                self._save_executions()
            
            self.logger.info(f"Script execution cancelled: {execution_id}")
            return True
        return False
    
    def get_execution(self, execution_id: str) -> Optional[ScriptExecution]:
        """Get execution by ID."""
        return self.executions.get(execution_id)
    
    def get_executions_for_script(self, script_id: str) -> List[ScriptExecution]:
        """Get all executions for a script."""
        return [exec for exec in self.executions.values() 
                if exec.script_id == script_id]
    
    def get_recent_executions(self, limit: int = 10) -> List[ScriptExecution]:
        """Get recent executions."""
        sorted_executions = sorted(
            self.executions.values(),
            key=lambda x: x.start_time,
            reverse=True
        )
        return sorted_executions[:limit]
    
    def _on_execution_started(self, execution_id: str):
        """Handle execution started."""
        self.execution_started.emit(execution_id)
    
    def _on_output_received(self, execution_id: str, output: str):
        """Handle output received."""
        if execution_id in self.executions:
            self.executions[execution_id].stdout += output + "\n"
        self.output_received.emit(execution_id, output)
    
    def _on_error_received(self, execution_id: str, error: str):
        """Handle error received."""
        if execution_id in self.executions:
            self.executions[execution_id].stderr += error + "\n"
        self.error_received.emit(execution_id, error)
    
    def _on_execution_finished(self, execution_id: str, exit_code: int):
        """Handle execution finished."""
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            execution.exit_code = exit_code
            execution.end_time = datetime.now().isoformat()
            execution.status = ScriptStatus.COMPLETED if exit_code == 0 else ScriptStatus.FAILED
            self._save_executions()
        
        # Clean up worker
        if execution_id in self.active_workers:
            del self.active_workers[execution_id]
        
        self.execution_finished.emit(execution_id, exit_code)
        self.logger.info(f"Script execution finished: {execution_id} (exit code: {exit_code})")
    
    def is_execution_running(self, execution_id: str) -> bool:
        """Check if execution is running."""
        return execution_id in self.active_workers
    
    def get_running_executions(self) -> List[str]:
        """Get list of running execution IDs."""
        return list(self.active_workers.keys())
    
    def cleanup_old_executions(self, max_age_days: int = 30, max_count: int = 100):
        """Cleanup old execution records."""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        # Remove old executions
        executions_to_remove = []
        for exec_id, execution in self.executions.items():
            try:
                exec_date = datetime.fromisoformat(execution.start_time)
                if exec_date < cutoff_date:
                    executions_to_remove.append(exec_id)
            except ValueError:
                # Invalid date format, remove it
                executions_to_remove.append(exec_id)
        
        for exec_id in executions_to_remove:
            del self.executions[exec_id]
        
        # Keep only the most recent executions if we have too many
        if len(self.executions) > max_count:
            sorted_executions = sorted(
                self.executions.items(),
                key=lambda x: x[1].start_time,
                reverse=True
            )
            
            executions_to_keep = dict(sorted_executions[:max_count])
            self.executions = executions_to_keep
        
        self._save_executions()
        
        if executions_to_remove:
            self.logger.info(f"Cleaned up {len(executions_to_remove)} old execution records")


# Global script manager instance
_script_manager = None

def get_script_manager() -> ScriptManager:
    """Get global script manager instance."""
    global _script_manager
    if _script_manager is None:
        _script_manager = ScriptManager()
    return _script_manager
