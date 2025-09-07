"""
Test script for integrated text editor functionality.

This script demonstrates the new integrated text editor feature.
"""

import sys
import tempfile
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

from src.adb.file_operations import FileInfo
from src.gui.integrated_text_editor import IntegratedTextEditor


class MockFileOperations:
    """Mock file operations for testing."""
    
    def __init__(self):
        self.test_content = "Hello World!\nThis is a test file.\nLine 3\nLine 4"
    
    async def pull_file(self, device_path: str, local_path: str) -> bool:
        """Mock pull file operation."""
        try:
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(self.test_content)
            return True
        except Exception:
            return False
    
    async def push_file(self, local_path: str, device_path: str) -> bool:
        """Mock push file operation."""
        try:
            with open(local_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"Mock upload to {device_path}:")
            print(content)
            print("-" * 40)
            return True
        except Exception:
            return False


class TestWindow(QMainWindow):
    """Test window for integrated text editor."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Integrated Text Editor Test")
        self.resize(400, 200)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Test button
        test_btn = QPushButton("🔧 Test Integrated Text Editor")
        test_btn.clicked.connect(self.test_editor)
        layout.addWidget(test_btn)
        
        # Mock file operations
        self.file_ops = MockFileOperations()
        
    def test_editor(self):
        """Test the integrated text editor."""
        # Create mock file info
        file_info = FileInfo(
            name="test_file.txt",
            path="/sdcard/test_file.txt",
            is_directory=False,
            size=100
        )
        
        # Create and show editor
        editor = IntegratedTextEditor(file_info, self.file_ops, self)
        editor.file_saved.connect(self.on_file_saved)
        editor.exec()
        
    def on_file_saved(self, device_path: str):
        """Handle file saved signal."""
        print(f"✅ File saved: {device_path}")


def main():
    """Main test function."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show test window
    window = TestWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
