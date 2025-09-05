#!/usr/bin/env python3
"""
Test script for logcat integration
"""

import sys
import asyncio
from src.adb.logcat_handler import LogcatHandler
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def test_logcat_handler():
    """Test the LogcatHandler functionality."""
    print("Testing LogcatHandler...")
    
    # Test with a dummy device ID for now
    device_id = "test_device"
    handler = LogcatHandler(device_id)
    
    print(f"LogcatHandler created for device: {device_id}")
    
    # Test log parsing
    test_log_lines = [
        "01-01 12:00:00.123  1234  5678 I TestTag: This is a test message",
        "01-01 12:00:01.456  2345  6789 E ErrorTag: This is an error message",
        "01-01 12:00:02.789  3456  7890 D DebugTag: Debug information here"
    ]
    
    print("\nTesting log parsing...")
    for line in test_log_lines:
        entry = handler.parse_log_line(line)
        if entry:
            print(f"Parsed: {entry.level}/{entry.tag}({entry.pid}): {entry.message}")
        else:
            print(f"Failed to parse: {line}")
    
    # Test filtering
    print("\nTesting filtering...")
    handler.log_entries = []
    for line in test_log_lines:
        entry = handler.parse_log_line(line)
        if entry:
            handler.log_entries.append(entry)
    
    # Filter by level
    filtered = handler.filter_entries(handler.log_entries, level_filter=['I', 'E'])
    print(f"Filtered by level (I, E): {len(filtered)} entries")
    for entry in filtered:
        print(f"  {entry.level}/{entry.tag}: {entry.message}")
    
    # Filter by tag
    filtered = handler.filter_entries(handler.log_entries, tag_filter='TestTag')
    print(f"Filtered by tag (TestTag): {len(filtered)} entries")
    for entry in filtered:
        print(f"  {entry.level}/{entry.tag}: {entry.message}")
    
    print("\nLogcat integration test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_logcat_handler())
