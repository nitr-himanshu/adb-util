"""
Command Runner

ADB command execution and shell operations.
"""

import asyncio
import subprocess
from typing import Tuple, Optional, Dict

from utils.logger import get_logger
from utils.constants import COMMAND_TIMEOUT


class CommandRunner:
    """Executes ADB commands and manages shell sessions."""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.logger = get_logger(__name__)
        
        self.logger.info(f"Command runner initialized for device: {device_id}")
    
    async def execute_command(self, command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """Execute ADB command and return stdout, stderr, and return code."""
        full_command = f"adb -s {self.device_id} {command}"
        self.logger.debug(f"Executing ADB command: {full_command}")
        
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
            
            stdout_str = stdout.decode('utf-8', errors='ignore')
            stderr_str = stderr.decode('utf-8', errors='ignore')
            return_code = process.returncode
            
            self.logger.debug(f"Command completed with return code: {return_code}")
            return stdout_str, stderr_str, return_code
            
        except asyncio.TimeoutError:
            self.logger.error(f"Command timeout after {timeout}s: {full_command}")
            return "", f"Command timeout after {timeout}s", -1
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return "", str(e), -1
    
    async def execute_shell_command(self, command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """Execute shell command on device."""
        shell_command = f"shell {command}"
        self.logger.debug(f"Executing shell command on {self.device_id}: {command}")
        return await self.execute_command(shell_command, timeout)
    
    async def start_shell_session(self):
        """Start interactive shell session."""
        shell_command = f"adb -s {self.device_id} shell"
        self.logger.info(f"Starting interactive shell for device: {self.device_id}")
        
        try:
            # For interactive shell, we'll use subprocess.Popen
            process = subprocess.Popen(
                shell_command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return process
        except Exception as e:
            self.logger.error(f"Failed to start shell session: {e}")
            return None
    
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
            self.logger.error("ADB not found or not accessible")
            return False
    
    async def get_device_properties(self) -> Dict[str, str]:
        """Get device properties using getprop."""
        self.logger.debug(f"Retrieving device properties for: {self.device_id}")
        
        stdout, stderr, return_code = await self.execute_shell_command("getprop")
        
        if return_code != 0:
            self.logger.error(f"Failed to get device properties: {stderr}")
            return {}
        
        return self._parse_properties(stdout)
    
    def _parse_properties(self, output: str) -> Dict[str, str]:
        """Parse device properties from getprop output."""
        import re
        properties = {}
        
        # Pattern matches: [property.name]: [value]
        pattern = r'\[([^\]]+)\]:\s*\[([^\]]*)\]'
        
        for match in re.finditer(pattern, output):
            prop_name = match.group(1)
            prop_value = match.group(2)
            properties[prop_name] = prop_value
        
        return properties
