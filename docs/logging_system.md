# ADB-UTIL Logging System

This document describes the comprehensive logging system implemented in ADB-UTIL.

## Overview

The ADB-UTIL application includes a robust logging system that provides:

- **Console Logging**: Real-time log output to the console (enabled by default)
- **File Logging**: Optional file-based logging with timestamp-based filenames (disabled by default)
- **Centralized Configuration**: Unified logging management across all modules
- **Multiple Log Levels**: DEBUG, INFO, WARNING, ERROR support
- **Rotating Files**: Automatic log file rotation when size limits are reached
- **Module-Specific Loggers**: Separate loggers for different application components

## Features

### 1. Console Logging

- Enabled by default
- Shows INFO level and above messages
- Color-coded output (where supported)
- Real-time feedback during application usage

### 2. File Logging

- **Disabled by default** (as requested)
- Can be enabled through Preferences dialog or programmatically
- **Timestamp-based filenames**: `ADB-UTIL_YYYYMMDD_HHMMSS.log`
- Automatic log directory creation: `~/.adb-util/logs/`
- File rotation at 10MB with 5 backup files
- Logs DEBUG level and above when enabled

### 3. Centralized Management

- Singleton `LoggerManager` class
- Consistent formatting across all modules
- Global enable/disable for file logging
- Configurable log levels for console and file separately

## Usage

### Basic Logging in Code

```python
from utils.logger import get_logger

# Get logger for current module
logger = get_logger(__name__)

# Log different levels
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

### Convenience Functions

```python
from utils.logger import log_device_operation, log_file_operation

# Log device operations
log_device_operation("emulator-5554", "connect", "Device connected successfully")

# Log file operations
log_file_operation("push", "/local/file.txt", "/sdcard/file.txt", "success")
```

### Enable/Disable File Logging

```python
from utils.logger import enable_file_logging, disable_file_logging

# Enable file logging (uses default directory)
enable_file_logging()

# Enable with custom directory
enable_file_logging(Path("/custom/log/directory"))

# Disable file logging
disable_file_logging()
```

### Get Logging Status

```python
from utils.logger import get_log_info

log_info = get_log_info()
print(f"File logging enabled: {log_info['file_logging_enabled']}")
print(f"Log directory: {log_info['log_directory']}")
print(f"Current log file: {log_info['current_log_file']}")
```

## Configuration

### Through Preferences Dialog

1. Open **Tools → Preferences**
2. Go to **Logging** tab
3. Check/uncheck "Enable file logging"
4. Set log directory (optional)
5. Configure log levels for console and file
6. Click **Apply** or **OK**

### Through Code

```python
from utils.logger import set_console_level, set_file_level
import logging

# Set console to show only warnings and errors
set_console_level(logging.WARNING)

# Set file to log everything
set_file_level(logging.DEBUG)
```

## Log File Format

```
YYYY-MM-DD HH:MM:SS - ADB-UTIL.module_name - LEVEL - Message
```

Example:

```
2025-09-06 01:19:00 - ADB-UTIL.main_window - INFO - Main window initialization complete
2025-09-06 01:19:00 - ADB-UTIL.device - INFO - Device emulator-5554: connect - Device connected
2025-09-06 01:19:00 - ADB-UTIL.file_ops - INFO - File push: /local/file.txt -> /sdcard/file.txt [success]
```

## File Management

### Automatic Features

- Log files are created with timestamp-based names
- Automatic rotation when files exceed 10MB
- Keeps up to 5 backup files automatically
- UTF-8 encoding for proper character support

### Manual Management

- Access **Preferences → Logging → Open Log Directory** to view log files
- Use **Clear Old Logs** to remove files older than 7 days
- Log files can be safely deleted when the application is not running

## Integration Points

The logging system is integrated throughout the application:

### GUI Modules

- **MainWindow**: Tab operations, device selection, menu actions
- **FileManager**: File operations (push, pull, sync)
- **Terminal**: Command execution and shell operations
- **Logging**: Logcat capture and filtering
- **Utils**: Device utilities and system operations
- **Preferences**: Settings changes and configuration

### ADB Modules

- **DeviceManager**: Device discovery and connection management
- **CommandRunner**: ADB command execution
- **FileOperations**: File transfer operations
- **LogcatHandler**: Log capture and processing

### Application Lifecycle

- **Startup**: Application initialization logging
- **Shutdown**: Graceful shutdown logging
- **Error Handling**: Exception logging with stack traces

## Best Practices

### For Developers

1. **Use module-specific loggers**:

   ```python
   logger = get_logger(__name__)
   ```

2. **Choose appropriate log levels**:
   - `DEBUG`: Detailed diagnostic information
   - `INFO`: General application flow
   - `WARNING`: Something unexpected but not critical
   - `ERROR`: Error conditions that need attention

3. **Include context in messages**:

   ```python
   logger.info(f"Processing file: {filename} for device: {device_id}")
   ```

4. **Use convenience functions for common operations**:

   ```python
   log_device_operation(device_id, "reboot", "User initiated reboot")
   ```

### For Users

1. **Enable file logging for troubleshooting**:
   - Use Preferences dialog to enable file logging
   - Reproduce the issue
   - Share log files with support

2. **Monitor log directory size**:
   - Check `~/.adb-util/logs/` periodically
   - Use "Clear Old Logs" feature in preferences

3. **Set appropriate log levels**:
   - Use INFO for normal usage
   - Use DEBUG for detailed troubleshooting

## Testing

Use the included test script to verify logging functionality:

```bash
python test_logging.py
```

This script demonstrates:

- Console logging at different levels
- File logging enable/disable
- Multiple logger usage
- Configuration inspection
- Convenience function usage

## Troubleshooting

### Common Issues

1. **Log files not created**:
   - Check file permissions in log directory
   - Verify file logging is enabled
   - Check available disk space

2. **Log directory not found**:
   - Application will attempt to create the directory
   - Check parent directory permissions
   - Use custom directory in preferences

3. **Large log files**:
   - Files automatically rotate at 10MB
   - Adjust rotation settings in constants.py if needed
   - Use "Clear Old Logs" feature

### Debug Logging Issues

1. Check current configuration:

   ```python
   from utils.logger import get_log_info
   print(get_log_info())
   ```

2. Enable file logging programmatically:

   ```python
   from utils.logger import enable_file_logging
   enable_file_logging()
   ```

3. Test with simple logger:

   ```python
   from utils.logger import get_logger
   logger = get_logger("test")
   logger.info("Test message")
   ```

## Summary

The ADB-UTIL logging system provides comprehensive logging capabilities with:

✅ **Console logging enabled by default**  
✅ **File logging disabled by default** (as requested)  
✅ **Timestamp-based log filenames**  
✅ **Integrated throughout the application**  
✅ **User-configurable through preferences**  
✅ **Automatic file rotation and management**  
✅ **Multiple log levels and module-specific loggers**

The system balances ease of use with powerful debugging capabilities, making it suitable for both end users and developers.
