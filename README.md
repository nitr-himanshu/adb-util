# ADB-UTIL

A comprehensive Python-based desktop application for Android Debug Bridge (ADB) operations with a modern GUI interface.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

## Features

### 🔌 Device Management

- **Auto-discovery** of connected ADB devices (USB & WiFi)
- **Real-time monitoring** of device connection status
- **Multi-device support** with tabbed interface
- **Device information** display (model, Android version, etc.)

### 📁 File Manager

- **Dual-pane file browser** (local ↔ device)
- **Drag & drop** file transfers with progress indicators
- **File operations**: Push, Pull, Delete, Move, Copy
- **Built-in text editor** with JSON formatting
- **Syntax highlighting** for various file types

### 💻 Terminal

- **Interactive ADB shell** with command history
- **Save and organize** frequently used commands
- **Command categories** and quick execution
- **Auto-completion** and output formatting

### 📊 Logging

- **Real-time logcat streaming** with filtering
- **Log level filtering** (Verbose, Debug, Info, Warning, Error)
- **Package/tag filtering** and regex search
- **Export logs** to file for analysis

### 🛠️ Utilities

- **WiFi status** and IP address display
- **One-click port forwarding** setup
- **Device screenshots** and system information
- **Battery monitoring** and network diagnostics

## Installation

### Prerequisites

- Python 3.9 or higher
- ADB (Android Debug Bridge) installed and accessible
- PyQt6 or PySide6

### Quick Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/nitr-himanshu/adb-util.git
   cd adb-util
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**

   ```bash
   python main.py
   ```

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

## Usage

### Getting Started

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

## Project Structure

```text
adb-util/
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── docs/                       # Documentation
│   ├── app_requirement.md      # Feature requirements
│   └── development_plan.md     # Development roadmap
├── src/                        # Source code
│   ├── gui/                    # UI components (PyQt6)
│   │   ├── main_window.py      # Main application window
│   │   ├── device_tab.py       # Device-specific tabs
│   │   ├── file_manager.py     # File operations UI
│   │   ├── terminal.py         # Terminal interface
│   │   ├── logging.py          # Logcat viewer
│   │   └── utils.py            # Utility functions UI
│   ├── adb/                    # ADB integration layer
│   │   ├── device_manager.py   # Device discovery & management
│   │   ├── file_operations.py  # File push/pull operations
│   │   ├── command_runner.py   # ADB command execution
│   │   └── logcat_handler.py   # Logcat streaming
│   ├── services/               # Business logic
│   │   ├── tab_manager.py      # Tab state management
│   │   ├── config_manager.py   # Application configuration
│   │   └── command_storage.py  # Saved commands management
│   ├── utils/                  # Helper utilities
│   │   ├── validators.py       # Input validation
│   │   ├── formatters.py       # Text/JSON formatting
│   │   └── constants.py        # Application constants
│   └── models/                 # Data models
│       ├── device.py           # Device data model
│       ├── command.py          # Command data model
│       └── tab.py              # Tab data model
└── tests/                      # Test suite
    ├── conftest.py            # Test configuration
    ├── test_device_manager.py # Device manager tests
    └── test_file_operations.py# File operations tests
```

## Technology Stack

- **Language**: Python 3.9+
- **GUI Framework**: PyQt6/PySide6
- **ADB Integration**: python-adb + subprocess
- **Async Operations**: asyncio
- **File Operations**: pathlib + aiofiles
- **Testing**: pytest

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
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks (optional)
pre-commit install
```

## Roadmap

- [x] **Phase 1**: Core infrastructure and project setup
- [ ] **Phase 2**: Device management and discovery
- [ ] **Phase 3**: File manager with dual-pane browser
- [ ] **Phase 4**: Interactive terminal with saved commands
- [ ] **Phase 5**: Real-time logcat with filtering
- [ ] **Phase 6**: Utility functions and port forwarding
- [ ] **Phase 7**: UI polish and comprehensive testing

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
