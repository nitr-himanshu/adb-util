#!/usr/bin/env python3
"""
Test script to check for logging issues
"""

import sys
import traceback
from PyQt6.QtWidgets import QApplication

def test_logging_import():
    """Test if logging module can be imported and instantiated."""
    print("Testing logging module...")
    
    try:
        from src.gui.logging import Logging, LogcatWorker
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
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_logging_import()
    sys.exit(0 if success else 1)
