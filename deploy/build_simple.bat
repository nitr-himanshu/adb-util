@echo off
echo ==============================================
echo ADB-UTIL Simple Executable Builder
echo ==============================================
echo.

REM Set script directory as working directory
cd /d "%~dp0"

REM Check if we're in the deploy directory and adjust path
if "%CD:~-6%" == "deploy" (
    cd ..
)

echo Working directory: %CD%

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
echo Creating version info file...
(
echo VSVersionInfo^(
echo   ffi=FixedFileInfo^(
echo     filevers=^(1, 0, 0, 0^),
echo     prodvers=^(1, 0, 0, 0^),
echo     mask=0x3f,
echo     flags=0x0,
echo     OS=0x4,
echo     fileType=0x1,
echo     subtype=0x0,
echo     date=^(0, 0^)
echo   ^),
echo   kids=[
echo     StringFileInfo^([
echo       StringTable^(
echo         u"040904B0",
echo         [StringStruct^(u"CompanyName", u"ADB-UTIL Project"^),
echo          StringStruct^(u"FileDescription", u"Android Debug Bridge Utility"^),
echo          StringStruct^(u"FileVersion", u"1.0.0.0"^),
echo          StringStruct^(u"InternalName", u"adb-util"^),
echo          StringStruct^(u"LegalCopyright", u"MIT License"^),
echo          StringStruct^(u"OriginalFilename", u"adb-util.exe"^),
echo          StringStruct^(u"ProductName", u"ADB-UTIL"^),
echo          StringStruct^(u"ProductVersion", u"1.0.0.0"^)]^)
echo     ]^),
echo     VarFileInfo^([VarStruct^(u"Translation", [1033, 1200]^)]^)
echo   ]
echo ^)
) > version_info.py

echo.
echo Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "adb-util.spec" del "adb-util.spec"

echo.
echo Building executable with enhanced security settings...
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
    --version-file version_info.py ^
    --exclude-module matplotlib ^
    --exclude-module numpy ^
    --exclude-module pandas ^
    --exclude-module PIL ^
    --exclude-module tkinter ^
    --exclude-module scipy ^
    --exclude-module IPython ^
    --exclude-module notebook ^
    --exclude-module jupyter ^
    --uac-admin ^
    --noconsole ^
    main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo Build failed! Trying with console mode and reduced options...
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
        --version-file version_info.py ^
        --exclude-module matplotlib ^
        --exclude-module numpy ^
        --exclude-module pandas ^
        main.py
)

echo.
if exist "dist\adb-util.exe" (
    echo ✓ Build successful! 
    echo Executable location: dist\adb-util.exe
    dir "dist\adb-util.exe"
    
    echo.
    echo Creating checksum for security verification...
    certutil -hashfile "dist\adb-util.exe" SHA256 > "dist\adb-util.exe.sha256"
    echo SHA256 checksum created: dist\adb-util.exe.sha256
    
    echo.
    echo Creating release package...
    if not exist "release" mkdir "release"
    copy "dist\adb-util.exe" "release\"
    copy "dist\adb-util.exe.sha256" "release\"
    if exist "README.md" copy "README.md" "release\"
    if exist "LICENSE" copy "LICENSE" "release\"
    
    (
    echo ADB-UTIL for Windows
    echo.
    echo Installation:
    echo 1. Extract all files from the archive
    echo 2. Run adb-util.exe
    echo.
    echo Security Note:
    echo This executable is built with PyInstaller and may trigger
    echo false positive warnings from some antivirus software.
    echo The SHA256 checksum is provided for verification.
    echo.
    echo Requirements:
    echo - Windows 10 or later
    echo - Administrator privileges may be required for ADB operations
    echo.
    echo For issues, please check the project repository.
    ) > "release\README-Windows.txt"
    
    echo Release package prepared in 'release' folder
    
) else (
    echo ✗ Build failed! Executable not found.
    if exist "dist" (
        echo Contents of dist folder:
        dir dist
    )
)

echo.
echo Cleaning up temporary files...
if exist "version_info.py" del "version_info.py"

echo.
pause
