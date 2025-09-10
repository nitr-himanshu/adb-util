#!/bin/bash
#
# ADB-UTIL Installation Script for Linux
# This script helps install ADB-UTIL and its dependencies
#

set -e

echo "=============================================="
echo "ADB-UTIL Installation Script for Linux"
echo "=============================================="
echo

# Detect distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    VERSION=$VERSION_ID
else
    echo "Cannot detect Linux distribution"
    exit 1
fi

echo "Detected: $PRETTY_NAME"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please do not run this script as root"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install dependencies based on distribution
install_dependencies() {
    case $DISTRO in
        ubuntu|debian)
            echo "Installing dependencies for Ubuntu/Debian..."
            sudo apt-get update
            sudo apt-get install -y \
                python3 \
                python3-pip \
                python3-venv \
                qt6-base-dev \
                qt6-tools-dev \
                libgl1-mesa-dev \
                libxcb-cursor0 \
                android-tools-adb
            ;;
        fedora)
            echo "Installing dependencies for Fedora..."
            sudo dnf install -y \
                python3 \
                python3-pip \
                qt6-qtbase-devel \
                qt6-qttools-devel \
                mesa-libGL-devel \
                android-tools
            ;;
        arch|manjaro)
            echo "Installing dependencies for Arch Linux..."
            sudo pacman -S --needed \
                python \
                python-pip \
                qt6-base \
                qt6-tools \
                mesa \
                android-tools
            ;;
        *)
            echo "Unsupported distribution: $DISTRO"
            echo "Please install these packages manually:"
            echo "- Python 3.9+"
            echo "- Qt6 development libraries"
            echo "- OpenGL libraries"
            echo "- Android ADB tools"
            exit 1
            ;;
    esac
}

# Main installation
main() {
    echo "Starting installation..."
    
    # Install system dependencies
    install_dependencies
    
    # Check if adb-util executable exists
    if [ ! -f "adb-util" ]; then
        echo "ERROR: adb-util executable not found in current directory"
        echo "Please extract the adb-util-linux.tar.gz file first"
        exit 1
    fi
    
    # Make executable
    chmod +x adb-util
    
    # Verify checksum if available
    if [ -f "adb-util.sha256" ]; then
        echo "Verifying checksum..."
        if sha256sum -c adb-util.sha256; then
            echo "✓ Checksum verification passed"
        else
            echo "⚠ Checksum verification failed"
            echo "The file may be corrupted or tampered with"
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
    
    # Test if the executable works
    echo "Testing executable..."
    if ./adb-util --help >/dev/null 2>&1; then
        echo "✓ Installation successful!"
    else
        echo "⚠ Installation completed but executable test failed"
        echo "You may need to install additional Qt6 runtime libraries"
    fi
    
    # Offer to install to system path
    echo
    read -p "Install to /usr/local/bin for system-wide access? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo cp adb-util /usr/local/bin/
        sudo chmod +x /usr/local/bin/adb-util
        echo "✓ Installed to /usr/local/bin/adb-util"
        echo "You can now run 'adb-util' from anywhere"
    else
        echo "To run: ./adb-util"
    fi
    
    echo
    echo "Installation completed!"
    echo
    echo "Usage:"
    echo "  ./adb-util              # Run from current directory"
    echo "  adb-util                # If installed system-wide"
    echo
}

# Run main function
main "$@"
