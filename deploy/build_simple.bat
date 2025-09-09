@echo off
echo ==============================================
echo ADB-UTIL Simple Executable Builder
echo ==============================================
echo.

REM Set script directory as working directory
cd /d "%~dp0"

echo Activating virtual environment...
if exist "adb-util-env\Scripts\activate.bat" (
    call "adb-util-env\Scripts\activate.bat"
) else (
    echo ERROR: Virtual environment not found at adb-util-env\Scripts\activate.bat
    echo Please ensure virtual environment is created and named 'adb-util-env'
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo.
echo Building executable...
pyinstaller ^
    --onefile ^
    --name adb-util ^
    --paths src ^
    --add-data "src;src" ^
    --hidden-import PyQt6 ^
    --hidden-import PyQt6.QtCore ^
    --hidden-import PyQt6.QtGui ^
    --hidden-import PyQt6.QtWidgets ^
    --hidden-import qasync ^
    --hidden-import aiofiles ^
    --hidden-import psutil ^
    --hidden-import watchdog ^
    --collect-all PyQt6 ^
    --noconsole ^
    main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo Build failed! Trying with console mode...
    pyinstaller ^
        --onefile ^
        --name adb-util ^
        --paths src ^
        --add-data "src;src" ^
        --hidden-import PyQt6 ^
        --hidden-import PyQt6.QtCore ^
        --hidden-import PyQt6.QtGui ^
        --hidden-import PyQt6.QtWidgets ^
        --hidden-import qasync ^
        --collect-all PyQt6 ^
        main.py
)

echo.
if exist "dist\adb-util.exe" (
    echo ✓ Build successful! 
    echo Executable location: dist\adb-util.exe
    dir "dist\adb-util.exe"
) else (
    echo ✗ Build failed! Executable not found.
    if exist "dist" (
        echo Contents of dist folder:
        dir dist
    )
)

echo.
pause
