"""
Logcat Handler

Real-time logcat streaming and log management.
"""

import asyncio
import subprocess
import re
from typing import AsyncGenerator, Optional, Dict, List, Callable
from datetime import datetime
from dataclasses import dataclass

from utils.logger import get_logger
from utils.constants import ADB_LOGCAT_COMMAND, COMMAND_TIMEOUT, MAX_LOG_BUFFER_SIZE


@dataclass
class LogEntry:
    """Represents a parsed logcat entry."""
    timestamp: str
    pid: str
    tid: str
    level: str
    tag: str
    message: str
    raw_line: str
    parsed_time: Optional[datetime] = None
    
    def __post_init__(self):
        """Parse timestamp if possible."""
        try:
            # Parse Android logcat timestamp format: MM-DD HH:MM:SS.mmm
            self.parsed_time = datetime.strptime(
                f"2024-{self.timestamp}", 
                "%Y-%m-%d %H:%M:%S.%f"
            )
        except ValueError:
            self.parsed_time = None


class LogcatHandler:
    """Handles logcat streaming and log operations."""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.logger = get_logger(__name__)
        self.logcat_process = None
        self.is_streaming = False
        self.log_entries: List[LogEntry] = []
        self.max_buffer_size = MAX_LOG_BUFFER_SIZE
        
        # Callbacks for real-time updates
        self.on_log_entry: Optional[Callable[[LogEntry], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_stream_status: Optional[Callable[[bool], None]] = None
        
        # Logcat parsing regex patterns
        self.logcat_patterns = [
            # Standard format: MM-DD HH:MM:SS.mmm  PID  TID LEVEL TAG: MESSAGE
            re.compile(r'^(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+(\d+)\s+(\d+)\s+([VDIWEF])\s+([^:]+):\s*(.*)$'),
            # Brief format: LEVEL/TAG(PID): MESSAGE
            re.compile(r'^([VDIWEF])/([^(]+)\(\s*(\d+)\):\s*(.*)$'),
            # Time format: MM-DD HH:MM:SS.mmm LEVEL/TAG(PID): MESSAGE  
            re.compile(r'^(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+([VDIWEF])/([^(]+)\(\s*(\d+)\):\s*(.*)$'),
        ]
        
        self.logger.info(f"Logcat handler initialized for device: {device_id}")
    
    async def start_logcat_stream(self, 
                                 buffer: Optional[str] = None,
                                 filter_spec: Optional[str] = None,
                                 format_type: str = "time") -> AsyncGenerator[LogEntry, None]:
        """Start real-time logcat streaming."""
        if self.is_streaming:
            self.logger.warning("Logcat stream already running")
            return
        
        try:
            # Build logcat command
            command = ADB_LOGCAT_COMMAND.format(device_id=self.device_id)
            
            # Add format
            command += f" -v {format_type}"
            
            # Add buffer if specified
            if buffer:
                command += f" -b {buffer}"
            
            # Add filter if specified
            if filter_spec:
                command += f" {filter_spec}"
            
            self.logger.info(f"Starting logcat stream: {command}")
            
            # Start logcat process
            self.logcat_process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.is_streaming = True
            if self.on_stream_status:
                self.on_stream_status(True)
            
            # Read logcat output line by line
            while self.is_streaming and self.logcat_process:
                try:
                    # Use shorter timeout for more responsive stop
                    line = await asyncio.wait_for(
                        self.logcat_process.stdout.readline(),
                        timeout=0.5
                    )
                    
                    if not line:
                        break
                    
                    line_str = line.decode('utf-8', errors='ignore').strip()
                    if line_str:
                        log_entry = self.parse_log_line(line_str)
                        if log_entry:
                            # Add to buffer
                            self.log_entries.append(log_entry)
                            
                            # Maintain buffer size
                            if len(self.log_entries) > self.max_buffer_size:
                                self.log_entries = self.log_entries[-self.max_buffer_size:]
                            
                            # Notify callback
                            if self.on_log_entry:
                                self.on_log_entry(log_entry)
                            
                            yield log_entry
                
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error reading logcat stream: {e}")
                    if self.on_error:
                        self.on_error(str(e))
                    break
        
        except Exception as e:
            self.logger.error(f"Failed to start logcat stream: {e}")
            if self.on_error:
                self.on_error(str(e))
        
        finally:
            await self.stop_logcat_stream()
    
    async def stop_logcat_stream(self):
        """Stop logcat streaming."""
        if not self.is_streaming:
            return
        
        self.logger.info("Stopping logcat stream")
        self.is_streaming = False
        
        if self.logcat_process:
            try:
                # First try graceful termination with shorter timeout
                self.logcat_process.terminate()
                await asyncio.wait_for(self.logcat_process.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                # Force kill if graceful termination takes too long
                self.logger.warning("Logcat process termination timeout, forcing kill")
                self.logcat_process.kill()
                try:
                    await asyncio.wait_for(self.logcat_process.wait(), timeout=1.0)
                except asyncio.TimeoutError:
                    self.logger.error("Failed to kill logcat process")
            except Exception as e:
                self.logger.error(f"Error stopping logcat process: {e}")
            finally:
                self.logcat_process = None
        
        if self.on_stream_status:
            self.on_stream_status(False)
        
        self.logger.info("Logcat stream stopped")
    
    async def clear_logcat(self) -> bool:
        """Clear device logs."""
        try:
            command = f"adb -s {self.device_id} logcat -c"
            self.logger.info(f"Clearing logcat: {command}")
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=COMMAND_TIMEOUT
            )
            
            if process.returncode == 0:
                self.logger.info("Logcat cleared successfully")
                # Also clear our buffer
                self.log_entries.clear()
                return True
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                self.logger.error(f"Failed to clear logcat: {error_msg}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error clearing logcat: {e}")
            return False
    
    async def get_logcat_dump(self, 
                             lines: Optional[int] = None,
                             filter_spec: Optional[str] = None,
                             format_type: str = "time") -> List[LogEntry]:
        """Get logcat dump (non-streaming)."""
        try:
            # Build command
            command = ADB_LOGCAT_COMMAND.format(device_id=self.device_id)
            command += f" -v {format_type} -d"  # -d for dump mode
            
            # Add line limit if specified
            if lines:
                command += f" -t {lines}"
            
            # Add filter if specified
            if filter_spec:
                command += f" {filter_spec}"
            
            self.logger.info(f"Getting logcat dump: {command}")
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=COMMAND_TIMEOUT
            )
            
            if process.returncode == 0:
                output = stdout.decode('utf-8', errors='ignore')
                entries = []
                
                for line in output.strip().split('\n'):
                    if line.strip():
                        entry = self.parse_log_line(line.strip())
                        if entry:
                            entries.append(entry)
                
                self.logger.info(f"Retrieved {len(entries)} log entries")
                return entries
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                self.logger.error(f"Failed to get logcat dump: {error_msg}")
                return []
        
        except Exception as e:
            self.logger.error(f"Error getting logcat dump: {e}")
            return []
    
    def parse_log_line(self, line: str) -> Optional[LogEntry]:
        """Parse logcat line into structured data."""
        if not line.strip():
            return None
        
        # Try different patterns
        for pattern in self.logcat_patterns:
            match = pattern.match(line)
            if match:
                groups = match.groups()
                
                # Standard format: timestamp, pid, tid, level, tag, message
                if len(groups) == 6:
                    timestamp, pid, tid, level, tag, message = groups
                    return LogEntry(
                        timestamp=timestamp,
                        pid=pid,
                        tid=tid,
                        level=level,
                        tag=tag.strip(),
                        message=message,
                        raw_line=line
                    )
                
                # Brief format: level, tag, pid, message
                elif len(groups) == 4:
                    level, tag, pid, message = groups
                    return LogEntry(
                        timestamp="",
                        pid=pid,
                        tid="",
                        level=level,
                        tag=tag.strip(),
                        message=message,
                        raw_line=line
                    )
                
                # Time format: timestamp, level, tag, pid, message
                elif len(groups) == 5:
                    timestamp, level, tag, pid, message = groups
                    return LogEntry(
                        timestamp=timestamp,
                        pid=pid,
                        tid="",
                        level=level,
                        tag=tag.strip(),
                        message=message,
                        raw_line=line
                    )
        
        # If no pattern matches, return None
        return None
    
    def filter_entries(self, 
                      entries: List[LogEntry],
                      level_filter: Optional[List[str]] = None,
                      tag_filter: Optional[str] = None,
                      message_filter: Optional[str] = None,
                      case_sensitive: bool = False,
                      use_regex: bool = False) -> List[LogEntry]:
        """Filter log entries based on criteria."""
        filtered = entries
        
        # Filter by log level
        if level_filter:
            filtered = [e for e in filtered if e.level in level_filter]
        
        # Filter by tag
        if tag_filter:
            if use_regex:
                try:
                    pattern = re.compile(tag_filter, re.IGNORECASE if not case_sensitive else 0)
                    filtered = [e for e in filtered if pattern.search(e.tag)]
                except re.error:
                    # Invalid regex, fall back to string search
                    tag_filter_lower = tag_filter.lower() if not case_sensitive else tag_filter
                    filtered = [e for e in filtered if 
                               (tag_filter_lower in e.tag.lower() if not case_sensitive else tag_filter in e.tag)]
            else:
                tag_filter_lower = tag_filter.lower() if not case_sensitive else tag_filter
                filtered = [e for e in filtered if 
                           (tag_filter_lower in e.tag.lower() if not case_sensitive else tag_filter in e.tag)]
        
        # Filter by message
        if message_filter:
            if use_regex:
                try:
                    pattern = re.compile(message_filter, re.IGNORECASE if not case_sensitive else 0)
                    filtered = [e for e in filtered if pattern.search(e.message)]
                except re.error:
                    # Invalid regex, fall back to string search
                    msg_filter_lower = message_filter.lower() if not case_sensitive else message_filter
                    filtered = [e for e in filtered if 
                               (msg_filter_lower in e.message.lower() if not case_sensitive else message_filter in e.message)]
            else:
                msg_filter_lower = message_filter.lower() if not case_sensitive else message_filter
                filtered = [e for e in filtered if 
                           (msg_filter_lower in e.message.lower() if not case_sensitive else message_filter in e.message)]
        
        return filtered
    
    def get_buffer_stats(self) -> Dict[str, int]:
        """Get statistics about the current log buffer."""
        if not self.log_entries:
            return {"total": 0, "levels": {}}
        
        level_counts = {}
        for entry in self.log_entries:
            level_counts[entry.level] = level_counts.get(entry.level, 0) + 1
        
        return {
            "total": len(self.log_entries),
            "levels": level_counts
        }
    
    def export_logs(self, filename: str, entries: Optional[List[LogEntry]] = None) -> bool:
        """Export logs to file."""
        try:
            entries_to_export = entries or self.log_entries
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# Logcat export from device: {self.device_id}\n")
                f.write(f"# Export time: {datetime.now().isoformat()}\n")
                f.write(f"# Total entries: {len(entries_to_export)}\n\n")
                
                for entry in entries_to_export:
                    f.write(f"{entry.raw_line}\n")
            
            self.logger.info(f"Exported {len(entries_to_export)} log entries to {filename}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to export logs: {e}")
            return False
