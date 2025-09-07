# Script Manager

The Script Manager is a powerful feature in ADB-UTIL that allows you to create, edit, and execute custom scripts for both host systems and connected Android devices.

## Features

### Script Types

1. **Host Scripts (Windows .bat)**
   - Batch files that run on Windows host system
   - Perfect for system administration tasks, ADB commands, file operations
   - Executed using Windows Command Prompt

2. **Host Scripts (Linux .sh)**
   - Shell scripts that run on Linux/Unix host systems
   - Supports bash scripting for advanced automation
   - Executed using bash shell

3. **Device Scripts (.sh)**
   - Shell scripts that are pushed to and executed on connected Android devices
   - Useful for device diagnostics, app management, system monitoring
   - Automatically made executable and cleaned up after execution

### Integrated Script Editor

- **Syntax Highlighting**: Context-aware highlighting for batch and shell scripts
- **Line Numbers**: Easy navigation with visible line numbers
- **Templates**: Pre-built templates for common script scenarios
- **Import/Export**: Import existing scripts or export for sharing
- **Real-time Editing**: Live syntax checking and formatting

### Script Management

- **Create New Scripts**: Built-in editor with syntax highlighting
- **Import Scripts**: Import existing .bat or .sh files
- **Duplicate Scripts**: Clone existing scripts for modification
- **Export Scripts**: Save scripts to custom locations
- **Organize by Type**: Filter scripts by Windows, Linux, or Device types

### Execution Features

- **Async Execution**: Scripts run in background threads without blocking UI
- **Real-time Output**: Live capture of stdout and stderr
- **Output Windows**: Dedicated windows for viewing script output
- **Save Output**: Export execution results to text files
- **Execution History**: Track recent script runs with status and exit codes
- **Device Selection**: Automatic device detection for device scripts

## Getting Started

### Creating Your First Script

1. Click the "📝 New Script" button in the Script Manager tab
2. Choose your script type (Windows .bat, Linux .sh, or Device .sh)
3. Enter a name and optional description
4. Write your script content in the editor
5. Use templates for common patterns
6. Save your script

### Sample Scripts

The application includes sample scripts in the `sample_scripts/` directory:

#### Host Scripts
- `adb_check.bat/sh`: Check ADB status and connected devices
- `system_info.bat/sh`: Collect system information

#### Device Scripts
- `device_info.sh`: Gather device hardware and software information
- `performance_monitor.sh`: Monitor device performance metrics
- `log_collection.sh`: Collect device logs and diagnostics

### Script Templates

The editor includes built-in templates for common scenarios:

#### Windows Batch Templates
- **System Info**: Collect Windows system information
- **ADB Check**: Verify ADB setup and device connectivity

#### Linux Shell Templates
- **System Info**: Gather Linux system details
- **ADB Check**: Test ADB installation and device status

#### Device Script Templates
- **Device Info**: Collect device specifications and status
- **Performance Monitor**: Monitor CPU, memory, and battery

### Best Practices

#### Host Scripts
- Use absolute paths when possible
- Add error checking and user feedback
- Include pause statements for interactive review
- Test scripts thoroughly before deployment

#### Device Scripts
- Keep scripts lightweight and focused
- Use standard Android shell commands
- Handle permissions gracefully
- Clean up temporary files

### Execution Output

Each script execution creates a dedicated output window showing:
- Real-time stdout and stderr streams
- Execution status and duration
- Exit codes for success/failure detection
- Save functionality for archiving results

### Troubleshooting

#### Script Not Found
- Verify the script file exists at the specified path
- Check file permissions (scripts should be readable)
- For device scripts, ensure device is connected and authorized

#### Execution Timeout
- Long-running scripts may need timeout adjustments
- Consider breaking complex scripts into smaller parts
- Use background execution for monitoring scripts

#### Permission Denied
- Ensure shell scripts are executable (chmod +x)
- Verify ADB permissions for device operations
- Check device developer options and USB debugging

#### Device Not Found
- Confirm device is connected and authorized
- Refresh device list in the main window
- Check ADB drivers and cable connections

## Advanced Usage

### Environment Variables

#### Windows Scripts
```batch
@echo off
echo Device ID: %DEVICE_ID%
echo User Profile: %USERPROFILE%
echo Current Directory: %CD%
```

#### Linux/Device Scripts
```bash
#!/bin/bash
echo "Device ID: $DEVICE_ID"
echo "Home Directory: $HOME"
echo "Current Directory: $(pwd)"
```

### Error Handling

#### Windows
```batch
@echo off
adb devices >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ADB not found or not working
    exit /b 1
)
echo ADB is working properly
```

#### Shell Scripts
```bash
#!/bin/bash
if ! command -v adb &> /dev/null; then
    echo "ADB not found in PATH"
    exit 1
fi
echo "ADB is available"
```

### Device Script Patterns

#### Check Device Status
```bash
#!/system/bin/sh
# Check if device is properly booted
if [ "$(getprop sys.boot_completed)" = "1" ]; then
    echo "Device boot completed"
else
    echo "Device still booting"
fi
```

#### Monitor Resources
```bash
#!/system/bin/sh
# Monitor memory usage
echo "Memory Status:"
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable"

echo "Top processes by memory:"
top -n 1 | head -10
```

## Configuration

Scripts are stored in:
- **Configuration**: `~/.adb-util/scripts.json`
- **User Scripts**: `~/.adb-util/user_scripts/`
- **Execution History**: `~/.adb-util/script_executions.json`

The script manager automatically:
- Creates necessary directories
- Manages script metadata
- Tracks execution history
- Handles cleanup and maintenance

## Security Considerations

- Scripts run with the same privileges as the ADB-UTIL application
- Device scripts are temporarily stored on the device during execution
- Always review imported scripts before execution
- Use caution with scripts that modify system settings
- Regular cleanup of execution history is recommended

## Integration

The Script Manager integrates seamlessly with other ADB-UTIL features:
- **Device Manager**: Automatic device detection for device scripts
- **Theme Manager**: Consistent theming across script editor and output windows
- **Logging System**: Comprehensive logging of script operations
- **File Manager**: Easy access to script files and output results
