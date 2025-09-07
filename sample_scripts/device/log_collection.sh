#!/system/bin/sh
echo "Starting log collection..."
echo

echo "Recent system logs:"
logcat -d -t 50 | tail -20

echo
echo "Recent app crashes:"
logcat -d -b crash | tail -10

echo
echo "Recent ANR (Application Not Responding):"
logcat -d | grep -i "anr" | tail -5

echo
echo "WiFi status:"
dumpsys wifi | grep -E "Wi-Fi is|state|SSID"

echo
echo "Bluetooth status:"
dumpsys bluetooth_manager | grep -E "enabled|state" | head -5

echo
echo "Recent kernel messages:"
dmesg | tail -10

echo
echo "Log collection completed."
