@echo off
echo Starting ADB utilities check...
echo.

echo Checking ADB version:
adb version

echo.
echo Listing connected devices:
adb devices

echo.
echo Checking device properties for first device:
for /f "tokens=1" %%i in ('adb devices ^| findstr device ^| head -1') do (
    echo Device: %%i
    adb -s %%i shell getprop ro.product.model
    adb -s %%i shell getprop ro.build.version.release
)

echo.
echo ADB utilities check completed.
pause
