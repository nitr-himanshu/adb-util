# ADB-UTIL System Requirements

This document outlines the system requirements for running ADB-UTIL.

## Prerequisites

### Android Debug Bridge (ADB)

ADB-UTIL requires the Android Debug Bridge (ADB) tool to be installed on your system. The application uses subprocess calls to interact with the system `adb` binary.

#### Windows Installation:
1. Download Android Platform Tools from: https://developer.android.com/studio/releases/platform-tools
2. Extract to a folder (e.g., `C:\adb\`)
3. Add the folder to your system PATH environment variable
4. Test: Open Command Prompt and run `adb version`

#### Linux Installation:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install android-tools-adb

# Fedora
sudo dnf install android-tools

# Arch Linux
sudo pacman -S android-tools
```

#### macOS Installation:
```bash
# Using Homebrew
brew install android-platform-tools

# Or download from Google's website (same as Windows)
```

### Python Dependencies

The Python dependencies are listed in `requirements.txt` and will be installed automatically during the build process or when setting up the development environment.

## Verification

To verify ADB is properly installed:

```bash
# Check ADB version
adb version

# List connected devices
adb devices
```

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd adb-util
   ```

2. **Create virtual environment**
   ```bash
   python -m venv adb-util-env
   
   # Windows
   adb-util-env\Scripts\activate
   
   # Linux/macOS
   source adb-util-env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**
   ```bash
   python main.py
   ```

## Distribution

The built executables include all Python dependencies but **do not include ADB tools**. Users must install ADB tools separately on their systems.

### For End Users:

1. **Install ADB tools** (see installation instructions above)
2. **Download and run ADB-UTIL executable**
   - Windows: `adb-util.exe`
   - Linux: `./adb-util`

The application will detect if ADB is available and show appropriate error messages if not found.
