"""
Integrated Text Editor

A built-in text editor for editing device files within the application.
Provides syntax highlighting, line numbers, and basic editing features.
"""

import os
import asyncio
import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
    QPushButton, QDialog, QMessageBox, QFrame, QStatusBar,
    QMenuBar, QMenu, QFileDialog, QInputDialog, QSplitter,
    QPlainTextEdit, QCheckBox, QSpinBox, QComboBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import (
    QFont, QFontMetrics, QPainter, QColor, QPalette,
    QTextCursor, QTextFormat, QSyntaxHighlighter,
    QTextDocument, QAction, QKeySequence
)

from src.adb.file_operations import FileOperations, FileInfo
from src.utils.logger import get_logger
from src.utils.theme_manager import theme_manager


class LineNumberArea(QWidget):
    """Widget for displaying line numbers alongside the text editor."""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        
    def sizeHint(self):
        return self.editor.line_number_area_width()
        
    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    """Text editor with line numbers and syntax highlighting."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.line_number_area = LineNumberArea(self)
        
        # Connect signals
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        theme_manager.theme_changed.connect(self.apply_theme)
        
        # Initial setup
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        
        # Set font
        font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Courier New", 10)
        self.setFont(font)
        
        # Enable line wrap
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        
        # Apply initial theme
        self.apply_theme(theme_manager.get_current_theme())
        
    def line_number_area_width(self):
        """Calculate the width needed for line numbers."""
        digits = 1
        count = max(1, self.blockCount())
        while count >= 10:
            count //= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
        
    def update_line_number_area_width(self, _):
        """Update the width of the line number area."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        
    def update_line_number_area(self, rect, dy):
        """Update the line number area when text changes."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), 
                                       self.line_number_area.width(), 
                                       rect.height())
            
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
            
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            cr.left(), cr.top(), 
            self.line_number_area_width(), 
            cr.height()
        )
        
    def line_number_area_paint_event(self, event):
        """Paint the line numbers."""
        painter = QPainter(self.line_number_area)
        
        # Get theme colors using app detection
        app = QApplication.instance()
        app_stylesheet = app.styleSheet() if app else ""
        is_dark_theme = "#2b2b2b" in app_stylesheet or "dark" in app_stylesheet.lower()
        
        # Set colors based on theme
        if is_dark_theme:
            bg_color = QColor("#363636")
            text_color = QColor("#bbbbbb")
        else:
            bg_color = QColor("#f0f0f0")
            text_color = QColor("#666666")
            
        painter.fillRect(event.rect(), bg_color)
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(text_color)
                painter.drawText(
                    0, int(top), 
                    self.line_number_area.width() - 5, 
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number
                )
                
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1
            
    def highlight_current_line(self):
        """Highlight the current line."""
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            
            # Get theme-appropriate colors using app detection
            app = QApplication.instance()
            app_stylesheet = app.styleSheet() if app else ""
            is_dark_theme = "#2b2b2b" in app_stylesheet or "dark" in app_stylesheet.lower()
            
            if is_dark_theme:
                # Dark theme: very subtle highlight that doesn't interfere with text
                line_color = QColor("#2a2a2a")  # Very subtle gray, barely darker than background
            else:
                # Light theme: subtle yellow highlight
                line_color = QColor("#fffacd")  # Light yellow
                
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
            
        self.setExtraSelections(extra_selections)
        
    def apply_theme(self, theme_name: str):
        """Apply theme styling to the editor."""
        if theme_name == "dark":
            # Dark theme colors
            bg_color = "#1e1e1e"
            text_color = "#ffffff"
            border_color = "#555555"
            selection_bg = "#264f78"
            selection_fg = "#ffffff"
            
            style = f"""
                QPlainTextEdit {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: 1px solid {border_color};
                    border-radius: 4px;
                    selection-background-color: {selection_bg};
                    selection-color: {selection_fg};
                    font-family: 'Consolas', 'Courier New', monospace;
                }}
                
                QPlainTextEdit:focus {{
                    border-color: #007acc;
                    border-width: 2px;
                }}
            """
            
            # Also set palette colors directly
            palette = self.palette()
            palette.setColor(QPalette.ColorRole.Base, QColor(bg_color))
            palette.setColor(QPalette.ColorRole.Text, QColor(text_color))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(selection_bg))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(selection_fg))
            self.setPalette(palette)
            
        else:
            # Light theme colors
            bg_color = "#ffffff"
            text_color = "#000000"
            border_color = "#c0c0c0"
            selection_bg = "#316ac5"
            selection_fg = "#ffffff"
            
            style = f"""
                QPlainTextEdit {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: 1px solid {border_color};
                    border-radius: 4px;
                    selection-background-color: {selection_bg};
                    selection-color: {selection_fg};
                    font-family: 'Consolas', 'Courier New', monospace;
                }}
                
                QPlainTextEdit:focus {{
                    border-color: #007acc;
                    border-width: 2px;
                }}
            """
            
            # Also set palette colors directly
            palette = self.palette()
            palette.setColor(QPalette.ColorRole.Base, QColor(bg_color))
            palette.setColor(QPalette.ColorRole.Text, QColor(text_color))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(selection_bg))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(selection_fg))
            self.setPalette(palette)
            
        self.setStyleSheet(style)
        
        # Update line number area
        self.line_number_area.update()
        
        # Re-highlight current line with new theme
        self.highlight_current_line()


class FileUploadWorker(QThread):
    """Worker thread for uploading file changes back to device."""
    
    upload_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, content: str, device_path: str, file_ops: FileOperations):
        super().__init__()
        self.content = content
        self.device_path = device_path
        self.file_ops = file_ops
        self.logger = get_logger(__name__)
        
    def run(self):
        """Execute the file upload."""
        try:
            # Create event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Create temporary file with content
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as temp_file:
                    temp_file.write(self.content)
                    temp_path = Path(temp_file.name)  # Convert to Path object
                
                # Upload to device
                success = loop.run_until_complete(
                    self.file_ops.push_file(temp_path, self.device_path)
                )
                
                # Clean up temp file
                temp_path.unlink(missing_ok=True)
                
                if success:
                    self.upload_completed.emit(True, "File uploaded successfully")
                else:
                    self.upload_completed.emit(False, "Failed to upload file to device")
                    
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Error uploading file: {e}")
            self.upload_completed.emit(False, f"Upload error: {str(e)}")


class IntegratedTextEditor(QDialog):
    """Integrated text editor dialog for editing device files."""
    
    file_saved = pyqtSignal(str)  # device_path
    
    def __init__(self, file_info: FileInfo, file_ops: FileOperations, parent=None):
        super().__init__(parent)
        self.file_info = file_info
        self.file_ops = file_ops
        self.logger = get_logger(__name__)
        self.content_modified = False
        self.original_content = ""
        self.upload_worker = None
        
        # Create editor first
        self.editor = CodeEditor()
        
        self.setup_ui()
        
        # Get theme from application stylesheet to ensure accuracy
        app = QApplication.instance()
        app_stylesheet = app.styleSheet() if app else ""
        
        # Detect theme from application state (more reliable than theme manager)
        detected_theme = "dark" if "#2b2b2b" in app_stylesheet or "dark" in app_stylesheet.lower() else "light"
        
        # Apply the detected theme
        self.apply_theme(detected_theme)
        
        # Connect theme changes
        theme_manager.theme_changed.connect(self.apply_theme)
        
        self.load_file_content()
        
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(f"Edit: {self.file_info.name}")
        self.setModal(True)
        self.resize(900, 700)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Connect editor signals
        self.editor.textChanged.connect(self.on_content_changed)
        
        # Menu bar
        self.setup_menu_bar(layout)
        
        # Toolbar
        self.setup_toolbar(layout)
        
        # Editor area
        layout.addWidget(self.editor)
        
        # Status bar
        self.setup_status_bar(layout)
        
        # Button bar
        self.setup_button_bar(layout)
        
        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(30000)  # Auto-save every 30 seconds
        
    def setup_menu_bar(self, layout):
        """Set up the menu bar."""
        menu_bar = QMenuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        close_action = QAction("&Close", self)
        close_action.setShortcut(QKeySequence.StandardKey.Close)
        close_action.triggered.connect(self.close_editor)
        file_menu.addAction(close_action)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        find_action = QAction("&Find", self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.triggered.connect(self.show_find_dialog)
        edit_menu.addAction(find_action)
        
        # Format menu
        format_menu = menu_bar.addMenu("&Format")
        
        format_json_action = QAction("Format &JSON", self)
        format_json_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        format_json_action.triggered.connect(self.format_json)
        format_menu.addAction(format_json_action)
        
        minify_json_action = QAction("&Minify JSON", self)
        minify_json_action.setShortcut(QKeySequence("Ctrl+Shift+M"))
        minify_json_action.triggered.connect(self.minify_json)
        format_menu.addAction(minify_json_action)
        
        format_menu.addSeparator()
        
        validate_json_action = QAction("&Validate JSON", self)
        validate_json_action.setShortcut(QKeySequence("Ctrl+Shift+V"))
        validate_json_action.triggered.connect(self.validate_json)
        format_menu.addAction(validate_json_action)
        
        layout.addWidget(menu_bar)
        
    def setup_toolbar(self, layout):
        """Set up the toolbar."""
        toolbar_frame = QFrame()
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
        # File info
        info_label = QLabel(f"File: {self.file_info.path} | Size: {self.file_info.size} bytes")
        info_label.setStyleSheet("color: #666; font-size: 10px;")
        toolbar_layout.addWidget(info_label)
        
        toolbar_layout.addStretch()
        
        # Auto-save checkbox
        self.auto_save_checkbox = QCheckBox("Auto-save")
        self.auto_save_checkbox.setChecked(True)
        self.auto_save_checkbox.stateChanged.connect(self.toggle_auto_save)
        toolbar_layout.addWidget(self.auto_save_checkbox)
        
        # JSON format button
        format_json_btn = QPushButton("📝 Format JSON")
        format_json_btn.setToolTip("Format JSON with proper indentation (Ctrl+Shift+F)")
        format_json_btn.clicked.connect(self.format_json)
        format_json_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        toolbar_layout.addWidget(format_json_btn)
        
        # JSON validate button
        validate_json_btn = QPushButton("✓ Validate")
        validate_json_btn.setToolTip("Validate JSON syntax (Ctrl+Shift+V)")
        validate_json_btn.clicked.connect(self.validate_json)
        validate_json_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        toolbar_layout.addWidget(validate_json_btn)
        
        layout.addWidget(toolbar_frame)
        
    def setup_status_bar(self, layout):
        """Set up the status bar."""
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(5, 2, 5, 2)
        
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Cursor position
        self.cursor_label = QLabel("Line 1, Column 1")
        self.editor.cursorPositionChanged.connect(self.update_cursor_position)
        status_layout.addWidget(self.cursor_label)
        
        layout.addWidget(status_frame)
        
    def setup_button_bar(self, layout):
        """Set up the button bar."""
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(5, 5, 5, 5)
        
        # Save button
        save_btn = QPushButton("💾 Save to Device")
        save_btn.clicked.connect(self.save_file)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(save_btn)
        
        # Save local button
        save_local_btn = QPushButton("💾 Save Local Copy")
        save_local_btn.clicked.connect(self.save_as_file)
        button_layout.addWidget(save_local_btn)
        
        button_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(self.close_editor)
        button_layout.addWidget(close_btn)
        
        layout.addWidget(button_frame)
        
    def load_file_content(self):
        """Load file content from device."""
        self.status_label.setText("Loading file content...")
        
        # Start worker thread to download content
        self.download_worker = FileDownloadWorker(self.file_info, self.file_ops)
        self.download_worker.content_loaded.connect(self.on_content_loaded)
        self.download_worker.error_occurred.connect(self.on_download_error)
        self.download_worker.start()
        
    def on_content_loaded(self, content: str):
        """Handle successful content loading."""
        self.original_content = content
        self.editor.setPlainText(content)
        self.content_modified = False
        self.status_label.setText("File loaded successfully")
        self.update_window_title()
        
    def on_download_error(self, error_message: str):
        """Handle download error."""
        self.status_label.setText(f"Error loading file: {error_message}")
        QMessageBox.critical(self, "Load Error", f"Failed to load file:\n{error_message}")
        
    def on_content_changed(self):
        """Handle content changes."""
        if hasattr(self, 'original_content'):
            self.content_modified = (self.editor.toPlainText() != self.original_content)
            self.update_window_title()
            
    def update_window_title(self):
        """Update window title with modification indicator."""
        title = f"Edit: {self.file_info.name}"
        if self.content_modified:
            title += " *"
        self.setWindowTitle(title)
        
    def update_cursor_position(self):
        """Update cursor position display."""
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        self.cursor_label.setText(f"Line {line}, Column {column}")
        
    def toggle_auto_save(self, state):
        """Toggle auto-save functionality."""
        if state == Qt.CheckState.Checked.value:
            self.auto_save_timer.start(30000)
        else:
            self.auto_save_timer.stop()
            
    def auto_save(self):
        """Auto-save if content has been modified."""
        if self.content_modified and self.auto_save_checkbox.isChecked():
            self.save_file(show_message=False)
            
    def save_file(self, show_message=True):
        """Save file content back to device."""
        if not self.content_modified:
            if show_message:
                self.status_label.setText("No changes to save")
            return
            
        content = self.editor.toPlainText()
        self.status_label.setText("Saving to device...")
        
        # Start upload worker
        self.upload_worker = FileUploadWorker(content, self.file_info.path, self.file_ops)
        self.upload_worker.upload_completed.connect(
            lambda success, msg: self.on_upload_completed(success, msg, show_message)
        )
        self.upload_worker.start()
        
    def on_upload_completed(self, success: bool, message: str, show_message: bool):
        """Handle upload completion."""
        if success:
            self.original_content = self.editor.toPlainText()
            self.content_modified = False
            self.update_window_title()
            self.status_label.setText("File saved successfully")
            if show_message:
                self.status_label.setText("✅ Saved to device")
            self.file_saved.emit(self.file_info.path)
        else:
            self.status_label.setText(f"Save failed: {message}")
            if show_message:
                QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{message}")
                
    def save_as_file(self):
        """Save file content to local disk."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save File As",
            self.file_info.name,
            "All Files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.editor.toPlainText())
                self.status_label.setText(f"Saved local copy: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save local file:\n{str(e)}")
                
    def show_find_dialog(self):
        """Show find dialog."""
        text, ok = QInputDialog.getText(self, "Find", "Find text:")
        if ok and text:
            self.find_text(text)
            
    def find_text(self, text: str):
        """Find and highlight text in editor."""
        cursor = self.editor.textCursor()
        found = self.editor.find(text)
        if not found:
            # Search from beginning
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)
            found = self.editor.find(text)
            if not found:
                self.status_label.setText(f"Text '{text}' not found")
                
    def format_json(self):
        """Format JSON content with proper indentation."""
        try:
            # Get current text
            current_text = self.editor.toPlainText().strip()
            
            if not current_text:
                self.status_label.setText("No content to format")
                return
                
            # Parse JSON
            try:
                parsed_json = json.loads(current_text)
            except json.JSONDecodeError as e:
                QMessageBox.warning(
                    self, 
                    "JSON Format Error",
                    f"Invalid JSON content:\n{str(e)}\n\nPlease fix the JSON syntax and try again."
                )
                self.status_label.setText("JSON formatting failed - invalid syntax")
                return
            
            # Format with indentation
            formatted_json = json.dumps(parsed_json, indent=4, ensure_ascii=False, sort_keys=True)
            
            # Preserve cursor position relative to content
            cursor = self.editor.textCursor()
            scroll_position = self.editor.verticalScrollBar().value()
            
            # Replace content
            self.editor.setPlainText(formatted_json)
            
            # Restore approximate scroll position
            self.editor.verticalScrollBar().setValue(scroll_position)
            
            self.status_label.setText("JSON formatted successfully")
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Format Error", 
                f"Failed to format JSON:\n{str(e)}"
            )
            self.status_label.setText("JSON formatting failed")
            
    def minify_json(self):
        """Minify JSON content by removing whitespace."""
        try:
            # Get current text
            current_text = self.editor.toPlainText().strip()
            
            if not current_text:
                self.status_label.setText("No content to minify")
                return
                
            # Parse JSON
            try:
                parsed_json = json.loads(current_text)
            except json.JSONDecodeError as e:
                QMessageBox.warning(
                    self, 
                    "JSON Minify Error",
                    f"Invalid JSON content:\n{str(e)}\n\nPlease fix the JSON syntax and try again."
                )
                self.status_label.setText("JSON minification failed - invalid syntax")
                return
            
            # Minify (no indentation, no extra spaces)
            minified_json = json.dumps(parsed_json, separators=(',', ':'), ensure_ascii=False)
            
            # Replace content
            self.editor.setPlainText(minified_json)
            
            self.status_label.setText("JSON minified successfully")
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Minify Error", 
                f"Failed to minify JSON:\n{str(e)}"
            )
            self.status_label.setText("JSON minification failed")
            
    def validate_json(self):
        """Validate JSON syntax and show detailed information."""
        try:
            # Get current text
            current_text = self.editor.toPlainText().strip()
            
            if not current_text:
                QMessageBox.information(self, "JSON Validation", "No content to validate")
                self.status_label.setText("No content to validate")
                return
                
            # Parse JSON
            try:
                parsed_json = json.loads(current_text)
                
                # Count elements for information
                if isinstance(parsed_json, dict):
                    element_count = len(parsed_json)
                    element_type = "object"
                elif isinstance(parsed_json, list):
                    element_count = len(parsed_json)
                    element_type = "array"
                else:
                    element_count = 1
                    element_type = "value"
                
                # Show success message with details
                QMessageBox.information(
                    self, 
                    "JSON Validation",
                    f"✅ Valid JSON!\n\n"
                    f"Type: {element_type}\n"
                    f"Elements: {element_count}\n"
                    f"Size: {len(current_text)} characters"
                )
                self.status_label.setText("JSON is valid")
                
            except json.JSONDecodeError as e:
                # Show detailed error information
                error_details = f"❌ Invalid JSON!\n\n"
                error_details += f"Error: {e.msg}\n"
                error_details += f"Line: {e.lineno}\n"
                error_details += f"Column: {e.colno}\n"
                
                if e.pos:
                    error_details += f"Position: {e.pos}\n"
                    
                    # Try to show the problematic part
                    start_pos = max(0, e.pos - 20)
                    end_pos = min(len(current_text), e.pos + 20)
                    context = current_text[start_pos:end_pos]
                    error_details += f"\nContext: ...{context}..."
                
                QMessageBox.warning(self, "JSON Validation", error_details)
                self.status_label.setText("JSON validation failed")
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Validation Error", 
                f"Failed to validate JSON:\n{str(e)}"
            )
            self.status_label.setText("JSON validation error")
                
    def close_editor(self):
        """Close the editor with save confirmation if needed."""
        if self.content_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "The file has unsaved changes. Do you want to save before closing?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_file()
                # Wait for save to complete before closing
                if self.upload_worker and self.upload_worker.isRunning():
                    self.upload_worker.finished.connect(self.accept)
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return
                
        self.accept()
        
    def closeEvent(self, event):
        """Handle close event."""
        if self.content_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "The file has unsaved changes. Do you want to save before closing?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_file()
                event.ignore()  # Prevent closing until save completes
                if self.upload_worker and self.upload_worker.isRunning():
                    self.upload_worker.finished.connect(lambda: event.accept())
                return
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
                
        # Clean up
        if self.upload_worker and self.upload_worker.isRunning():
            self.upload_worker.terminate()
            self.upload_worker.wait(1000)
            
        event.accept()
        
    def apply_theme(self, theme_name: str):
        """Apply theme styling to the dialog."""
        theme_colors = theme_manager.get_theme_colors()
        
        if theme_name == "dark":
            style = f"""
                QDialog {{
                    background-color: #2b2b2b;
                    color: #ffffff;
                }}
                
                QMenuBar {{
                    background-color: #363636;
                    color: #ffffff;
                    border-bottom: 1px solid #555555;
                }}
                
                QMenuBar::item:selected {{
                    background-color: #484848;
                }}
                
                QMenu {{
                    background-color: #363636;
                    color: #ffffff;
                    border: 1px solid #555555;
                }}
                
                QMenu::item:selected {{
                    background-color: #484848;
                }}
                
                QLabel {{
                    color: #ffffff;
                }}
                
                QFrame {{
                    border: 1px solid #555555;
                    background-color: #363636;
                }}
                
                QCheckBox {{
                    color: #ffffff;
                }}
                
                QPushButton {{
                    background-color: #363636;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 8px 16px;
                    border-radius: 4px;
                }}
                
                QPushButton:hover {{
                    background-color: #484848;
                }}
                
                QPushButton:pressed {{
                    background-color: #555555;
                }}
            """
        else:
            style = f"""
                QDialog {{
                    background-color: #ffffff;
                    color: #000000;
                }}
                
                QMenuBar {{
                    background-color: #e0e0e0;
                    color: #000000;
                    border-bottom: 1px solid #c0c0c0;
                }}
                
                QMenuBar::item:selected {{
                    background-color: #d0d0d0;
                }}
                
                QMenu {{
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #c0c0c0;
                }}
                
                QMenu::item:selected {{
                    background-color: #e0e0e0;
                }}
                
                QLabel {{
                    color: #000000;
                }}
                
                QFrame {{
                    border: 1px solid #c0c0c0;
                    background-color: #f0f0f0;
                }}
                
                QCheckBox {{
                    color: #000000;
                }}
                
                QPushButton {{
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #c0c0c0;
                    padding: 8px 16px;
                    border-radius: 4px;
                }}
                
                QPushButton:hover {{
                    background-color: #e0e0e0;
                }}
                
                QPushButton:pressed {{
                    background-color: #d0d0d0;
                }}
            """
            
        self.setStyleSheet(style)
        
        # Apply theme to the embedded CodeEditor (this is the important part!)
        if hasattr(self, 'editor'):
            self.editor.apply_theme(theme_name)
            # Force immediate update
            self.editor.update()
            self.editor.line_number_area.update()
            # Force repaint
            self.editor.repaint()


