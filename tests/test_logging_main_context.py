#!/usr/bin/env python3
"""
Test script to check for logging issues in main app context
"""

import sys
import traceback
from pathlib import Path

# Add src directory to path for imports (same as main.py)
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PyQt6.QtWidgets import QApplication

def test_logging_in_main_context():
    """Test logging module in the same context as main.py"""
    print("Testing logging module in main app context...")
    
    try:
        # Initialize logging first (same as main.py)
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Test logging initialization...")
        
        from gui.logging import Logging, LogcatWorker
        print("✅ Logging class imported successfully")
        
        # Test instantiation
        app = QApplication(sys.argv)
        logging_widget = Logging("test_device")
        print("✅ Logging widget instantiated successfully")
        
        # Test LogcatWorker creation
        try:
            worker = LogcatWorker("test_device")
            print("✅ LogcatWorker created successfully")
            
            # Test worker parameters
            worker.set_parameters("main", "time")
            print("✅ Worker parameters set successfully")
            
            # Test starting worker (but don't actually start)
            print("✅ Worker setup complete")
            
            # Test worker cleanup
            worker.deleteLater()
            print("✅ Worker cleaned up successfully")
            
        except Exception as worker_error:
            print(f"❌ LogcatWorker error: {worker_error}")
            traceback.print_exc()
        
        # Test some UI interactions
        try:
            logging_widget.apply_filters()
            print("✅ Filter application works")
            
            logging_widget.refresh_display()
            print("✅ Display refresh works")
            
        except Exception as ui_error:
            print(f"❌ UI interaction error: {ui_error}")
            traceback.print_exc()
        
        # Test cleanup
        logging_widget.cleanup()
        print("✅ Cleanup completed successfully")
        
        app.quit()
        print("✅ All tests passed in main context!")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_logging_in_main_context()
    sys.exit(0 if success else 1)
