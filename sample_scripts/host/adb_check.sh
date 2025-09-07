#!/bin/bash
echo "Starting ADB utilities check..."
echo

echo "Checking ADB version:"
adb version

echo
echo "Listing connected devices:"
adb devices

echo
echo "Checking device properties for first device:"
DEVICE=$(adb devices | grep -v "List" | grep "device" | head -1 | cut -f1)
if [ ! -z "$DEVICE" ]; then
    echo "Device: $DEVICE"
    adb -s $DEVICE shell getprop ro.product.model
    adb -s $DEVICE shell getprop ro.build.version.release
else
    echo "No devices found"
fi

echo
echo "ADB utilities check completed."
