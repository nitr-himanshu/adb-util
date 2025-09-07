#!/usr/bin/env python3
"""
Test script to verify popup styling in both light and dark themes.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PyQt6.QtCore import Qt
from utils.theme_manager import theme_manager

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Popup Styling Test")
        self.setGeometry(300, 300, 400, 200)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Theme toggle button
        self.theme_btn = QPushButton("Toggle Theme (Current: Light)")
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn.setToolTip("Click to toggle between light and dark themes")
        layout.addWidget(self.theme_btn)
        
        # Test message box button
        msg_btn = QPushButton("Test Message Box")
        msg_btn.clicked.connect(self.show_message_box)
        msg_btn.setToolTip("This tooltip should be visible in both themes")
        layout.addWidget(msg_btn)
        
        # Test question dialog button
        question_btn = QPushButton("Test Question Dialog")
        question_btn.clicked.connect(self.show_question_dialog)
        question_btn.setToolTip("Test question dialog visibility")
        layout.addWidget(question_btn)
        
        # Initialize theme
        theme_manager.set_theme("light")
        theme_manager.theme_changed.connect(self.on_theme_changed)
    
    def toggle_theme(self):
        theme_manager.toggle_theme()
    
    def on_theme_changed(self, theme_name):
        self.theme_btn.setText(f"Toggle Theme (Current: {theme_name.title()})")
    
    def show_message_box(self):
        QMessageBox.information(self, "Test Message", 
                              "This is a test message box.\n\n"
                              "The text should be clearly visible in both light and dark themes.")
    
    def show_question_dialog(self):
        reply = QMessageBox.question(self, "Test Question", 
                                   "Can you see this text clearly?\n\n"
                                   "Click Yes if the text is visible, No if it's not.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Great!", "Perfect! The popup styling is working correctly.")
        else:
            QMessageBox.warning(self, "Issue Found", "There seems to be a visibility issue with the popup text.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
