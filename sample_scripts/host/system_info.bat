@echo off
echo Starting system information collection...
echo.

echo Current date and time:
date /t
time /t

echo.
echo System information:
systeminfo | findstr /C:"OS Name" /C:"OS Version" /C:"System Type" /C:"Total Physical Memory"

echo.
echo Disk space:
dir c:\ | findstr "free"

echo.
echo Network configuration:
ipconfig | findstr /C:"IPv4" /C:"Subnet" /C:"Gateway"

echo.
echo Running processes:
tasklist | findstr /C:"adb" /C:"python" /C:"java"

echo.
echo System information collection completed.
pause
