"""
File Operations

ADB file push/pull operations and file management.
"""

import subprocess
import os
from pathlib import Path
import asyncio
from typing import List, Dict, Optional, Tuple
import re
from datetime import datetime

from utils.logger import get_logger


class FileInfo:
    """Information about a file or directory."""
    
    def __init__(self, name: str, path: str, is_directory: bool = False, 
                 size: int = 0, permissions: str = "", modified: str = ""):
        self.name = name
        self.path = path
        self.is_directory = is_directory
        self.size = size
        self.permissions = permissions
        self.modified = modified
    
    def __repr__(self):
        return f"FileInfo({self.name}, dir={self.is_directory}, size={self.size})"


class FileOperations:
    """Handles file operations between local system and Android device."""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.logger = get_logger(__name__)
    
    async def push_file(self, local_path: Path, device_path: str, progress_callback=None) -> bool:
        """Push file from local system to device."""
        try:
            self.logger.info(f"Pushing file {local_path} to {device_path} on device {self.device_id}")
            
            # Execute adb push command
            cmd = ["adb", "-s", self.device_id, "push", str(local_path), device_path]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info(f"Successfully pushed file to device")
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.logger.error(f"Failed to push file: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error pushing file: {e}")
            return False
    
    async def pull_file(self, device_path: str, local_path: Path, progress_callback=None) -> bool:
        """Pull file from device to local system."""
        try:
            self.logger.info(f"Pulling file {device_path} from device {self.device_id} to {local_path}")
            
            # Ensure local directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Execute adb pull command
            cmd = ["adb", "-s", self.device_id, "pull", device_path, str(local_path)]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info(f"Successfully pulled file from device")
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.logger.error(f"Failed to pull file: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error pulling file: {e}")
            return False
    
    async def delete_file(self, device_path: str) -> bool:
        """Delete file on device."""
        try:
            self.logger.info(f"Deleting file {device_path} on device {self.device_id}")
            
            # Execute adb shell rm command
            cmd = ["adb", "-s", self.device_id, "shell", "rm", "-f", device_path]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info(f"Successfully deleted file from device")
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.logger.error(f"Failed to delete file: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting file: {e}")
            return False
    
    async def delete_directory(self, device_path: str) -> bool:
        """Delete directory on device."""
        try:
            self.logger.info(f"Deleting directory {device_path} on device {self.device_id}")
            
            # Execute adb shell rm -rf command
            cmd = ["adb", "-s", self.device_id, "shell", "rm", "-rf", device_path]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info(f"Successfully deleted directory from device")
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.logger.error(f"Failed to delete directory: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting directory: {e}")
            return False
    
    async def create_directory(self, device_path: str) -> bool:
        """Create directory on device."""
        try:
            self.logger.info(f"Creating directory {device_path} on device {self.device_id}")
            
            # Execute adb shell mkdir command
            cmd = ["adb", "-s", self.device_id, "shell", "mkdir", "-p", device_path]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info(f"Successfully created directory on device")
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.logger.error(f"Failed to create directory: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating directory: {e}")
            return False
    
    async def move_file(self, source_path: str, dest_path: str) -> bool:
        """Move/rename file on device."""
        try:
            self.logger.info(f"Moving file {source_path} to {dest_path} on device {self.device_id}")
            
            # Execute adb shell mv command
            cmd = ["adb", "-s", self.device_id, "shell", "mv", source_path, dest_path]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info(f"Successfully moved file on device")
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.logger.error(f"Failed to move file: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error moving file: {e}")
            return False
    
    async def copy_file(self, source_path: str, dest_path: str) -> bool:
        """Copy file on device."""
        try:
            self.logger.info(f"Copying file {source_path} to {dest_path} on device {self.device_id}")
            
            # Execute adb shell cp command
            cmd = ["adb", "-s", self.device_id, "shell", "cp", source_path, dest_path]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info(f"Successfully copied file on device")
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.logger.error(f"Failed to copy file: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error copying file: {e}")
            return False
    
    async def list_directory(self, device_path: str) -> List[FileInfo]:
        """List contents of device directory."""
        try:
            self.logger.info(f"Listing directory {device_path} on device {self.device_id}")
            
            # First try detailed listing with ls -la
            cmd = ["adb", "-s", self.device_id, "shell", "ls", "-la", device_path]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = stdout.decode()
                files = self._parse_ls_output(output, device_path)
                if files:  # If we got files, return them
                    self.logger.info(f"Found {len(files)} items in directory using ls -la")
                    return files
            
            # Fallback: try simple ls command
            self.logger.info("Trying fallback simple ls command")
            cmd_simple = ["adb", "-s", self.device_id, "shell", "ls", device_path]
            process_simple = await asyncio.create_subprocess_exec(
                *cmd_simple,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout_simple, stderr_simple = await process_simple.communicate()
            
            if process_simple.returncode == 0:
                output_simple = stdout_simple.decode()
                files = self._parse_simple_ls_output(output_simple, device_path)
                self.logger.info(f"Found {len(files)} items in directory using simple ls")
                return files
            else:
                error_msg = stderr_simple.decode() if stderr_simple else "Unknown error"
                self.logger.error(f"Failed to list directory with simple ls: {error_msg}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error listing directory: {e}")
            return []
    
    def _parse_simple_ls_output(self, output: str, base_path: str) -> List[FileInfo]:
        """Parse simple ls output into FileInfo objects."""
        files = []
        lines = output.strip().split('\n')
        
        self.logger.debug(f"Parsing simple ls output for {base_path}:")
        self.logger.debug(f"Raw output: {repr(output)}")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # In simple ls, each line is typically just a filename
            name = line
            
            # Skip . and .. entries
            if name in ['.', '..']:
                continue
            
            # Build full path
            full_path = f"{base_path.rstrip('/')}/{name}"
            
            # We can't determine if it's a directory without additional info
            # So we'll assume it's a file for now
            is_directory = False
            
            # Try to determine if it's a directory by common patterns
            if name.endswith('/') or not '.' in name or name in ['sdcard', 'storage', 'data', 'system', 'vendor', 'etc', 'proc', 'sys', 'dev']:
                is_directory = True
                name = name.rstrip('/')  # Remove trailing slash if present
                full_path = f"{base_path.rstrip('/')}/{name}"
            
            file_info = FileInfo(
                name=name,
                path=full_path,
                is_directory=is_directory,
                size=0,  # Unknown size
                permissions="",  # Unknown permissions
                modified=""  # Unknown modification time
            )
            
            self.logger.debug(f"Created FileInfo from simple ls: {file_info}")
            files.append(file_info)
        
        self.logger.info(f"Parsed {len(files)} files from simple ls output")
        return files
    
    def _parse_ls_output(self, output: str, base_path: str) -> List[FileInfo]:
        """Parse ls -la output into FileInfo objects."""
        files = []
        lines = output.strip().split('\n')
        
        self.logger.debug(f"Parsing ls output for {base_path}:")
        self.logger.debug(f"Raw output: {repr(output)}")
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('total'):
                continue
                
            self.logger.debug(f"Processing line: {repr(line)}")
            
            # Try to parse ls -la format: permissions links owner group size date time name
            parts = line.split()
            if len(parts) < 8:
                self.logger.debug(f"Skipping line with insufficient parts: {len(parts)}")
                continue
                
            permissions = parts[0]
            
            # Handle size field - might be different for directories or devices
            size = 0
            size_idx = 4  # Default position for size
            
            # Try to find the size field by looking for numeric values
            for i in range(3, min(7, len(parts))):
                try:
                    size = int(parts[i])
                    size_idx = i
                    break
                except ValueError:
                    continue
            
            # If it's a directory, size is usually 0 or block size
            if permissions.startswith('d'):
                size = 0
            
            # Get file name (everything after date/time, which is usually 3 fields after size)
            name_start_idx = size_idx + 4  # size + 3 date/time fields
            if name_start_idx < len(parts):
                name = ' '.join(parts[name_start_idx:])
            else:
                # Fallback: use last part as name
                name = parts[-1] if parts else "unknown"
            
            # Skip . and .. entries
            if name in ['.', '..']:
                continue
            
            # Handle symbolic links (name might contain ->)
            if '->' in name:
                name = name.split('->')[0].strip()
            
            # Determine if it's a directory
            is_directory = permissions.startswith('d')
            
            # Build full path
            full_path = f"{base_path.rstrip('/')}/{name}"
            
            # Get modification time (try to extract from available fields)
            try:
                # Look for date/time fields after size
                time_fields = parts[size_idx + 1:size_idx + 4]
                modified = ' '.join(time_fields) if len(time_fields) >= 3 else ""
            except (IndexError, ValueError):
                modified = ""
            
            file_info = FileInfo(
                name=name,
                path=full_path,
                is_directory=is_directory,
                size=size,
                permissions=permissions,
                modified=modified
            )
            
            self.logger.debug(f"Created FileInfo: {file_info}")
            files.append(file_info)
        
        self.logger.info(f"Parsed {len(files)} files from ls output")
        return files
    
    async def test_device_connection(self) -> bool:
        """Test if device is accessible via ADB."""
        try:
            self.logger.info(f"Testing connection to device {self.device_id}")
            
            # Simple test: try to get device properties
            cmd = ["adb", "-s", self.device_id, "shell", "echo", "test"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = stdout.decode().strip()
                self.logger.info(f"Device connection test successful: {output}")
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.logger.error(f"Device connection test failed: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error testing device connection: {e}")
            return False
    
    async def get_file_info(self, device_path: str) -> Optional[FileInfo]:
        """Get information about a specific file."""
        try:
            # Execute adb shell stat command if available, otherwise use ls
            cmd = ["adb", "-s", self.device_id, "shell", "ls", "-la", device_path]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = stdout.decode().strip()
                if output:
                    # Parse single file info
                    parts = output.split()
                    if len(parts) >= 8:
                        permissions = parts[0]
                        size = 0
                        try:
                            size = int(parts[4]) if not permissions.startswith('d') else 0
                        except (ValueError, IndexError):
                            pass
                        
                        name = os.path.basename(device_path)
                        is_directory = permissions.startswith('d')
                        
                        try:
                            modified = f"{parts[5]} {parts[6]} {parts[7]}"
                        except IndexError:
                            modified = ""
                        
                        return FileInfo(
                            name=name,
                            path=device_path,
                            is_directory=is_directory,
                            size=size,
                            permissions=permissions,
                            modified=modified
                        )
            
            return None
                
        except Exception as e:
            self.logger.error(f"Error getting file info: {e}")
            return None
