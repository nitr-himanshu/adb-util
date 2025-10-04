"""
Shell session management.

This module handles interactive shell sessions and shell command execution.
"""

import asyncio
import subprocess
from typing import List
from dataclasses import dataclass

from ...utils.logger import get_logger
from .executor import CommandResult


class ShellManager:
    """Manages interactive shell sessions."""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.logger = get_logger(__name__)
        self._shell_process: Optional[asyncio.subprocess.Process] = None
    
    async def start_shell_session(self):
        """Start an interactive shell session."""
        if self._shell_process:
            self.logger.warning("Shell session already active")
            return
        
        try:
            self._shell_process = await asyncio.create_subprocess_shell(
                f"adb -s {self.device_id} shell",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            self.logger.info(f"Shell session started for device {self.device_id}")
        except Exception as e:
            self.logger.error(f"Failed to start shell session: {e}")
            raise
    
    async def stop_shell_session(self):
        """Stop the interactive shell session."""
        if self._shell_process:
            self._shell_process.terminate()
            await self._shell_process.wait()
            self._shell_process = None
            self.logger.info("Shell session stopped")
    
    async def send_shell_command(self, command: str) -> str:
        """Send a command to the shell session and get response."""
        if not self._shell_process:
            raise RuntimeError("Shell session not started")
        
        try:
            self._shell_process.stdin.write(f"{command}\n".encode())
            await self._shell_process.stdin.drain()
            
            # Read response
            response = await self._shell_process.stdout.readline()
            return response.decode('utf-8', errors='ignore').strip()
            
        except Exception as e:
            self.logger.error(f"Failed to send shell command: {e}")
            raise
    
    def is_shell_active(self) -> bool:
        """Check if shell session is active."""
        return self._shell_process is not None and self._shell_process.returncode is None
