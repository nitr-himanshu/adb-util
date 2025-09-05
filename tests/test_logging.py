"""
Logging Test Script

Demonstrates the logging capabilities of the ADB-UTIL application.
"""

import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from utils.logger import (
    get_logger, enable_file_logging, disable_file_logging,
    get_log_info, log_device_operation, log_file_operation,
    log_startup, log_shutdown
)


def test_logging():
    """Test various logging features."""
    print("=== ADB-UTIL Logging System Test ===\n")
    
    # Get logger
    logger = get_logger("test")
    
    # Test basic logging
    print("1. Testing basic console logging:")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("\n2. Current logging configuration:")
    log_info = get_log_info()
    for key, value in log_info.items():
        print(f"   {key}: {value}")
    
    print("\n3. Testing convenience logging functions:")
    log_startup()
    log_device_operation("emulator-5554", "connect", "Testing device connection")
    log_file_operation("push", "/local/file.txt", "/sdcard/file.txt", "success")
    
    print("\n4. Enabling file logging:")
    enable_file_logging()
    
    # Log some messages to file
    logger.info("File logging is now enabled!")
    logger.warning("This message should appear in both console and file")
    log_device_operation("emulator-5554", "reboot", "Testing file logging")
    
    print("\n5. Updated logging configuration:")
    log_info = get_log_info()
    for key, value in log_info.items():
        print(f"   {key}: {value}")
    
    print("\n6. Testing different loggers:")
    file_logger = get_logger("file_manager")
    terminal_logger = get_logger("terminal")
    utils_logger = get_logger("utils")
    
    file_logger.info("File manager operation completed")
    terminal_logger.debug("Terminal command executed")
    utils_logger.warning("Device utils warning")
    
    print("\n7. Disabling file logging:")
    disable_file_logging()
    
    logger.info("File logging disabled - this should only appear in console")
    log_shutdown()
    
    print("\n=== Test Complete ===")
    print("Check the logs directory for created log files!")


if __name__ == "__main__":
    test_logging()
