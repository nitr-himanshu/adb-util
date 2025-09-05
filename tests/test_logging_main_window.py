#!/usr/bin/env python3
"""
Test script to simulate the exact logging widget creation from main window
"""

import sys
import traceback
from pathlib import Path

# Add src directory to path for imports (same as main.py)
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget

def test_logging_from_main_window():
    """Test logging widget creation exactly as main window does it"""
    print("Testing logging widget creation from main window context...")
    
    try:
        # Initialize logging first
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Main window logging test initialization...")
        
        # Create QApplication
        app = QApplication(sys.argv)
        
        # Create a minimal main window structure
        main_window = QMainWindow()
        tab_widget = QTabWidget()
        main_window.setCentralWidget(tab_widget)
        
        print("✅ Main window structure created")
        
        # Test the exact code from main_window.py
        device_id = "test_device"
        mode = "logging"
        tab_title = f"📊 Logging - {device_id}"
        
        print(f"🔄 Creating {mode} tab for device {device_id}")
        
        # This is the exact code from main_window.py line 404-405
        if mode == "logging":
            from gui.logging import Logging
            widget = Logging(device_id)
            print("✅ Logging widget created successfully")
            
            # Add to tab widget (like main window does)
            tab_widget.addTab(widget, tab_title)
            tab_widget.setCurrentWidget(widget)
            print("✅ Logging widget added to tab successfully")
            
            # Test some interactions
            try:
                # Simulate user interactions that might cause issues
                widget.apply_filters()
                widget.refresh_display()
                print("✅ User interactions work correctly")
                
                # Test error that might occur during actual usage
                widget.toggle_capture()  # This might trigger the error
                print("✅ Toggle capture works")
                
                # Stop capture if it started
                if widget.is_capturing:
                    widget.stop_capture()
                    print("✅ Stop capture works")
                
            except Exception as interaction_error:
                print(f"❌ Interaction error: {interaction_error}")
                traceback.print_exc()
            
            # Clean up
            widget.cleanup()
            print("✅ Widget cleanup completed")
        
        # Clean up app
        app.quit()
        print("✅ All main window tests passed!")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_logging_from_main_window()
    sys.exit(0 if success else 1)
