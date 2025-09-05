#!/usr/bin/env python3
"""
Test script to verify raw logging format works correctly.
"""

import asyncio
from src.adb.logcat_handler import LogcatHandler

async def test_raw_format():
    """Test raw format parsing."""
    handler = LogcatHandler("test_device")
    
    # Test raw format parsing
    test_lines = [
        "This is a raw log message",
        "Another raw message without any structure",
        "Error: Something went wrong",
        "DEBUG: This is debug info",
        ""
    ]
    
    print("Testing RAW format parsing:")
    print("-" * 50)
    
    # Set format to raw
    handler.current_format = "raw"
    
    for line in test_lines:
        if line.strip():  # Skip empty lines
            entry = handler.parse_log_line(line)
            if entry:
                print(f"Input:  '{line}'")
                print(f"Output: Level={entry.level}, Tag={entry.tag}, Message='{entry.message}'")
                print(f"Raw:    '{entry.raw_line}'")
                print()
            else:
                print(f"Failed to parse: '{line}'")
                print()
    
    # Test structured format for comparison
    print("Testing TIME format parsing:")
    print("-" * 50)
    
    handler.current_format = "time"
    structured_lines = [
        "01-02 03:04:05.678 I/ActivityManager(12345): Starting activity",
        "01-02 03:04:05.679 E/System(12346): Error occurred",
        "This won't match structured pattern"
    ]
    
    for line in structured_lines:
        entry = handler.parse_log_line(line)
        if entry:
            print(f"Input:  '{line}'")
            print(f"Output: Time={entry.timestamp}, Level={entry.level}, Tag={entry.tag}, PID={entry.pid}")
            print(f"        Message='{entry.message}'")
            print()
        else:
            print(f"Failed to parse: '{line}'")
            print()

if __name__ == "__main__":
    asyncio.run(test_raw_format())
