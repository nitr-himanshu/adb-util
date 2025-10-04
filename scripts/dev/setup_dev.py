#!/usr/bin/env python3
"""
Development Environment Setup Script for ADB-UTIL

This script automates the setup of the development environment for the ADB-UTIL project.
It handles virtual environment creation, dependency installation, and development tools setup.

Usage:
    python scripts/dev/setup_dev.py [options]

Options:
    --force          Force recreation of virtual environment
    --no-dev         Skip development dependencies
    --no-pre-commit  Skip pre-commit hooks installation
    --help           Show this help message
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent.absolute()


def get_venv_path():
    """Get the virtual environment path."""
    return get_project_root() / ".venv"


def get_activate_script():
    """Get the appropriate activation script for the current platform."""
    venv_path = get_venv_path()
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "activate.bat"
    else:
        return venv_path / "bin" / "activate"


def get_python_executable():
    """Get the Python executable path in the virtual environment."""
    venv_path = get_venv_path()
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def get_pip_executable():
    """Get the pip executable path in the virtual environment."""
    venv_path = get_venv_path()
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd or get_project_root(), 
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"Error: {result.stderr}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        raise


def check_python_version():
    """Check if Python version meets requirements."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"Error: Python 3.9+ is required, but found {version.major}.{version.minor}")
        sys.exit(1)
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")


def create_virtual_environment(force=False):
    """Create or recreate the virtual environment."""
    venv_path = get_venv_path()
    
    if venv_path.exists():
        if force:
            print(f"Removing existing virtual environment at {venv_path}")
            import shutil
            shutil.rmtree(venv_path)
        else:
            print(f"✓ Virtual environment already exists at {venv_path}")
            return
    
    print(f"Creating virtual environment at {venv_path}")
    run_command([sys.executable, "-m", "venv", str(venv_path)])
    print("✓ Virtual environment created successfully")


def upgrade_pip():
    """Upgrade pip in the virtual environment."""
    print("Upgrading pip...")
    pip_exe = get_pip_executable()
    run_command([str(pip_exe), "install", "--upgrade", "pip"])
    print("✓ pip upgraded successfully")


def install_dependencies(dev=True):
    """Install project dependencies."""
    pip_exe = get_pip_executable()
    project_root = get_project_root()
    
    if dev:
        print("Installing development dependencies...")
        run_command([str(pip_exe), "install", "-e", "."])
        print("✓ Development dependencies installed successfully")
    else:
        print("Installing base dependencies...")
        run_command([str(pip_exe), "install", "-r", "requirements/base.txt"])
        print("✓ Base dependencies installed successfully")


def install_precommit_hooks():
    """Install and setup pre-commit hooks."""
    pip_exe = get_pip_executable()
    python_exe = get_python_executable()
    
    print("Installing pre-commit...")
    run_command([str(pip_exe), "install", "pre-commit"])
    
    print("Installing pre-commit hooks...")
    run_command([str(python_exe), "-m", "pre_commit", "install"])
    print("✓ Pre-commit hooks installed successfully")


def verify_installation():
    """Verify that the installation was successful."""
    python_exe = get_python_executable()
    
    print("Verifying installation...")
    
    # Test importing main modules
    try:
        result = run_command([str(python_exe), "-c", "import sys; sys.path.insert(0, '.'); import main; print('✓ Main module imports successfully')"])
    except subprocess.CalledProcessError:
        print("✗ Failed to import main module")
        return False
    
    # Test if adb-util script is available
    try:
        if platform.system() == "Windows":
            script_path = get_venv_path() / "Scripts" / "adb-util.exe"
        else:
            script_path = get_venv_path() / "bin" / "adb-util"
        
        if script_path.exists():
            print("✓ adb-util script is available")
        else:
            print("! adb-util script not found (this may be normal)")
    except Exception as e:
        print(f"! Could not verify script: {e}")
    
    print("✓ Installation verification completed")
    return True


def print_activation_instructions():
    """Print instructions for activating the virtual environment."""
    activate_script = get_activate_script()
    
    print("\n" + "="*60)
    print("🎉 Development environment setup completed!")
    print("="*60)
    print("\nTo activate the virtual environment:")
    
    if platform.system() == "Windows":
        print(f"  {activate_script}")
        print("  # Or in PowerShell:")
        print(f"  {activate_script.replace('.bat', '.ps1')}")
    else:
        print(f"  source {activate_script}")
    
    print("\nTo run the application:")
    print("  adb-util")
    print("  # Or directly:")
    print("  python main.py")
    
    print("\nTo run tests:")
    print("  pytest tests/ -v")
    
    print("\nTo format code:")
    print("  black src/ tests/ main.py")
    
    print("\nTo lint code:")
    print("  flake8 src/ tests/ main.py")
    
    print("\nHappy coding! 🚀")


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(
        description="Setup development environment for ADB-UTIL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force recreation of virtual environment"
    )
    parser.add_argument(
        "--no-dev", 
        action="store_true", 
        help="Skip development dependencies"
    )
    parser.add_argument(
        "--no-pre-commit", 
        action="store_true", 
        help="Skip pre-commit hooks installation"
    )
    
    args = parser.parse_args()
    
    print("ADB-UTIL Development Environment Setup")
    print("="*40)
    
    try:
        # Check Python version
        check_python_version()
        
        # Create virtual environment
        create_virtual_environment(force=args.force)
        
        # Upgrade pip
        upgrade_pip()
        
        # Install dependencies
        install_dependencies(dev=not args.no_dev)
        
        # Install pre-commit hooks (optional)
        if not args.no_pre_commit:
            try:
                install_precommit_hooks()
            except subprocess.CalledProcessError:
                print("! Pre-commit installation failed (continuing without it)")
        
        # Verify installation
        if verify_installation():
            print_activation_instructions()
        else:
            print("! Installation verification failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
