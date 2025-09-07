#!/system/bin/sh
echo "Starting device performance monitoring..."
echo

echo "CPU usage:"
top -n 1 | head -10

echo
echo "Memory usage:"
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable|Cached|Buffers"

echo
echo "Battery information:"
dumpsys battery | grep -E "level|temperature|voltage|status"

echo
echo "Thermal information:"
if [ -d /sys/class/thermal ]; then
    for thermal in /sys/class/thermal/thermal_zone*/temp; do
        if [ -r "$thermal" ]; then
            echo "$(basename $(dirname $thermal)): $(cat $thermal)"
        fi
    done
fi

echo
echo "Top processes by CPU:"
top -n 1 | tail -n +8 | head -10

echo
echo "Device performance monitoring completed."
