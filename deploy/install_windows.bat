@echo off
REM ADB-UTIL Installation Script for Windows
REM This script helps verify and set up ADB-UTIL

echo ==============================================
echo ADB-UTIL Installation Script for Windows
echo ==============================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges
) else (
    echo WARNING: Not running as administrator
    echo Some ADB operations may require administrator privileges
    echo.
)

REM Check if adb-util.exe exists
if not exist "adb-util.exe" (
    echo ERROR: adb-util.exe not found in current directory
    echo Please extract the adb-util-windows.zip file first
    pause
    exit /b 1
)

echo Found: adb-util.exe
echo.

REM Verify checksum if available
if exist "adb-util.exe.sha256" (
    echo Verifying checksum...
    certutil -hashfile "adb-util.exe" SHA256 > temp_hash.txt
    fc /b "adb-util.exe.sha256" "temp_hash.txt" >nul 2>&1
    if %errorLevel% == 0 (
        echo ✓ Checksum verification passed
    ) else (
        echo ⚠ Checksum verification failed
        echo The file may be corrupted or tampered with
        set /p choice="Continue anyway? (y/N): "
        if /i not "%choice%"=="y" (
            del temp_hash.txt 2>nul
            exit /b 1
        )
    )
    del temp_hash.txt 2>nul
    echo.
)

REM Check Windows version
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
echo Windows version: %VERSION%
echo.

REM Test if the executable works
echo Testing executable...
"adb-util.exe" --help >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Executable test passed
) else (
    echo ⚠ Executable test failed
    echo This may be due to:
    echo   - Missing Visual C++ Redistributables
    echo   - Antivirus blocking the executable
    echo   - Windows Defender SmartScreen
    echo.
    echo If Windows shows a security warning:
    echo   1. Click "More info"
    echo   2. Click "Run anyway"
    echo.
)

REM Check for ADB in PATH
where adb >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ ADB found in system PATH
    adb version
) else (
    echo ⚠ ADB not found in system PATH
    echo Please install Android SDK Platform Tools:
    echo https://developer.android.com/studio/releases/platform-tools
)

echo.
set /p choice="Add ADB-UTIL to system PATH? (y/N): "
if /i "%choice%"=="y" (
    setx PATH "%PATH%;%CD%" /M >nul 2>&1
    if %errorLevel% == 0 (
        echo ✓ Added to system PATH
        echo Restart your command prompt to use 'adb-util' command
    ) else (
        echo ⚠ Failed to add to system PATH
        echo Try running as administrator or add manually:
        echo   %CD%
    )
)

echo.
echo Installation completed!
echo.
echo Usage:
echo   adb-util.exe            # Run from current directory
echo   adb-util                # If added to PATH
echo.
echo If you encounter antivirus warnings:
echo   - This is a false positive common with PyInstaller executables
echo   - The SHA256 checksum can verify file integrity
echo   - Add exception to your antivirus if needed
echo.

REM Offer to create desktop shortcut
set /p choice="Create desktop shortcut? (y/N): "
if /i "%choice%"=="y" (
    set "desktop=%USERPROFILE%\Desktop"
    set "shortcut=%desktop%\ADB-UTIL.lnk"
    
    powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%shortcut%'); $Shortcut.TargetPath = '%CD%\adb-util.exe'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.Description = 'Android Debug Bridge Utility'; $Shortcut.Save()"
    
    if exist "%shortcut%" (
        echo ✓ Desktop shortcut created
    ) else (
        echo ⚠ Failed to create desktop shortcut
    )
)

echo.
pause
