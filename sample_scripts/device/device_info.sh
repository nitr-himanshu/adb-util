#!/system/bin/sh
echo "Starting device system information collection..."
echo

echo "Device information:"
getprop ro.product.model
getprop ro.product.manufacturer
getprop ro.build.version.release
getprop ro.build.version.sdk

echo
echo "Hardware information:"
cat /proc/cpuinfo | grep -E "processor|model name" | head -8
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable"

echo
echo "Storage information:"
df | grep -E "/data|/system|/sdcard"

echo
echo "Network information:"
ip addr show | grep -E "inet|UP" | head -10

echo
echo "Running processes:"
ps | grep -E "system_server|zygote|surfaceflinger" | head -5

echo
echo "Device system information collection completed."
