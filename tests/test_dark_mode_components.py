#!/usr/bin/env python3
"""
Simple test to verify dark mode styling components.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, 
    QLineEdit, QCheckBox, QComboBox, QSpinBox, QGroupBox,
    QPushButton, QHBoxLayout, QLabel
)
from utils.theme_manager import theme_manager


class DarkModeTestWidget(QWidget):
    """Test widget to verify dark mode styling."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dark Mode Component Test")
        self.setGeometry(200, 200, 600, 500)
        
        layout = QVBoxLayout(self)
        
        # Theme toggle
        theme_layout = QHBoxLayout()
        self.theme_btn = QPushButton("Toggle to Dark Mode")
        self.theme_btn.clicked.connect(self.toggle_theme)
        theme_layout.addWidget(self.theme_btn)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # Test components
        self.text_edit = QTextEdit()
        self.text_edit.setText("This text should be clearly visible in both themes.")
        layout.addWidget(QLabel("QTextEdit:"))
        layout.addWidget(self.text_edit)
        
        self.line_edit = QLineEdit("Test input text")
        layout.addWidget(QLabel("QLineEdit:"))
        layout.addWidget(self.line_edit)
        
        self.checkbox = QCheckBox("Test checkbox - should be visible")
        layout.addWidget(self.checkbox)
        
        self.combo = QComboBox()
        self.combo.addItems(["Option 1", "Option 2", "Option 3"])
        layout.addWidget(QLabel("QComboBox:"))
        layout.addWidget(self.combo)
        
        self.spinbox = QSpinBox()
        self.spinbox.setRange(0, 100)
        self.spinbox.setValue(50)
        layout.addWidget(QLabel("QSpinBox:"))
        layout.addWidget(self.spinbox)
        
        # Group box with contents
        group = QGroupBox("Test Group Box")
        group_layout = QVBoxLayout(group)
        group_layout.addWidget(QCheckBox("Checkbox inside group"))
        group_layout.addWidget(QLineEdit("Input inside group"))
        layout.addWidget(group)
        
        # Initialize theme
        theme_manager.set_theme("light")
        theme_manager.theme_changed.connect(self.on_theme_changed)
        
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        current = theme_manager.get_current_theme()
        new_theme = "dark" if current == "light" else "light"
        theme_manager.set_theme(new_theme)
        
    def on_theme_changed(self, theme_name: str):
        """Handle theme change event."""
        if theme_name == "dark":
            self.theme_btn.setText("Toggle to Light Mode")
        else:
            self.theme_btn.setText("Toggle to Dark Mode")
            
        # Force style refresh
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


def main():
    app = QApplication(sys.argv)
    
    widget = DarkModeTestWidget()
    widget.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
