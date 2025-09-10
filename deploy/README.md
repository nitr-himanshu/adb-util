# ADB-UTIL Build & Deployment Guide

This directory contains scripts and configurations for building ADB-UTIL executables for different platforms.

## Files Overview

### Build Scripts
- `build_simple.bat` - Windows executable builder
- `build_linux.sh` - Linux executable builder (Ubuntu 22.04+)

### Installation Scripts
- `install_windows.bat` - Windows installation helper
- `install_linux.sh` - Linux installation helper

### GitHub Actions
- `../.github/workflows/main.yml` - Automated CI/CD pipeline

## Building Locally

### Windows

1. **Prerequisites:**
   ```cmd
   # Install Python 3.11+
   # Create virtual environment
   python -m venv adb-util-env
   adb-util-env\Scripts\activate.bat
   ```

2. **Build:**
   ```cmd
   cd deploy
   build_simple.bat
   ```

3. **Output:** `dist/adb-util.exe` and release package in `release/` folder

### Linux (Ubuntu 22.04+)

1. **Prerequisites:**
   ```bash
   # Make script executable
   chmod +x deploy/build_linux.sh
   
   # The script will install system dependencies
   ```

2. **Build:**
   ```bash
   cd deploy
   ./build_linux.sh
   ```

3. **Output:** `dist/adb-util` and release package `adb-util-linux.tar.gz`

## Antivirus False Positives

### Why it happens:
- PyInstaller bundles Python runtime with the executable
- Antivirus software may flag this as suspicious behavior
- No actual malware is present

### Solutions implemented:
1. **Version Information:** Added Windows version info to reduce false positives
2. **Code Signing:** SHA256 checksums for verification
3. **Exclusions:** Excluded unnecessary modules to reduce size
4. **Metadata:** Proper executable metadata and descriptions

### For users:
- Verify SHA256 checksums provided with releases
- Add antivirus exceptions if needed
- Use Windows Defender "Run anyway" option if prompted

## GitHub Actions Workflow

The automated build process:

1. **Triggers:**
   - On tag push (`v*`)
   - Manual workflow dispatch

2. **Builds:**
   - Windows executable (windows-latest)
   - Linux executable (ubuntu-22.04)

3. **Features:**
   - Dependency caching
   - Multi-platform builds
   - Checksum generation
   - Release packaging
   - Automatic GitHub releases

4. **Outputs:**
   - `adb-util-windows.zip` - Windows package
   - `adb-util-linux.tar.gz` - Linux package

## Release Process

### Automated (Recommended)

1. **Create and push a tag:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **GitHub Actions will:**
   - Build for both platforms
   - Create release packages
   - Generate checksums
   - Create GitHub release
   - Upload artifacts

### Manual

1. **Build locally using the scripts above**
2. **Create release packages:**
   - Windows: ZIP file with exe, checksums, and documentation
   - Linux: TAR.GZ file with binary, checksums, and documentation

## Installation for End Users

### Windows
1. Download `adb-util-windows.zip`
2. Extract to desired location
3. Run `install_windows.bat` (optional)
4. Execute `adb-util.exe`

### Linux
1. Download `adb-util-linux.tar.gz`
2. Extract: `tar -xzf adb-util-linux.tar.gz`
3. Run `./install_linux.sh` (optional)
4. Execute `./adb-util`

## Troubleshooting

### Windows Issues
- **Antivirus blocking:** Add exception or use "Run anyway"
- **Missing dependencies:** Install Visual C++ Redistributables
- **Admin required:** Some ADB operations need elevation

### Linux Issues
- **Qt6 missing:** Install `qt6-base-dev` package
- **ADB missing:** Install `android-tools-adb` package
- **Permission denied:** Run `chmod +x adb-util`

### Build Issues
- **Python version:** Use Python 3.9+ for best compatibility
- **Dependencies:** Ensure all requirements.txt packages are installed
- **Virtual environment:** Always use a clean virtual environment

## Security Notes

1. **Checksums:** Always verify SHA256 checksums
2. **Source:** Only download from official GitHub releases
3. **Antivirus:** False positives are common with PyInstaller
4. **Permissions:** Application may request admin rights for ADB operations

## Development

### Testing Builds
```bash
# Test Windows build
dist/adb-util.exe --help

# Test Linux build
./dist/adb-util --help
```

### Debugging
- Use console mode builds for error messages
- Check PyInstaller logs in `build/` directory
- Verify all dependencies are included

## Contributing

When modifying build scripts:
1. Test on target platforms
2. Update this documentation
3. Verify antivirus compatibility
4. Test automated workflow
