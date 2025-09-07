#!/usr/bin/env python3
"""
Test script to verify logging window dark mode fixes.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, 
    QPushButton, QHBoxLayout, QLabel, QTextEdit
)
from PyQt6.QtCore import QTimer, Qt
from utils.theme_manager import theme_manager
from gui.logging import Logging


class LoggingTestWindow(QMainWindow):
    """Test window to verify logging dark mode fixes."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logging Dark Mode Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Theme controls
        theme_layout = QHBoxLayout()
        
        self.theme_label = QLabel("Current Theme: Light")
        theme_layout.addWidget(self.theme_label)
        
        self.theme_toggle_btn = QPushButton("🌙 Switch to Dark Mode")
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        theme_layout.addWidget(self.theme_toggle_btn)
        
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # Instructions
        instructions = QLabel(
            "Instructions:\n"
            "1. Click 'Switch to Dark Mode' to test dark theme\n"
            "2. Verify that all logging window elements are visible:\n"
            "   - Log display area should have dark background with white text\n"
            "   - All input fields should be dark with white text\n"
            "   - Checkboxes should be clearly visible\n"
            "   - Group boxes should have proper dark styling\n"
            "   - Scroll bars should be dark themed\n"
            "3. Switch back to light mode to verify consistency"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 4px;")
        layout.addWidget(instructions)
        
        # Create logging widget with dummy device
        self.logging_widget = Logging("test_device_123")
        layout.addWidget(self.logging_widget)
        
        # Initialize theme manager
        theme_manager.theme_changed.connect(self.on_theme_changed)
        theme_manager.set_theme("light")
        
        # Add some dummy log entries to test text visibility
        QTimer.singleShot(1000, self.add_test_logs)
        
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        current = theme_manager.get_current_theme()
        new_theme = "dark" if current == "light" else "light"
        theme_manager.set_theme(new_theme)
        
    def on_theme_changed(self, theme_name: str):
        """Handle theme change event."""
        self.theme_label.setText(f"Current Theme: {theme_name.title()}")
        
        if theme_name == "dark":
            self.theme_toggle_btn.setText("☀️ Switch to Light Mode")
        else:
            self.theme_toggle_btn.setText("🌙 Switch to Dark Mode")
            
        # Force refresh of logging widget theme
        if hasattr(self, 'logging_widget'):
            QTimer.singleShot(100, self.logging_widget.refresh_theme)
    
    def add_test_logs(self):
        """Add test log entries to verify text visibility."""
        test_logs = [
            "2024-01-15 10:30:01.123  1234  1234 V TestTag: This is a verbose message for testing visibility",
            "2024-01-15 10:30:02.456  1234  1234 D TestTag: This is a debug message with some details",
            "2024-01-15 10:30:03.789  1234  1234 I TestTag: This is an info message - everything working normally",
            "2024-01-15 10:30:04.012  1234  1234 W TestTag: This is a warning message - something might be wrong",
            "2024-01-15 10:30:05.345  1234  1234 E TestTag: This is an error message - something went wrong!",
            "2024-01-15 10:30:06.678  1234  1234 F TestTag: This is a fatal error - critical failure!",
            "",
            "Test Instructions:",
            "- All text above should be clearly visible in both light and dark themes",
            "- Background should change appropriately when switching themes",
            "- Input fields, checkboxes, and other controls should be theme-appropriate",
            "- No elements should be invisible or hard to read in either theme"
        ]
        
        log_text = "\n".join(test_logs)
        if hasattr(self.logging_widget, 'log_display'):
            self.logging_widget.log_display.setText(log_text)


def main():
    """Main function to run the test."""
    app = QApplication(sys.argv)
    
    window = LoggingTestWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
