"""
Script Editor Dialog

Integrated text editor dialog for creating and editing scripts.
Supports syntax highlighting for batch files and shell scripts.
"""

import os
import re
from pathlib import Path
from typing import Optional, Dict

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
    QPushButton, QMessageBox, QFrame, QComboBox, QLineEdit,
    QFormLayout, QPlainTextEdit, QFileDialog, QSplitter,
    QGroupBox, QCheckBox, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QFont, QFontMetrics, QPainter, QColor, QPalette,
    QTextCursor, QTextFormat, QSyntaxHighlighter,
    QTextDocument, QAction, QKeySequence, QTextCharFormat
)

from services.script_manager import Script, ScriptType
from utils.logger import get_logger
from utils.theme_manager import theme_manager


class LineNumberArea(QWidget):
    """Widget for displaying line numbers alongside the text editor."""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        
    def sizeHint(self):
        return self.editor.line_number_area_width()
        
    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class ScriptSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for script files."""
    
    def __init__(self, document, script_type: ScriptType):
        super().__init__(document)
        self.script_type = script_type
        self.highlighting_rules = []
        self.setup_highlighting_rules()
        
    def setup_highlighting_rules(self):
        """Setup syntax highlighting rules based on script type."""
        self.highlighting_rules.clear()
        
        # Keywords format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(86, 156, 214))  # Blue
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        # Comments format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(106, 153, 85))  # Green
        comment_format.setFontItalic(True)
        
        # Strings format
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(206, 145, 120))  # Orange
        
        # Variables format
        variable_format = QTextCharFormat()
        variable_format.setForeground(QColor(156, 220, 254))  # Light blue
        
        # Commands format
        command_format = QTextCharFormat()
        command_format.setForeground(QColor(220, 220, 170))  # Yellow
        
        if self.script_type == ScriptType.HOST_WINDOWS:
            # Windows batch file highlighting
            
            # Keywords
            keywords = [
                r'\\b(echo|set|if|else|for|goto|call|exit|pause|rem|del|copy|move|mkdir|rmdir|cd|dir|type|findstr|sort)\\b'
            ]
            for pattern in keywords:
                self.highlighting_rules.append((re.compile(pattern, re.IGNORECASE), keyword_format))
            
            # Comments (REM and ::)
            self.highlighting_rules.append((re.compile(r'\\brem\\b.*$', re.IGNORECASE | re.MULTILINE), comment_format))
            self.highlighting_rules.append((re.compile(r'^::.*$', re.MULTILINE), comment_format))
            
            # Variables (%VAR%)
            self.highlighting_rules.append((re.compile(r'%[^%]*%'), variable_format))
            
            # Strings (quoted text)
            self.highlighting_rules.append((re.compile(r'"[^"]*"'), string_format))
            
        else:  # Shell scripts (Linux or device)
            # Shell script highlighting
            
            # Keywords
            keywords = [
                r'\\b(if|then|else|elif|fi|for|while|do|done|case|esac|function|return|break|continue|exit|echo|printf|read|test|source|export|alias|unset|cd|pwd|ls|cat|grep|sed|awk|sort|uniq|head|tail|wc|find|chmod|chown|mkdir|rmdir|cp|mv|rm|ln)\\b'
            ]
            for pattern in keywords:
                self.highlighting_rules.append((re.compile(pattern), keyword_format))
            
            # Comments (#)
            self.highlighting_rules.append((re.compile(r'#.*$', re.MULTILINE), comment_format))
            
            # Variables ($VAR, ${VAR})
            self.highlighting_rules.append((re.compile(r'\\$\\{?[A-Za-z_][A-Za-z0-9_]*\\}?'), variable_format))
            
            # Strings (single and double quoted)
            self.highlighting_rules.append((re.compile(r'"[^"]*"'), string_format))
            self.highlighting_rules.append((re.compile(r"'[^']*'"), string_format))
            
            # Commands in backticks
            self.highlighting_rules.append((re.compile(r'`[^`]*`'), command_format))
            
    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text."""
        for pattern, format_obj in self.highlighting_rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format_obj)


