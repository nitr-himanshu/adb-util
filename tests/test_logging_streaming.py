#!/usr/bin/env python3
"""
Test script to check for logging issues with actual streaming
"""

import sys
import traceback
import time
from pathlib import Path

# Add src directory to path for imports (same as main.py)
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

def test_logging_with_streaming():
    """Test logging module with actual streaming simulation"""
    print("Testing logging module with streaming...")
    
    try:
        # Initialize logging first
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Test with streaming initialization...")
        
        from gui.logging import Logging, LogcatWorker
        print("✅ Logging class imported successfully")
        
        # Test instantiation
        app = QApplication(sys.argv)
        logging_widget = Logging("test_device")
        print("✅ Logging widget instantiated successfully")
        
        # Test error handlers
        def on_error_received(error_msg):
            print(f"🔥 Error received: {error_msg}")
        
        def on_status_changed(is_streaming):
            print(f"📡 Streaming status: {'ON' if is_streaming else 'OFF'}")
        
        # Test starting capture (this might trigger the error)
        try:
            print("🚀 Testing start capture...")
            logging_widget.start_capture()
            print("✅ Start capture initiated")
            
            # Let it run for a moment
            print("⏳ Waiting for streaming to start...")
            
            # Use QTimer to stop after a short time
            def stop_test():
                print("🛑 Stopping test...")
                if logging_widget.is_capturing:
                    logging_widget.stop_capture()
                app.quit()
            
            timer = QTimer()
            timer.singleShot(2000, stop_test)  # Stop after 2 seconds
            
            # Run the event loop briefly
            app.processEvents()
            time.sleep(0.5)
            app.processEvents()
            
            print("✅ Streaming test completed")
            
        except Exception as streaming_error:
            print(f"❌ Streaming error: {streaming_error}")
            traceback.print_exc()
        
        # Test cleanup
        logging_widget.cleanup()
        print("✅ Cleanup completed successfully")
        
        print("✅ All streaming tests completed!")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_logging_with_streaming()
    sys.exit(0 if success else 1)
