"""
Logging UI

Real-time logcat viewer with filtering and search capabilities.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QComboBox, QCheckBox,
    QLabel, QFrame, QSplitter, QTabWidget,
    QSpinBox, QGroupBox, QScrollArea, QMessageBox,
    QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat


class LogEntry:
    """Represents a single log entry."""
    
    def __init__(self, timestamp, level, tag, pid, message):
        self.timestamp = timestamp
        self.level = level
        self.tag = tag
        self.pid = pid
        self.message = message


class Logging(QWidget):
    """Logging widget for viewing and filtering device logs."""
    
    def __init__(self, device_id: str):
        super().__init__()
        self.device_id = device_id
        self.is_capturing = False
        self.log_entries = []
        self.filtered_entries = []
        self.init_ui()
        self.setup_timer()
    
    def init_ui(self):
        """Initialize the logging UI."""
        layout = QHBoxLayout(self)
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Create log viewer panel
        log_panel = self.create_log_panel()
        splitter.addWidget(log_panel)
        
        # Create filter panel
        filter_panel = self.create_filter_panel()
        splitter.addWidget(filter_panel)
        
        # Set splitter proportions
        splitter.setSizes([700, 300])
    
    def create_log_panel(self):
        """Create the main log viewing panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Log controls header
        controls_layout = QHBoxLayout()
        
        log_label = QLabel(f"📋 Logcat - {self.device_id}")
        log_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        controls_layout.addWidget(log_label)
        
        controls_layout.addStretch()
        
        # Capture controls
        self.start_btn = QPushButton("▶️ Start Capture")
        self.start_btn.clicked.connect(self.toggle_capture)
        controls_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_capture)
        controls_layout.addWidget(self.stop_btn)
        
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_logs)
        controls_layout.addWidget(clear_btn)
        
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_logs)
        controls_layout.addWidget(save_btn)
        
        layout.addLayout(controls_layout)
        
        # Status bar
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Status: Ready")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.entry_count_label = QLabel("Entries: 0")
        status_layout.addWidget(self.entry_count_label)
        
        self.capture_rate_label = QLabel("Rate: 0/sec")
        status_layout.addWidget(self.capture_rate_label)
        
        layout.addLayout(status_layout)
        
        # Search bar
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("🔍 Search:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search logs...")
        self.search_input.textChanged.connect(self.search_logs)
        search_layout.addWidget(self.search_input)
        
        self.search_case_sensitive = QCheckBox("Case sensitive")
        search_layout.addWidget(self.search_case_sensitive)
        
        self.search_regex = QCheckBox("Regex")
        search_layout.addWidget(self.search_regex)
        
        layout.addLayout(search_layout)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setFont(QFont("Consolas", 9))
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #333333;
            }
        """)
        layout.addWidget(self.log_display)
        
        # Auto-scroll checkbox
        auto_scroll_layout = QHBoxLayout()
        self.auto_scroll_checkbox = QCheckBox("Auto-scroll to bottom")
        self.auto_scroll_checkbox.setChecked(True)
        auto_scroll_layout.addWidget(self.auto_scroll_checkbox)
        
        auto_scroll_layout.addStretch()
        
        # Buffer size
        auto_scroll_layout.addWidget(QLabel("Buffer size:"))
        self.buffer_size_spin = QSpinBox()
        self.buffer_size_spin.setRange(100, 10000)
        self.buffer_size_spin.setValue(1000)
        self.buffer_size_spin.setSuffix(" lines")
        auto_scroll_layout.addWidget(self.buffer_size_spin)
        
        layout.addLayout(auto_scroll_layout)
        
        return panel
    
    def create_filter_panel(self):
        """Create the filter and settings panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Header
        filter_label = QLabel("🔧 Filters & Settings")
        filter_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(filter_label)
        
        # Create scroll area for filters
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Log Level Filter
        level_group = QGroupBox("Log Levels")
        level_layout = QVBoxLayout(level_group)
        
        self.level_checkboxes = {}
        levels = [
            ("Verbose", "V", "#888888"),
            ("Debug", "D", "#00ff00"),
            ("Info", "I", "#0080ff"),
            ("Warning", "W", "#ffff00"),
            ("Error", "E", "#ff8000"),
            ("Fatal", "F", "#ff0000")
        ]
        
        for level_name, level_code, color in levels:
            checkbox = QCheckBox(f"{level_name} ({level_code})")
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.apply_filters)
            checkbox.setStyleSheet(f"QCheckBox {{ color: {color}; }}")
            self.level_checkboxes[level_code] = checkbox
            level_layout.addWidget(checkbox)
        
        scroll_layout.addWidget(level_group)
        
        # Tag Filter
        tag_group = QGroupBox("Tag Filters")
        tag_layout = QVBoxLayout(tag_group)
        
        tag_input_layout = QHBoxLayout()
        self.tag_filter_input = QLineEdit()
        self.tag_filter_input.setPlaceholderText("Enter tag to filter...")
        tag_input_layout.addWidget(self.tag_filter_input)
        
        add_tag_btn = QPushButton("Add")
        add_tag_btn.clicked.connect(self.add_tag_filter)
        tag_input_layout.addWidget(add_tag_btn)
        
        tag_layout.addLayout(tag_input_layout)
        
        # Tag filter list
        self.tag_filter_list = QWidget()
        self.tag_filter_layout = QVBoxLayout(self.tag_filter_list)
        tag_layout.addWidget(self.tag_filter_list)
        
        scroll_layout.addWidget(tag_group)
        
        # PID Filter
        pid_group = QGroupBox("Process ID (PID) Filter")
        pid_layout = QVBoxLayout(pid_group)
        
        self.pid_filter_enabled = QCheckBox("Enable PID filtering")
        self.pid_filter_enabled.stateChanged.connect(self.apply_filters)
        pid_layout.addWidget(self.pid_filter_enabled)
        
        pid_input_layout = QHBoxLayout()
        pid_input_layout.addWidget(QLabel("PID:"))
        
        self.pid_filter_input = QSpinBox()
        self.pid_filter_input.setRange(0, 99999)
        self.pid_filter_input.valueChanged.connect(self.apply_filters)
        pid_input_layout.addWidget(self.pid_filter_input)
        
        pid_layout.addLayout(pid_input_layout)
        
        scroll_layout.addWidget(pid_group)
        
        # Highlight Settings
        highlight_group = QGroupBox("Highlighting")
        highlight_layout = QVBoxLayout(highlight_group)
        
        self.highlight_enabled = QCheckBox("Enable keyword highlighting")
        self.highlight_enabled.setChecked(True)
        highlight_layout.addWidget(self.highlight_enabled)
        
        highlight_input_layout = QHBoxLayout()
        self.highlight_input = QLineEdit()
        self.highlight_input.setPlaceholderText("Keywords to highlight...")
        highlight_input_layout.addWidget(self.highlight_input)
        
        add_highlight_btn = QPushButton("Add")
        add_highlight_btn.clicked.connect(self.add_highlight_keyword)
        highlight_input_layout.addWidget(add_highlight_btn)
        
        highlight_layout.addLayout(highlight_input_layout)
        
        scroll_layout.addWidget(highlight_group)
        
        # Export Settings
        export_group = QGroupBox("Export Options")
        export_layout = QVBoxLayout(export_group)
        
        self.export_timestamp = QCheckBox("Include timestamps")
        self.export_timestamp.setChecked(True)
        export_layout.addWidget(self.export_timestamp)
        
        self.export_filtered_only = QCheckBox("Export filtered logs only")
        self.export_filtered_only.setChecked(True)
        export_layout.addWidget(self.export_filtered_only)
        
        export_btn = QPushButton("📤 Export to File")
        export_btn.clicked.connect(self.export_logs)
        export_layout.addWidget(export_btn)
        
        scroll_layout.addWidget(export_group)
        
        # Add stretch to push everything to top
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        return panel
    
    def setup_timer(self):
        """Setup timer for simulating log capture."""
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.simulate_log_entry)
        
        self.rate_timer = QTimer()
        self.rate_timer.timeout.connect(self.update_capture_rate)
        self.rate_timer.start(1000)  # Update every second
        
        self.entry_count = 0
        self.last_entry_count = 0
    
    def toggle_capture(self):
        """Toggle log capture on/off."""
        if not self.is_capturing:
            self.start_capture()
        else:
            self.stop_capture()
    
    def start_capture(self):
        """Start capturing logs."""
        self.is_capturing = True
        self.start_btn.setText("⏸️ Pause")
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Status: Capturing...")
        
        # Start simulated log capture
        self.log_timer.start(100)  # New log every 100ms
    
    def stop_capture(self):
        """Stop capturing logs."""
        self.is_capturing = False
        self.start_btn.setText("▶️ Start Capture")
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: Stopped")
        
        # Stop log capture
        self.log_timer.stop()
    
    def simulate_log_entry(self):
        """Simulate a new log entry (for demo purposes)."""
        import random
        import datetime
        
        # Sample log data
        levels = ["V", "D", "I", "W", "E", "F"]
        tags = ["ActivityManager", "WindowManager", "PackageManager", "System", 
                "Bluetooth", "WiFi", "Camera", "MediaPlayer", "SurfaceFlinger"]
        messages = [
            "Service started successfully",
            "Connection established",
            "Data received from server",
            "Warning: Low memory condition",
            "Error: Failed to connect",
            "Debug: Processing request",
            "Info: System update available",
            "Critical: System failure detected"
        ]
        
        timestamp = datetime.datetime.now().strftime("%m-%d %H:%M:%S.%f")[:-3]
        level = random.choice(levels)
        tag = random.choice(tags)
        pid = random.randint(1000, 9999)
        message = random.choice(messages)
        
        log_entry = LogEntry(timestamp, level, tag, pid, message)
        self.add_log_entry(log_entry)
    
    def add_log_entry(self, entry):
        """Add a new log entry."""
        self.log_entries.append(entry)
        self.entry_count += 1
        
        # Apply filters
        if self.passes_filters(entry):
            self.filtered_entries.append(entry)
            self.display_log_entry(entry)
        
        # Update counters
        self.entry_count_label.setText(f"Entries: {len(self.log_entries)} (Filtered: {len(self.filtered_entries)})")
        
        # Maintain buffer size
        buffer_size = self.buffer_size_spin.value()
        if len(self.log_entries) > buffer_size:
            self.log_entries = self.log_entries[-buffer_size:]
        
        if len(self.filtered_entries) > buffer_size:
            self.filtered_entries = self.filtered_entries[-buffer_size:]
            self.refresh_display()
    
    def passes_filters(self, entry):
        """Check if log entry passes current filters."""
        # Level filter
        if not self.level_checkboxes[entry.level].isChecked():
            return False
        
        # PID filter
        if self.pid_filter_enabled.isChecked():
            if entry.pid != self.pid_filter_input.value():
                return False
        
        # Search filter
        search_text = self.search_input.text()
        if search_text:
            search_in = f"{entry.tag} {entry.message}"
            if not self.search_case_sensitive.isChecked():
                search_in = search_in.lower()
                search_text = search_text.lower()
            
            if self.search_regex.isChecked():
                import re
                try:
                    if not re.search(search_text, search_in):
                        return False
                except re.error:
                    return False
            else:
                if search_text not in search_in:
                    return False
        
        return True
    
    def display_log_entry(self, entry):
        """Display a single log entry."""
        # Color mapping for log levels
        colors = {
            "V": "#888888",  # Gray
            "D": "#00ff00",  # Green
            "I": "#0080ff",  # Blue
            "W": "#ffff00",  # Yellow
            "E": "#ff8000",  # Orange
            "F": "#ff0000"   # Red
        }
        
        # Format log line
        log_line = f"{entry.timestamp} {entry.level}/{entry.tag}({entry.pid}): {entry.message}"
        
        # Add to display
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Set color based on log level
        format = QTextCharFormat()
        format.setForeground(QColor(colors.get(entry.level, "#ffffff")))
        cursor.setCharFormat(format)
        
        cursor.insertText(log_line + "\n")
        
        # Auto-scroll if enabled
        if self.auto_scroll_checkbox.isChecked():
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.log_display.setTextCursor(cursor)
    
    def clear_logs(self):
        """Clear all logs."""
        self.log_entries.clear()
        self.filtered_entries.clear()
        self.log_display.clear()
        self.entry_count = 0
        self.entry_count_label.setText("Entries: 0")
    
    def save_logs(self):
        """Save logs to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Logs", 
            f"logcat_{self.device_id}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            # TODO: Implement actual file saving
            QMessageBox.information(self, "Save Logs", f"Logs saved to {filename}")
    
    def search_logs(self):
        """Search and filter logs based on search criteria."""
        self.apply_filters()
    
    def apply_filters(self):
        """Apply all active filters and refresh display."""
        self.filtered_entries.clear()
        
        for entry in self.log_entries:
            if self.passes_filters(entry):
                self.filtered_entries.append(entry)
        
        self.refresh_display()
        self.entry_count_label.setText(f"Entries: {len(self.log_entries)} (Filtered: {len(self.filtered_entries)})")
    
    def refresh_display(self):
        """Refresh the log display with filtered entries."""
        self.log_display.clear()
        
        for entry in self.filtered_entries:
            self.display_log_entry(entry)
    
    def add_tag_filter(self):
        """Add a new tag filter."""
        tag = self.tag_filter_input.text().strip()
        if tag:
            # TODO: Add tag filter widget
            self.tag_filter_input.clear()
    
    def add_highlight_keyword(self):
        """Add a keyword for highlighting."""
        keyword = self.highlight_input.text().strip()
        if keyword:
            # TODO: Implement keyword highlighting
            self.highlight_input.clear()
    
    def export_logs(self):
        """Export logs with current filters applied."""
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Logs", 
            f"logcat_export_{self.device_id}.txt",
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)"
        )
        
        if filename:
            # TODO: Implement actual export
            QMessageBox.information(self, "Export Logs", f"Logs exported to {filename}")
    
    def update_capture_rate(self):
        """Update the capture rate display."""
        current_count = len(self.log_entries)
        rate = current_count - self.last_entry_count
        self.last_entry_count = current_count
        self.capture_rate_label.setText(f"Rate: {rate}/sec")