class ScriptCodeEditor(QPlainTextEdit):
    """Enhanced text editor for script editing with line numbers."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.line_number_area = LineNumberArea(self)
        self.highlighter = None
        
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
        
        # Apply theme
        self.apply_theme()
        
    def set_script_type(self, script_type: ScriptType):
        """Set script type for syntax highlighting."""
        if self.highlighter:
            self.highlighter.setDocument(None)
        
        self.highlighter = ScriptSyntaxHighlighter(self.document(), script_type)
        
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
            cr.left(), cr.top(), self.line_number_area_width(), cr.height()
        )
        
    def line_number_area_paint_event(self, event):
        """Paint line numbers."""
        painter = QPainter(self.line_number_area)
        
        # Get theme colors
        if hasattr(theme_manager, 'get_current_theme') and theme_manager.get_current_theme() == 'dark':
            bg_color = QColor(45, 45, 45)
            text_color = QColor(150, 150, 150)
            border_color = QColor(60, 60, 60)
        else:
            bg_color = QColor(245, 245, 245)
            text_color = QColor(100, 100, 100)
            border_color = QColor(200, 200, 200)
        
        painter.fillRect(event.rect(), bg_color)
        
        # Draw border
        painter.setPen(border_color)
        painter.drawLine(event.rect().topRight(), event.rect().bottomRight())
        
        # Draw line numbers
        painter.setPen(text_color)
        painter.setFont(self.font())
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0, int(top), self.line_number_area.width() - 3, 
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
            
            # Get theme colors
            if hasattr(theme_manager, 'get_current_theme') and theme_manager.get_current_theme() == 'dark':
                line_color = QColor(40, 40, 40)
            else:
                line_color = QColor(250, 250, 250)
            
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
            
        self.setExtraSelections(extra_selections)
        
    def apply_theme(self):
        """Apply current theme to the editor."""
        if hasattr(theme_manager, 'get_current_theme') and theme_manager.get_current_theme() == 'dark':
            # Dark theme colors
            bg_color = "#2d2d2d"
            text_color = "#d4d4d4"
            border_color = "#3c3c3c"
            selection_bg = "#264f78"
            selection_fg = "#ffffff"
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
        """
        
        self.setStyleSheet(style)
        
        # Update line number area
        self.line_number_area.update()
        
        # Re-highlight current line
        self.highlight_current_line()


