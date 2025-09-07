# ADB-UTIL

A comprehensive Python-based desktop application for Android Debug Bridge (ADB) operations with a modern GUI interface.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![Status](https://img.shields.io/badge/status-Active%20Development-brightgreen.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)

## Features

### 🔌 Device Management

- **Auto-discovery** of connected ADB devices (USB & WiFi) ✅ **IMPLEMENTED**
- **Real-time monitoring** of device connection status ✅ **IMPLEMENTED**
- **Multi-device support** with tabbed interface ✅ **IMPLEMENTED**
- **Device information** display (model, Android version, etc.) ✅ **IMPLEMENTED**
- **Connection type detection** (USB vs TCP/IP) ✅ **IMPLEMENTED**
- **Device status tracking** (online, offline, unauthorized) ✅ **IMPLEMENTED**

### 📁 File Manager

- **Dual-pane file browser** (local ↔ device) 🚧 **IN DEVELOPMENT**
- **Drag & drop** file transfers with progress indicators 🚧 **IN DEVELOPMENT**
- **File operations**: Push, Pull, Delete, Move, Copy 🚧 **IN DEVELOPMENT**
- **Integrated text editor** with line numbers and syntax highlighting 🚧 **IN DEVELOPMENT**
- **Auto-save functionality** for seamless editing experience 🚧 **IN DEVELOPMENT**
- **External editor support** for advanced editing workflows 🚧 **IN DEVELOPMENT**
- **File type detection** and appropriate handling 🚧 **IN DEVELOPMENT**

### 💻 Terminal

- **Interactive ADB shell** with command history 🚧 **IN DEVELOPMENT**
- **Save and organize** frequently used commands 🚧 **IN DEVELOPMENT**
- **Command categories** and quick execution 🚧 **IN DEVELOPMENT**
- **Auto-completion** and output formatting 🚧 **IN DEVELOPMENT**

### 📊 Logging

- **Real-time logcat streaming** with filtering ✅ **IMPLEMENTED**
- **Log level filtering** (Verbose, Debug, Info, Warning, Error) ✅ **IMPLEMENTED**
- **Package/tag filtering** and regex search ✅ **IMPLEMENTED**
- **Export logs** to file for analysis ✅ **IMPLEMENTED**
- **Multi-format support** (brief, time, threadtime, etc.) ✅ **IMPLEMENTED**
- **Buffer selection** (main, system, radio, events) ✅ **IMPLEMENTED**
- **Advanced search** with case sensitivity and regex ✅ **IMPLEMENTED**

### 🛠️ Utilities

- **WiFi status** and IP address display 🚧 **IN DEVELOPMENT**
- **One-click port forwarding** setup 🚧 **IN DEVELOPMENT**
- **Device screenshots** and system information 🚧 **IN DEVELOPMENT**
- **Battery monitoring** and network diagnostics 🚧 **IN DEVELOPMENT**

## Installation

### Prerequisites

- **Python 3.9 or higher** ✅
- **ADB (Android Debug Bridge)** installed and accessible ✅
- **PyQt6** (will be installed automatically) ✅

### Quick Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/nitr-himanshu/adb-util.git
   cd adb-util
   ```

2. **Create and activate virtual environment**

   ```bash
   python -m venv adb-util-env
   
   # Windows
   adb-util-env\Scripts\activate
   
   # macOS/Linux
   source adb-util-env/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**

   ```bash
   python main.py
   ```

### Using VS Code Tasks

The project includes pre-configured VS Code tasks for common operations:

- **Install Dependencies**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Install Dependencies"
- **Run Application**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Run ADB-UTIL"
- **Run Tests**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Run Tests"
- **Format Code**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Format Code (Black)"
- **Lint Code**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Lint Code (Flake8)"

### ADB Setup

Ensure ADB is installed and accessible:

**Windows:**

- Download [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools)
- Add to PATH or place `adb.exe` in project directory

**macOS:**

```bash
brew install android-platform-tools
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt install android-tools-adb
```

## Getting Started

### Quick Start Guide

1. **Clone and Setup**

   ```bash
   git clone https://github.com/nitr-himanshu/adb-util.git
   cd adb-util
   python -m venv adb-util-env
   adb-util-env\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Launch Application**

   ```bash
   python main.py
   ```

3. **Current Working Features**
   - ✅ **Device Discovery**: Automatically detects connected Android devices
   - ✅ **Real-time Monitoring**: Live device status updates
   - ✅ **Logcat Streaming**: Full-featured log viewing with filtering
   - ✅ **Export Functionality**: Save filtered logs to files

### What's Currently Working

The application successfully provides:

- **Device Management**: Robust device discovery and monitoring system
- **Logcat Collection**: Professional-grade log viewing with:
  - Real-time streaming
  - Advanced filtering (level, tag, message)
  - Multiple output formats (brief, time, threadtime)
  - Export capabilities with metadata
  - Buffer selection (main, system, radio, events)
  - Search functionality with regex support

## Usage

### Application Usage

1. **Launch the application**

   ```bash
   python main.py
   ```

2. **Connect your Android device**
   - Enable Developer Options and USB Debugging
   - Connect via USB or setup wireless ADB

3. **Select device and mode**
   - Choose your device from the home screen
   - Select desired operation mode (File Manager, Terminal, Logging, Utils)

### Device Modes

#### File Manager Mode

- **Local panel**: Browse your computer's files
- **Device panel**: Navigate Android device filesystem
- **Transfer files**: Drag & drop between panels
- **Edit files**: Double-click to open text editor

#### Terminal Mode

- **Execute commands**: Type ADB shell commands
- **Save commands**: Create reusable command shortcuts
- **Command history**: Access previously executed commands

#### Logging Mode

- **Start logcat**: Begin real-time log streaming
- **Apply filters**: Filter by log level, package, or custom regex
- **Export logs**: Save filtered logs to file

#### Utils Mode

- **Network info**: View WiFi status and IP address
- **Port forwarding**: Setup ADB port forwarding tunnels
- **Screenshots**: Capture device screenshots

## Logcat Formats and Buffer Levels

### Logcat Output Formats

The logging interface supports various output formats for different analysis needs:

#### Available Formats

| Format | Description | Example Output |
|--------|-------------|----------------|
| **brief** | Minimal format with priority, tag, and message | `I/ActivityManager: Starting activity` |
| **process** | Includes PID in addition to brief format | `I(12345) Starting activity (ActivityManager)` |
| **tag** | Shows priority and tag only | `I/ActivityManager: Starting activity` |
| **raw** | Raw log message without any formatting | `Starting activity` |
| **time** | Includes timestamp, priority, tag, PID | `01-02 03:04:05.678 I/ActivityManager(12345): Starting activity` |
| **threadtime** | Most detailed - timestamp, PID, TID, priority, tag | `01-02 03:04:05.678 12345 12367 I ActivityManager: Starting activity` |
| **long** | Multi-line format with full metadata | ```[ 01-02 03:04:05.678 12345:12367 I/ActivityManager ]<br>Starting activity``` |

#### Recommended Formats

- **time**: Best for general debugging and log analysis
- **threadtime**: Ideal for performance analysis and threading issues
- **brief**: Good for quick overview and log filtering
- **raw**: Useful when processing logs with external tools

### Logcat Buffer Levels

Android maintains separate log buffers for different system components:

#### Available Buffers

| Buffer | Purpose | Content |
|--------|---------|---------|
| **main** | Default application logs | App-generated logs, system services |
| **system** | System-level logs | Android framework, system processes |
| **radio** | Radio/telephony logs | Cellular, WiFi, Bluetooth communication |
| **events** | System events | Binary format events, performance metrics |
| **crash** | Crash dumps | Native crashes, tombstones |
| **all** | Combined buffer | All buffers merged (can be verbose) |

#### Buffer Selection Guide

**For App Development:**

- Use `main` buffer for general application debugging
- Add `system` for framework-related issues
- Use `crash` when debugging native crashes

**For System Analysis:**

- Use `system` for Android framework debugging
- Use `radio` for connectivity issues
- Use `events` for performance monitoring

**For Comprehensive Debugging:**

- Use `all` to capture everything (warning: high volume)
- Filter by log levels to manage output volume

### Log Levels

Each log entry has a priority level indicating its importance:

| Level | Code | Color | Purpose |
|-------|------|-------|---------|
| **Verbose** | V | Gray | Detailed tracing information |
| **Debug** | D | Green | Debug messages for development |
| **Info** | I | Blue | General information messages |
| **Warning** | W | Yellow | Warning conditions |
| **Error** | E | Orange | Error conditions |
| **Fatal** | F | Red | Critical errors causing crashes |

### Usage Examples

**Real-time Monitoring:**

```bash
# Start capture with time format and main buffer
Format: time, Buffer: main
```

**Performance Analysis:**

```bash
# Use threadtime format to see thread IDs
Format: threadtime, Buffer: main
```

**Network Debugging:**

```bash
# Monitor radio buffer for connectivity issues
Format: time, Buffer: radio
```

**System Debugging:**

```bash
# Monitor system buffer with verbose logging
Format: threadtime, Buffer: system
Level Filter: All levels enabled
```

### Filtering and Search

The logging interface provides powerful filtering options:

- **Level Filtering**: Enable/disable specific log levels
- **PID Filtering**: Show logs from specific process IDs
- **Tag Filtering**: Filter by application or component tags
- **Text Search**: Regex and case-sensitive search
- **Keyword Highlighting**: Highlight important terms

### Export Options

Captured logs can be exported in various formats:

- **Filtered Export**: Export only logs matching current filters
- **Timestamp Options**: Include/exclude timestamps
- **Format Preservation**: Maintain original log formatting

## Project Structure

```text
adb-util/
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── adb-util-env/              # Virtual environment
├── docs/                       # Documentation
│   ├── app_requirement.md      # Feature requirements
│   ├── development_plan.md     # Development roadmap
│   ├── device_discovery_implementation.md  # Device discovery docs
│   ├── logcat.md              # Logcat implementation docs
│   ├── logging_system.md      # Logging architecture
│   └── script_manager.md      # Script management docs
├── sample_scripts/            # Example scripts
│   ├── device/                # Device-side scripts
│   └── host/                  # Host-side scripts
├── src/                       # Source code
│   ├── gui/                   # UI components (PyQt6)
│   │   ├── main_window.py     # Main application window
│   │   ├── device_tab.py      # Device-specific tabs
│   │   ├── file_manager.py    # File operations UI
│   │   ├── terminal.py        # Terminal interface
│   │   ├── logging.py         # Logcat viewer ✅ IMPLEMENTED
│   │   └── utils.py           # Utility functions UI
│   ├── adb/                   # ADB integration layer
│   │   ├── device_manager.py  # Device discovery & management ✅ IMPLEMENTED
│   │   ├── file_operations.py # File push/pull operations
│   │   ├── command_runner.py  # ADB command execution ✅ IMPLEMENTED
│   │   └── logcat_handler.py  # Logcat streaming ✅ IMPLEMENTED
│   ├── services/              # Business logic
│   │   ├── tab_manager.py     # Tab state management
│   │   ├── config_manager.py  # Application configuration
│   │   └── command_storage.py # Saved commands management
│   ├── utils/                 # Helper utilities
│   │   ├── validators.py      # Input validation
│   │   ├── formatters.py      # Text/JSON formatting
│   │   ├── constants.py       # Application constants ✅ IMPLEMENTED
│   │   └── logger.py          # Logging system ✅ IMPLEMENTED
│   └── models/                # Data models
│       ├── device.py          # Device data model ✅ IMPLEMENTED
│       ├── command.py         # Command data model
│       └── tab.py             # Tab data model
└── tests/                     # Test suite ✅ COMPREHENSIVE COVERAGE
    ├── conftest.py            # Test configuration
    ├── test_device_manager.py # Device manager tests ✅
    ├── test_logcat_comprehensive.py # Logcat tests ✅
    └── [25+ additional test files] # Extensive test coverage
```

## Technology Stack

- **Language**: Python 3.9+
- **GUI Framework**: PyQt6 (primary) / PySide6 (alternative)
- **ADB Integration**: python-adb + subprocess
- **Async Operations**: asyncio + qasync
- **File Operations**: pathlib + aiofiles
- **Testing**: pytest + pytest-asyncio + pytest-qt
- **Code Quality**: black, flake8, mypy

## Current Status

### ✅ Implemented Features

- **Core Infrastructure**: Project setup, virtual environment, dependency management
- **Device Discovery**: Complete device management system with real-time monitoring
- **Logcat Collection**: Full-featured logging with filtering, export, and GUI integration
- **Testing Framework**: Comprehensive test suites with 100% pass rate
- **Development Tools**: Code formatting, linting, type checking

### 🚧 In Development

- **File Manager**: Dual-pane browser with drag-and-drop transfers
- **Terminal Interface**: Interactive shell with command history
- **Utilities**: Network info, port forwarding, screenshots

### 📋 Planned Features

- **Advanced File Operations**: External editor integration, JSON formatting
- **Command Management**: Saved commands, categories, auto-completion
- **UI/UX Polish**: Theming, responsive design, keyboard shortcuts

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black src/ tests/
```

### Linting

```bash
flake8 src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone and setup
git clone https://github.com/nitr-himanshu/adb-util.git
cd adb-util

# Create virtual environment
python -m venv adb-util-env
adb-util-env\Scripts\activate  # Windows
# source adb-util-env/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Format code
python -m black src/ tests/ main.py

# Lint code
python -m flake8 src/ tests/ main.py

# Type check
python -m mypy src/
```

## Roadmap

- [x] **Phase 1**: Core infrastructure and project setup
- [x] **Phase 2**: Device management and discovery ✅ **COMPLETED**
- [ ] **Phase 3**: File manager with dual-pane browser
- [ ] **Phase 4**: Interactive terminal with saved commands
- [x] **Phase 5**: Real-time logcat with filtering ✅ **COMPLETED**
- [ ] **Phase 6**: Utility functions and port forwarding
- [ ] **Phase 7**: UI polish and comprehensive testing

### ✅ Recently Completed Features

- **Device Discovery System**: Fully implemented with real-time monitoring, auto-detection of USB and WiFi devices, and comprehensive device property extraction
- **Logcat Collection**: Complete real-time logcat streaming with advanced filtering, multi-format support, export functionality, and GUI integration
- **Async Architecture**: Non-blocking UI operations with proper thread management
- **Comprehensive Testing**: Full test suites for device discovery and logcat functionality

See [Development Plan](docs/development_plan.md) for detailed roadmap.

## Troubleshooting

### Common Issues

#### ADB not found

```bash
# Verify ADB installation
adb version

# Add ADB to PATH or specify path in config
```

#### Device not detected

- Enable USB Debugging in Developer Options
- Check USB cable and try different port
- Verify device authorization prompt

#### Permission denied errors

- Ensure proper device permissions
- Try running with elevated privileges if needed

#### GUI not starting

```bash
# Install GUI dependencies
pip install PyQt6
# or
pip install PySide6
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Android Debug Bridge (ADB) team
- PyQt6/PySide6 developers
- Python asyncio community
- Contributors and testers

## Support

- 📁 [Issues](https://github.com/nitr-himanshu/adb-util/issues)
- 💬 [Discussions](https://github.com/nitr-himanshu/adb-util/discussions)
- 📧 Email: [thehimanshukeshri@gmail.com]

---

Made with ❤️ for Android developers
