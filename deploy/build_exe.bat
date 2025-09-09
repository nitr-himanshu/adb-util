@echo off
echo ==============================================
echo ADB-UTIL Executable Builder
echo ==============================================
echo.

REM Set script directory as working directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "adb-util-env\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please create virtual environment first:
    echo python -m venv adb-util-env
    pause
    exit /b 1
)

echo Activating virtual environment...
call "adb-util-env\Scripts\activate.bat"

echo.
echo Installing/updating dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo Cleaning previous build...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"

echo.
echo Building executable with PyInstaller...
echo Using enhanced configuration for proper dependency inclusion...

REM Create enhanced spec file with proper path handling
python -c "
import os
from pathlib import Path

spec_content = '''# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

# Get the project root directory
project_root = Path(SPECPATH)
src_path = project_root / 'src'

# Add all Python files from src directory
def get_all_python_files(directory):
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

# Analysis configuration
a = Analysis(
    ['main.py'],
    pathex=[str(project_root), str(src_path)],
    binaries=[],
    datas=[
        # Include all source files as data
        (str(src_path), 'src'),
    ],
    hiddenimports=[
        # Explicitly include all our modules
        'src.utils.logger',
        'src.gui.main_window',
        'src.services',
        'src.models',
        'src.adb',
        # PyQt6 modules
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        # Other dependencies
        'qasync',
        'aiofiles',
        'psutil',
        'watchdog',
        'adb_shell',
        'libusb1',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
    ],
    noarchive=False,
    optimize=0,
)

# Filter out unnecessary files
a.datas = [x for x in a.datas if not x[0].endswith(('.pyc', '.pyo'))]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='adb-util',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path if you have one
)
'''

with open('adb-util-enhanced.spec', 'w', encoding='utf-8') as f:
    f.write(spec_content)
    
print('Enhanced spec file created successfully!')
"

if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to create spec file!
    pause
    exit /b 1
)

echo.
echo Running PyInstaller with enhanced configuration...
pyinstaller --clean --noconfirm adb-util-enhanced.spec

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: PyInstaller build failed!
    echo.
    echo Trying alternative build method...
    echo.
    
    REM Alternative build command with more explicit options
    pyinstaller ^
        --onefile ^
        --name adb-util ^
        --paths src ^
        --add-data "src;src" ^
        --hidden-import src.utils.logger ^
        --hidden-import src.gui.main_window ^
        --hidden-import PyQt6.QtCore ^
        --hidden-import PyQt6.QtGui ^
        --hidden-import PyQt6.QtWidgets ^
        --hidden-import qasync ^
        --hidden-import aiofiles ^
        --hidden-import psutil ^
        --hidden-import watchdog ^
        --exclude-module tkinter ^
        --exclude-module matplotlib ^
        --exclude-module numpy ^
        --noconsole ^
        main.py
        
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Alternative build method also failed!
        pause
        exit /b 1
    )
)

echo.
echo ==============================================
echo Build completed successfully!
echo ==============================================
echo.

if exist "dist\adb-util.exe" (
    echo Executable created: dist\adb-util.exe
    echo File size:
    dir "dist\adb-util.exe" | find "adb-util.exe"
    echo.
    echo Testing executable...
    echo.
    cd dist
    adb-util.exe --help 2>nul
    if %ERRORLEVEL% equ 0 (
        echo ✓ Executable runs successfully!
    ) else (
        echo ⚠ Executable created but may have runtime issues
        echo   Check dependencies and try running manually
    )
    cd ..
) else (
    echo ERROR: Executable not found in dist directory!
    if exist "dist" (
        echo Contents of dist directory:
        dir dist
    )
    pause
    exit /b 1
)

echo.
echo Cleaning up temporary files...
if exist "adb-util-enhanced.spec" del "adb-util-enhanced.spec"
if exist "build" rmdir /s /q "build" 2>nul

echo.
echo ==============================================
echo Build process completed!
echo ==============================================
echo.
echo Your executable is ready at: dist\adb-util.exe
echo.
echo You can now:
echo 1. Test the executable: dist\adb-util.exe
echo 2. Distribute the single file: dist\adb-util.exe
echo.

pause
