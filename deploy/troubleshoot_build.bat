@echo off
echo ==============================================
echo ADB-UTIL Build Troubleshooter
echo ==============================================
echo.

cd /d "%~dp0"

echo Checking environment...
echo.

echo 1. Checking Python installation...
python --version
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found in PATH!
    echo Please install Python and add it to PATH
    pause
    exit /b 1
)

echo.
echo 2. Checking virtual environment...
if exist "adb-util-env\Scripts\python.exe" (
    echo ✓ Virtual environment found
    call "adb-util-env\Scripts\activate.bat"
    echo Active Python: 
    where python
    python --version
) else (
    echo ✗ Virtual environment not found
    echo Creating virtual environment...
    python -m venv adb-util-env
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    call "adb-util-env\Scripts\activate.bat"
)

echo.
echo 3. Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo 4. Checking project structure...
if exist "src\utils\logger.py" (
    echo ✓ src\utils\logger.py found
) else (
    echo ✗ src\utils\logger.py not found
    echo Checking src directory contents:
    if exist "src" (
        dir src /b
    ) else (
        echo ERROR: src directory not found!
    )
)

if exist "src\gui\main_window.py" (
    echo ✓ src\gui\main_window.py found
) else (
    echo ✗ src\gui\main_window.py not found
)

echo.
echo 5. Testing imports...
python -c "
import sys
from pathlib import Path
src_path = Path('.') / 'src'
sys.path.insert(0, str(src_path))

try:
    from utils.logger import get_logger
    print('✓ utils.logger import successful')
except ImportError as e:
    print(f'✗ utils.logger import failed: {e}')
    
try:
    from gui.main_window import MainWindow
    print('✓ gui.main_window import successful')
except ImportError as e:
    print(f'✗ gui.main_window import failed: {e}')

try:
    from PyQt6.QtWidgets import QApplication
    print('✓ PyQt6 import successful')
except ImportError as e:
    print(f'✗ PyQt6 import failed: {e}')
"

echo.
echo 6. Building with verbose output...
echo.
echo Choose build method:
echo [1] Enhanced build (recommended)
echo [2] Simple build
echo [3] Debug build (with console)
echo [4] Manual PyInstaller
echo.
set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto enhanced
if "%choice%"=="2" goto simple  
if "%choice%"=="3" goto debug
if "%choice%"=="4" goto manual
goto enhanced

:enhanced
echo Running enhanced build...
call build_exe.bat
goto end

:simple
echo Running simple build...
call build_simple.bat
goto end

:debug
echo Running debug build...
pyinstaller --onefile --name adb-util-debug --paths src --add-data "src;src" --hidden-import PyQt6 --console main.py
goto end

:manual
echo Running manual PyInstaller...
echo Enter your custom PyInstaller command or press Enter for default:
set /p manual_cmd=""
if "%manual_cmd%"=="" (
    pyinstaller --onefile --name adb-util --paths src --add-data "src;src" main.py
) else (
    %manual_cmd%
)

:end
echo.
echo Build attempt completed.
echo.
if exist "dist\adb-util.exe" (
    echo ✓ Executable found: dist\adb-util.exe
    echo Testing executable...
    cd dist
    echo Testing basic execution...
    adb-util.exe --version 2>nul
    if %ERRORLEVEL% equ 0 (
        echo ✓ Executable runs successfully!
    ) else (
        echo ⚠ Executable may have issues - check dependencies
    )
    cd ..
) else if exist "dist\adb-util-debug.exe" (
    echo ✓ Debug executable found: dist\adb-util-debug.exe
) else (
    echo ✗ No executable found
    echo.
    echo Troubleshooting tips:
    echo 1. Check if all dependencies are installed
    echo 2. Verify src directory structure
    echo 3. Try the debug build option
    echo 4. Check PyInstaller output for specific errors
)

echo.
pause