class FileDownloadWorker(QThread):
    """Worker thread for downloading file content from device."""
    
    content_loaded = pyqtSignal(str)  # content
    error_occurred = pyqtSignal(str)  # error_message
    
    def __init__(self, file_info: FileInfo, file_ops: FileOperations):
        super().__init__()
        self.file_info = file_info
        self.file_ops = file_ops
        self.logger = get_logger(__name__)
        
    def run(self):
        """Execute the file download."""
        try:
            # Create event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Create temporary file for download
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as temp_file:
                    temp_path = Path(temp_file.name)  # Convert to Path object
                
                # Download from device
                success = loop.run_until_complete(
                    self.file_ops.pull_file(self.file_info.path, temp_path)
                )
                
                if success:
                    # Read content
                    try:
                        with open(temp_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        self.content_loaded.emit(content)
                    except UnicodeDecodeError:
                        # Try with different encoding
                        try:
                            with open(temp_path, 'r', encoding='latin-1') as f:
                                content = f.read()
                            self.content_loaded.emit(content)
                        except Exception as e:
                            self.error_occurred.emit(f"Failed to read file content: {str(e)}")
                else:
                    self.error_occurred.emit("Failed to download file from device")
                
                # Clean up temp file
                temp_path.unlink(missing_ok=True)
                    
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Error downloading file: {e}")
            self.error_occurred.emit(f"Download error: {str(e)}")
