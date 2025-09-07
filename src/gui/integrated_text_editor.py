"""
Integrated Text Editor

A built-in text editor for editing device files within the application.
Provides syntax highlighting, line numbers, and basic editing features.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
    QPushButton, QDialog, QMessageBox, QFrame, QStatusBar,
    QMenuBar, QMenu, QFileDialog, QInputDialog, QSplitter,
    QPlainTextEdit, QCheckBox, QSpinBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import (
    QFont, QFontMetrics, QPainter, QColor, QPalette,
    QTextCursor, QTextFormat, QSyntaxHighlighter,
    QTextDocument, QAction, QKeySequence
)

from src.adb.file_operations import FileOperations, FileInfo
from src.utils.logger import get_logger


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
        painter.fillRect(event.rect(), QColor(240, 240, 240))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(120, 120, 120))
                painter.drawText(
                    0, int(top), 
                    self.line_number_area.width(), 
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
            
            line_color = QColor(Qt.GlobalColor.yellow).lighter(160)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
            
        self.setExtraSelections(extra_selections)


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
