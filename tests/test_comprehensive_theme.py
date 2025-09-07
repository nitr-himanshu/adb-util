#!/usr/bin/env python3
"""
Comprehensive test to verify ALL UI elements get proper theme styling.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, 
    QPushButton, QHBoxLayout, QLabel
)
from PyQt6.QtCore import QTimer, Qt
from utils.theme_manager import theme_manager
from gui.logging import Logging


class ComprehensiveThemeTestWindow(QMainWindow):
    """Test window to verify comprehensive theme application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Comprehensive Theme Test - ALL Elements")
        self.setGeometry(50, 50, 1400, 900)
        
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
        
        test_all_btn = QPushButton("🔄 Test All Elements")
        test_all_btn.clicked.connect(self.test_all_elements)
        theme_layout.addWidget(test_all_btn)
        
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # Instructions
        instructions = QLabel(
            "COMPREHENSIVE THEME TEST:\n\n"
            "1. Click 'Switch to Dark Mode' to test dark theme\n"
            "2. Verify ALL elements are properly themed:\n"
            "   ✓ Log display area (dark background, white text)\n"
            "   ✓ ALL buttons (proper dark styling)\n"
            "   ✓ ALL input fields and dropdowns (dark backgrounds)\n"
            "   ✓ ALL checkboxes (visible indicators)\n"
            "   ✓ ALL group boxes (dark borders and titles)\n"
            "   ✓ ALL scroll bars (dark themed)\n"
            "   ✓ ALL labels (white text)\n"
            "   ✓ Search bar and filter inputs\n"
            "   ✓ Export buttons and controls\n"
            "3. Click 'Test All Elements' to programmatically verify\n"
            "4. Switch back to light mode to verify consistency\n\n"
            "NO ELEMENT should remain unthemed!"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 4px;")
        layout.addWidget(instructions)
        
        # Create logging widget with comprehensive UI
        self.logging_widget = Logging("comprehensive_test_device")
        layout.addWidget(self.logging_widget)
        
        # Initialize theme manager
        theme_manager.theme_changed.connect(self.on_theme_changed)
        theme_manager.set_theme("light")
        
        # Add test data to make all elements visible
        QTimer.singleShot(500, self.populate_test_data)
        
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
            
        # Force comprehensive refresh of logging widget theme
        if hasattr(self, 'logging_widget'):
            # Multiple refresh attempts to ensure complete application
            QTimer.singleShot(50, self.logging_widget.refresh_theme)
            QTimer.singleShot(150, self.logging_widget.refresh_theme)
            QTimer.singleShot(300, self.logging_widget.refresh_theme)
    
    def populate_test_data(self):
        """Add test data to make all UI elements visible and testable."""
        if hasattr(self.logging_widget, 'log_display'):
            test_logs = [
                "2024-01-15 10:30:01.123  1234  1234 V TestTag: VERBOSE - Testing theme visibility",
                "2024-01-15 10:30:02.456  1234  1234 D TestTag: DEBUG - All buttons should be themed",
                "2024-01-15 10:30:03.789  1234  1234 I TestTag: INFO - Input fields must have dark backgrounds",
                "2024-01-15 10:30:04.012  1234  1234 W TestTag: WARNING - Checkboxes need proper indicators",
                "2024-01-15 10:30:05.345  1234  1234 E TestTag: ERROR - Group boxes require dark styling",
                "2024-01-15 10:30:06.678  1234  1234 F TestTag: FATAL - Scroll bars must be dark themed",
                "",
                "Theme Test Status:",
                "✓ Log display - Should have dark background with white text",
                "✓ Search input - Should have dark background",
                "✓ Format/Buffer dropdowns - Should be dark themed",
                "✓ All buttons - Should have proper dark button styling",
                "✓ All checkboxes - Should have visible dark indicators",
                "✓ Group boxes - Should have dark borders and titles",
                "✓ Export controls - Should be consistently themed",
                "",
                "NO ELEMENT should remain unthemed in dark mode!"
            ]
            
            log_text = "\n".join(test_logs)
            self.logging_widget.log_display.setText(log_text)
            
        # Enable some checkboxes to test their visibility
        if hasattr(self.logging_widget, 'level_checkboxes'):
            for i, checkbox in enumerate(self.logging_widget.level_checkboxes.values()):
                checkbox.setChecked(i % 2 == 0)  # Alternate checked/unchecked
                
        # Set some filter text to test input fields
        if hasattr(self.logging_widget, 'search_input'):
            self.logging_widget.search_input.setText("test search")
            
        if hasattr(self.logging_widget, 'highlight_input'):
            self.logging_widget.highlight_input.setText("highlight test")
    
    def test_all_elements(self):
        """Programmatically test that all elements have proper theme styling."""
        current_theme = theme_manager.get_current_theme()
        results = []
        
        # Test various widget types
        from PyQt6.QtWidgets import QPushButton, QLineEdit, QComboBox, QCheckBox, QGroupBox, QScrollArea, QLabel
        
        # Check buttons
        buttons = self.logging_widget.findChildren(QPushButton)
        button_themed = 0
        for button in buttons:
            style = button.styleSheet()
            if current_theme == "dark":
                if "#363636" in style or "#484848" in style or "background-color:" in style:
                    button_themed += 1
            else:
                if "#ffffff" in style or "#e0e0e0" in style or "background-color:" in style:
                    button_themed += 1
        results.append(f"Buttons: {button_themed}/{len(buttons)} themed")
        
        # Check line edits
        line_edits = self.logging_widget.findChildren(QLineEdit)
        line_edit_themed = 0
        for le in line_edits:
            style = le.styleSheet()
            if "background-color:" in style and "color:" in style:
                line_edit_themed += 1
        results.append(f"Input Fields: {line_edit_themed}/{len(line_edits)} themed")
        
        # Check combo boxes
        combos = self.logging_widget.findChildren(QComboBox)
        combo_themed = 0
        for combo in combos:
            style = combo.styleSheet()
            if "background-color:" in style and "color:" in style:
                combo_themed += 1
        results.append(f"Combo Boxes: {combo_themed}/{len(combos)} themed")
        
        # Check checkboxes
        checkboxes = self.logging_widget.findChildren(QCheckBox)
        checkbox_themed = 0
        for cb in checkboxes:
            style = cb.styleSheet()
            if "QCheckBox" in style and "color:" in style:
                checkbox_themed += 1
        results.append(f"Checkboxes: {checkbox_themed}/{len(checkboxes)} themed")
        
        # Check group boxes
        groupboxes = self.logging_widget.findChildren(QGroupBox)
        groupbox_themed = 0
        for gb in groupboxes:
            style = gb.styleSheet()
            if "QGroupBox" in style and "color:" in style:
                groupbox_themed += 1
        results.append(f"Group Boxes: {groupbox_themed}/{len(groupboxes)} themed")
        
        # Update instructions with results
        result_text = f"\n\nTEST RESULTS ({current_theme.upper()} THEME):\n" + "\n".join(results)
        
        if hasattr(self, 'instructions_label'):
            current_text = self.instructions_label.text()
            # Remove old results if they exist
            if "TEST RESULTS" in current_text:
                current_text = current_text.split("TEST RESULTS")[0]
            self.instructions_label.setText(current_text + result_text)


def main():
    """Main function to run the comprehensive theme test."""
    app = QApplication(sys.argv)
    
    window = ComprehensiveThemeTestWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