class ScriptEditorDialog(QDialog):
    """Dialog for creating and editing scripts with integrated editor."""
    
    script_saved = pyqtSignal(str)  # script_id
    
    def __init__(self, script: Optional[Script] = None, parent=None):
        super().__init__(parent)
        self.script = script
        self.logger = get_logger(__name__)
        self.is_new_script = script is None
        self.content_modified = False
        self.original_content = ""
        
        self.setWindowTitle("Script Editor" if self.is_new_script else f"Edit Script: {script.name}")
        self.setModal(True)
        self.resize(900, 700)
        
        self.setup_ui()
        self.apply_theme()
        
        if not self.is_new_script:
            self.load_script_content()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Create splitter for properties and editor
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)
        
        # Properties section
        props_widget = self.create_properties_section()
        splitter.addWidget(props_widget)
        
        # Editor section
        editor_widget = self.create_editor_section()
        splitter.addWidget(editor_widget)
        
        # Set splitter proportions (properties smaller, editor larger)
        splitter.setSizes([150, 550])
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Template button
        template_btn = QPushButton("📄 Load Template")
        template_btn.clicked.connect(self.load_template)
        button_layout.addWidget(template_btn)
        
        # Import button
        import_btn = QPushButton("📁 Import File")
        import_btn.clicked.connect(self.import_file)
        button_layout.addWidget(import_btn)
        
        button_layout.addStretch()
        
        # Save button
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self.save_script)
        button_layout.addWidget(self.save_btn)
        
        # Save As button
        save_as_btn = QPushButton("💾 Save As...")
        save_as_btn.clicked.connect(self.save_as_script)
        button_layout.addWidget(save_as_btn)
        
        # Cancel button
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Connect content change signal
        self.editor.textChanged.connect(self.on_content_changed)
        
        # Set initial focus
        if self.is_new_script:
            self.name_edit.setFocus()
        else:
            self.editor.setFocus()
    
    def create_properties_section(self) -> QWidget:
        """Create script properties section."""
        group = QGroupBox("Script Properties")
        layout = QFormLayout(group)
        
        # Script name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter script name")
        if not self.is_new_script:
            self.name_edit.setText(self.script.name)
        layout.addRow("Name:", self.name_edit)
        
        # Script type
        self.type_combo = QComboBox()
        self.type_combo.addItem("Host Script (Windows .bat)", ScriptType.HOST_WINDOWS)
        self.type_combo.addItem("Host Script (Linux .sh)", ScriptType.HOST_LINUX)
        self.type_combo.addItem("Device Script (.sh)", ScriptType.DEVICE)
        
        if self.is_new_script:
            # Set default based on OS
            if os.name == 'nt':
                self.type_combo.setCurrentIndex(0)  # Windows
            else:
                self.type_combo.setCurrentIndex(1)  # Linux
        else:
            # Set based on existing script
            type_index = {
                ScriptType.HOST_WINDOWS: 0,
                ScriptType.HOST_LINUX: 1,
                ScriptType.DEVICE: 2
            }.get(self.script.script_type, 0)
            self.type_combo.setCurrentIndex(type_index)
        
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        layout.addRow("Type:", self.type_combo)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Optional description")
        self.description_edit.setMaximumHeight(80)
        if not self.is_new_script:
            self.description_edit.setText(self.script.description)
        layout.addRow("Description:", self.description_edit)
        
        return group
    
    def create_editor_section(self) -> QWidget:
        """Create editor section."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Editor header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Script Content:"))
        header_layout.addStretch()
        
        # Status label
        self.status_label = QLabel("Ready")
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Editor
        self.editor = ScriptCodeEditor()
        layout.addWidget(self.editor)
        
        # Set initial syntax highlighting
        self.on_type_changed()
        
        return widget
    
    def on_type_changed(self):
        """Handle script type change."""
        script_type = self.type_combo.currentData()
        self.editor.set_script_type(script_type)
        
        # Update editor content with template if it's empty
        if not self.editor.toPlainText().strip():
            self.load_default_template(script_type)
    
    def load_default_template(self, script_type: ScriptType):
        """Load default template for script type."""
        if script_type == ScriptType.HOST_WINDOWS:
            template = '''@echo off
echo Starting script execution...
echo.

REM Add your commands here
echo Hello from Windows batch script!

REM Example: List files in current directory
dir

echo.
echo Script execution completed.
pause'''
        elif script_type == ScriptType.HOST_LINUX:
            template = '''#!/bin/bash
echo "Starting script execution..."
echo

# Add your commands here
echo "Hello from Linux shell script!"

# Example: List files in current directory
ls -la

echo
echo "Script execution completed."'''
        else:  # DEVICE
            template = '''#!/system/bin/sh
echo "Starting device script execution..."
echo

# Add your commands here
echo "Hello from device shell script!"

# Example: Get device info
getprop ro.product.model
getprop ro.build.version.release

echo
echo "Device script execution completed."'''
        
        self.editor.setPlainText(template)
        self.original_content = template
        self.content_modified = False
    
    def load_template(self):
        """Load a predefined template."""
        script_type = self.type_combo.currentData()
        
        templates = {
            ScriptType.HOST_WINDOWS: {
                "System Info": '''@echo off
echo Collecting system information...
echo.

echo System Information:
systeminfo | findstr /C:"OS Name" /C:"OS Version" /C:"System Type"

echo.
echo Disk Space:
wmic logicaldisk get size,freespace,caption

echo.
echo Running Processes:
tasklist | findstr /C:"notepad" /C:"chrome" /C:"firefox"

pause''',
                "ADB Check": '''@echo off
echo Checking ADB status...
echo.

echo ADB Version:
adb version

echo.
echo Connected Devices:
adb devices

echo.
echo Device Properties:
for /f "tokens=1" %%i in ('adb devices ^| findstr device ^| head -1') do (
    adb -s %%i shell getprop ro.product.model
    adb -s %%i shell getprop ro.build.version.release
)

pause'''
            },
            ScriptType.HOST_LINUX: {
                "System Info": '''#!/bin/bash
echo "Collecting system information..."
echo

echo "System Information:"
uname -a

echo
echo "Memory Usage:"
free -h

echo
echo "Disk Usage:"
df -h

echo
echo "Network Interfaces:"
ip addr show | grep -E "inet|UP"''',
                "ADB Check": '''#!/bin/bash
echo "Checking ADB status..."
echo

echo "ADB Version:"
adb version

echo
echo "Connected Devices:"
adb devices

echo
echo "Device Properties:"
DEVICE=$(adb devices | grep -v "List" | grep "device" | head -1 | cut -f1)
if [ ! -z "$DEVICE" ]; then
    adb -s $DEVICE shell getprop ro.product.model
    adb -s $DEVICE shell getprop ro.build.version.release
fi'''
            },
            ScriptType.DEVICE: {
                "Device Info": '''#!/system/bin/sh
echo "Collecting device information..."
echo

echo "Device Model:"
getprop ro.product.model

echo "Android Version:"
getprop ro.build.version.release

echo "CPU Info:"
cat /proc/cpuinfo | grep -E "processor|model name" | head -4

echo "Memory Info:"
cat /proc/meminfo | grep -E "MemTotal|MemFree"''',
                "Performance Monitor": '''#!/system/bin/sh
echo "Device performance monitoring..."
echo

echo "CPU Usage:"
top -n 1 | head -10

echo "Memory Usage:"
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable"

echo "Battery Status:"
dumpsys battery | grep -E "level|temperature|voltage"

echo "Storage Usage:"
df | grep -E "/data|/system"'''
            }
        }
        
        available_templates = templates.get(script_type, {})
        if not available_templates:
            QMessageBox.information(self, "No Templates", "No templates available for this script type.")
            return
        
        # Show template selection dialog
        from PyQt6.QtWidgets import QInputDialog
        template_name, ok = QInputDialog.getItem(
            self, "Select Template", "Choose a template:",
            list(available_templates.keys()), 0, False
        )
        
        if ok and template_name:
            template_content = available_templates[template_name]
            self.editor.setPlainText(template_content)
            self.original_content = template_content
            self.content_modified = False
            self.status_label.setText(f"Template '{template_name}' loaded")
    
    def import_file(self):
        """Import script content from file."""
        script_type = self.type_combo.currentData()
        
        if script_type == ScriptType.HOST_WINDOWS:
            file_filter = "Batch Files (*.bat);;All Files (*)"
        else:
            file_filter = "Shell Scripts (*.sh);;All Files (*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Script File", str(Path.home()), file_filter
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.editor.setPlainText(content)
                self.original_content = content
                self.content_modified = False
                
                # Auto-fill name if empty
                if not self.name_edit.text():
                    name = Path(file_path).stem
                    self.name_edit.setText(name)
                
                self.status_label.setText(f"Imported from {Path(file_path).name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import file:\n{e}")
    
    def load_script_content(self):
        """Load existing script content."""
        if self.script and Path(self.script.script_path).exists():
            try:
                with open(self.script.script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.editor.setPlainText(content)
                self.original_content = content
                self.content_modified = False
                self.status_label.setText("Script loaded")
                
            except Exception as e:
                self.logger.error(f"Failed to load script content: {e}")
                QMessageBox.critical(self, "Load Error", f"Failed to load script content:\n{e}")
    
    def on_content_changed(self):
        """Handle content changes."""
        if hasattr(self, 'original_content'):
            self.content_modified = (self.editor.toPlainText() != self.original_content)
            self.update_title()
    
    def update_title(self):
        """Update dialog title with modification indicator."""
        base_title = "Script Editor" if self.is_new_script else f"Edit Script: {self.script.name}"
        if self.content_modified:
            self.setWindowTitle(f"{base_title} *")
        else:
            self.setWindowTitle(base_title)
    
    def save_script(self):
        """Save the script."""
        if not self.validate_input():
            return
        
        name = self.name_edit.text().strip()
        script_type = self.type_combo.currentData()
        description = self.description_edit.toPlainText().strip()
        content = self.editor.toPlainText()
        
        try:
            # Determine file extension
            if script_type == ScriptType.HOST_WINDOWS:
                extension = ".bat"
            else:
                extension = ".sh"
            
            # Create scripts directory if it doesn't exist
            scripts_dir = Path.home() / ".adb-util" / "user_scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate file path
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            script_path = scripts_dir / f"{safe_name}{extension}"
            
            # Save content to file
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Make shell scripts executable on Unix systems
            if script_type in [ScriptType.HOST_LINUX, ScriptType.DEVICE] and os.name != 'nt':
                os.chmod(script_path, 0o755)
            
            # Update or create script in manager
            if self.is_new_script:
                from services.script_manager import get_script_manager
                script_manager = get_script_manager()
                script_id = script_manager.add_script(name, script_type, str(script_path), description)
                self.script_saved.emit(script_id)
            else:
                # Update existing script
                if str(script_path) != self.script.script_path:
                    # Path changed, remove old file if it exists
                    old_path = Path(self.script.script_path)
                    if old_path.exists() and old_path != script_path:
                        try:
                            old_path.unlink()
                        except Exception as e:
                            self.logger.warning(f"Could not remove old script file: {e}")
                
                from services.script_manager import get_script_manager
                script_manager = get_script_manager()
                script_manager.update_script(
                    self.script.id,
                    name=name,
                    script_type=script_type,
                    script_path=str(script_path),
                    description=description
                )
                self.script_saved.emit(self.script.id)
            
            self.original_content = content
            self.content_modified = False
            self.status_label.setText(f"Script saved to {script_path.name}")
            self.update_title()
            
            QMessageBox.information(self, "Success", f"Script saved successfully to:\n{script_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save script: {e}")
            QMessageBox.critical(self, "Save Error", f"Failed to save script:\n{e}")
    
    def save_as_script(self):
        """Save script to a custom location."""
        script_type = self.type_combo.currentData()
        
        if script_type == ScriptType.HOST_WINDOWS:
            file_filter = "Batch Files (*.bat);;All Files (*)"
            default_ext = ".bat"
        else:
            file_filter = "Shell Scripts (*.sh);;All Files (*)"
            default_ext = ".sh"
        
        default_name = self.name_edit.text().strip() or "script"
        default_name = "".join(c for c in default_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        default_name = default_name.replace(' ', '_') + default_ext
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Script As", str(Path.home() / default_name), file_filter
        )
        
        if file_path:
            try:
                content = self.editor.toPlainText()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Make shell scripts executable on Unix systems
                if script_type in [ScriptType.HOST_LINUX, ScriptType.DEVICE] and os.name != 'nt':
                    os.chmod(file_path, 0o755)
                
                self.status_label.setText(f"Script saved to {Path(file_path).name}")
                QMessageBox.information(self, "Success", f"Script saved to:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save script:\n{e}")
    
    def validate_input(self) -> bool:
        """Validate user input."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a script name.")
            self.name_edit.setFocus()
            return False
        
        content = self.editor.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Validation Error", "Please enter script content.")
            self.editor.setFocus()
            return False
        
        return True
    
    def apply_theme(self):
        """Apply current theme."""
        if hasattr(theme_manager, 'apply_theme'):
            theme_manager.apply_theme(self)
    
    def closeEvent(self, event):
        """Handle close event."""
        if self.content_modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_script()
                # Only close if save was successful (no exception)
                if not self.content_modified:
                    event.accept()
                else:
                    event.ignore()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:  # Cancel
                event.ignore()
        else:
            event.accept()
