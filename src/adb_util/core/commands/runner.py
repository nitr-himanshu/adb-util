"""
Command runner - main interface for command execution.

This module provides the main interface for ADB command execution,
combining executor and shell functionality.
"""

from typing import Tuple, Optional, Dict
from ...utils.logger import get_logger
from .executor import CommandExecutor, CommandResult
from .shell import ShellManager


class CommandRunner:
    """Main command runner that coordinates execution and shell operations."""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.executor = CommandExecutor(device_id)
        self.shell = ShellManager(device_id)
    
    async def execute_command(self, command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """Execute an ADB command."""
        return await self.executor.execute_command(command, timeout)
    
    async def execute_shell_command(self, command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """Execute a shell command on the device."""
        return await self.executor.execute_shell_command(command, timeout)
    
    async def start_shell_session(self):
        """Start an interactive shell session."""
        await self.shell.start_shell_session()
    
    async def stop_shell_session(self):
        """Stop the interactive shell session."""
        await self.shell.stop_shell_session()
    
    async def send_shell_command(self, command: str) -> str:
        """Send a command to the shell session."""
        return await self.shell.send_shell_command(command)
    
    def is_shell_active(self) -> bool:
        """Check if shell session is active."""
        return self.shell.is_shell_active()
    
    async def get_device_properties(self) -> Dict[str, str]:
        """Get device properties."""
        return await self.executor.get_device_properties()
    
    def is_adb_available(self) -> bool:
        """Check if ADB is available."""
        return self.executor.is_adb_available()
