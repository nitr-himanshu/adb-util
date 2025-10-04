#!/bin/bash
#
# ADB-UTIL Linux Build Script for Ubuntu 22.04+
# This script builds a standalone executable for Linux systems
#

set -e  # Exit on any error

echo "=============================================="
echo "ADB-UTIL Linux Executable Builder"
echo "=============================================="
echo

# Set script directory as working directory
cd "$(dirname "$0")"

# Check if we're in the deploy directory and adjust path
if [[ $(basename "$PWD") == "deploy" ]]; then
    cd ..
fi

echo "Working directory: $PWD"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
echo "Checking system requirements..."

if ! command_exists python3; then
    echo "ERROR: Python 3 is not installed"
    echo "Install with: sudo apt-get install python3 python3-pip python3-venv"
    exit 1
fi

if ! command_exists pip3; then
    echo "ERROR: pip3 is not installed"
    echo "Install with: sudo apt-get install python3-pip"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $PYTHON_VERSION"

if [[ $(echo "$PYTHON_VERSION < 3.9" | bc -l) -eq 1 ]]; then
    echo "WARNING: Python 3.9+ is recommended for best compatibility"
fi

# Install system dependencies
echo
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-venv \
    build-essential \
    qt6-base-dev \
    qt6-tools-dev \
    qt6-tools-dev-tools \
    libgl1-mesa-dev \
    libglib2.0-dev \
    libfontconfig1-dev \
    libdbus-1-dev \
    libxkbcommon-dev \
    libxkbcommon-x11-dev \
    libxcb-xinerama0-dev \
    libxcb-cursor0 \
    android-tools-adb \
    bc

# Create virtual environment if it doesn't exist
VENV_DIR="adb-util-env"
if [ ! -d "$VENV_DIR" ]; then
    echo
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip and install dependencies
echo
echo "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Clean previous builds
echo
echo "Cleaning previous builds..."
if [ -d "dist" ]; then
    rm -rf dist
fi
if [ -d "build" ]; then
    rm -rf build
fi
if [ -f "adb-util.spec" ]; then
    rm -f adb-util.spec
fi

# Set environment variables for Qt
export QT_QPA_PLATFORM_PLUGIN_PATH="/usr/lib/x86_64-linux-gnu/qt6/plugins"
export QT_PLUGIN_PATH="/usr/lib/x86_64-linux-gnu/qt6/plugins"

echo
echo "Building executable..."
pyinstaller \
    --onefile \
    --name adb-util \
    --paths src \
    --add-data "src:src" \
    --hidden-import PyQt6 \
    --hidden-import PyQt6.QtCore \
    --hidden-import PyQt6.QtGui \
    --hidden-import PyQt6.QtWidgets \
    --hidden-import qasync \
    --hidden-import aiofiles \
    --hidden-import psutil \
    --hidden-import watchdog \
    --collect-all PyQt6 \
    --exclude-module matplotlib \
    --exclude-module numpy \
    --exclude-module pandas \
    --exclude-module PIL \
    --exclude-module tkinter \
    --strip \
    main.py

echo
if [ -f "dist/adb-util" ]; then
    echo "✓ Build successful!"
    echo "Executable location: dist/adb-util"
    
    # Make executable
    chmod +x "dist/adb-util"
    
    # Create checksum
    cd dist
    sha256sum adb-util > adb-util.sha256
    cd ..
    
    # Show file info
    ls -lh dist/adb-util
    echo
    echo "SHA256: $(cat dist/adb-util.sha256)"
    
    # Test if the executable can be run
    echo
    echo "Testing executable..."
    if ./dist/adb-util --help 2>/dev/null; then
        echo "✓ Executable test passed"
    else
        echo "⚠ Executable test failed, but file was created"
        echo "You may need to install additional Qt6 dependencies:"
        echo "sudo apt-get install qt6-base-dev qt6-tools-dev"
    fi
    
    # Create release package
    echo
    echo "Creating release package..."
    mkdir -p release
    cp dist/adb-util release/
    cp dist/adb-util.sha256 release/
    cp README.md release/ 2>/dev/null || echo "README.md not found"
    cp LICENSE release/ 2>/dev/null || echo "LICENSE not found"
    
    cat > release/README-Linux.txt << EOF
ADB-UTIL for Linux (Ubuntu 22.04+)

Installation:
1. Make sure you have Qt6 installed:
   sudo apt-get update
   sudo apt-get install qt6-base-dev android-tools-adb

2. Make the executable runnable:
   chmod +x adb-util

3. Run the application:
   ./adb-util

Requirements:
- Ubuntu 22.04+ or compatible Linux distribution
- Qt6 libraries
- ADB tools (android-tools-adb package)

SHA256 Checksum:
$(cat dist/adb-util.sha256)

For issues, please check the project repository.
EOF
    
    # Create tarball
    cd release
    tar -czf ../adb-util-linux.tar.gz *
    cd ..
    
    echo "✓ Release package created: adb-util-linux.tar.gz"
    
else
    echo "✗ Build failed! Executable not found."
    if [ -d "dist" ]; then
        echo "Contents of dist folder:"
        ls -la dist/
    fi
    exit 1
fi

echo
echo "Build completed successfully!"
echo "To run: ./dist/adb-util"
echo "Package: adb-util-linux.tar.gz"
