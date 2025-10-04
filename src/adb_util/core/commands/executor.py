"""
Command execution functionality.

This module handles the execution of ADB commands with proper error handling
and timeout management.
"""

import asyncio
import subprocess
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass

from ...utils.logger import get_logger
from ...utils.constants import COMMAND_TIMEOUT


@dataclass
class CommandResult:
    """Result of a command execution."""
    success: bool
    stdout: str
    stderr: str
    return_code: int


class CommandExecutor:
    """Executes ADB commands with proper error handling."""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.logger = get_logger(__name__)
    
    async def execute_command(self, command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """Execute an ADB command and return stdout, stderr, and return code."""
        full_command = f"adb -s {self.device_id} {command}"
        self.logger.debug(f"Executing command: {full_command}")
        
        try:
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            stdout_str = stdout.decode('utf-8', errors='ignore').strip()
            stderr_str = stderr.decode('utf-8', errors='ignore').strip()
            
            self.logger.debug(f"Command completed with return code: {process.returncode}")
            
            return stdout_str, stderr_str, process.returncode
            
        except asyncio.TimeoutError:
            self.logger.error(f"Command timeout: {full_command}")
            return "", "Command timeout", -1
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return "", str(e), -1
    
    async def execute_shell_command(self, command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """Execute a shell command on the device."""
        shell_command = f"shell {command}"
        return await self.execute_command(shell_command, timeout)
    
    async def get_device_properties(self) -> Dict[str, str]:
        """Get device properties using getprop."""
        stdout, stderr, return_code = await self.execute_shell_command("getprop")
        
        if return_code == 0:
            return self._parse_properties(stdout)
        else:
            self.logger.error(f"Failed to get device properties: {stderr}")
            return {}
    
    def _parse_properties(self, output: str) -> Dict[str, str]:
        """Parse properties from getprop output."""
        properties = {}
        for line in output.split('\n'):
            line = line.strip()
            if ':' in line:
                try:
                    key, value = line.split(':', 1)
                    key = key.strip('[]')
                    value = value.strip('[]')
                    properties[key] = value
                except ValueError:
                    continue
        return properties
    
    def is_adb_available(self) -> bool:
        """Check if ADB is available and accessible."""
        try:
            result = subprocess.run(
                ["adb", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
