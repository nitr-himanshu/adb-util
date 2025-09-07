#!/bin/bash
echo "Starting system information collection..."
echo

echo "Current date and time:"
date

echo
echo "System information:"
uname -a

echo
echo "Memory information:"
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable"

echo
echo "Disk space:"
df -h

echo
echo "Network configuration:"
ip addr show | grep -E "inet|UP"

echo
echo "Running processes:"
ps aux | grep -E "adb|python|java" | grep -v grep

echo
echo "System information collection completed."
