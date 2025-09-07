"""
Logging UI

Real-time logcat viewer with filtering and search capabilities.
"""

import asyncio
import re
from typing import List, Optional, Set
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QComboBox, QCheckBox,
    QLabel, QFrame, QSplitter, QTabWidget,
    QSpinBox, QGroupBox, QScrollArea, QMessageBox,
    QFileDialog, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat, QPalette

from adb.logcat_handler import LogcatHandler, LogEntry
from utils.logger import get_logger
from utils.constants import LOG_LEVELS, LOGCAT_FORMATS, LOGCAT_BUFFERS, MAX_LOG_BUFFER_SIZE


class LogcatWorker(QThread):
    """Worker thread for logcat streaming."""
    
    log_entry_received = pyqtSignal(object)
    stream_status_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, device_id: str):
        super().__init__()
        self.device_id = device_id
        self.logcat_handler = LogcatHandler(device_id)
        self.logger = get_logger(__name__)
        self.should_stop = False
        self.buffer = "main"
        self.format_type = "time"
        self.filter_spec = None
    
    def set_parameters(self, buffer: str, format_type: str, filter_spec: Optional[str] = None):
        """Set logcat parameters."""
        self.buffer = buffer
        self.format_type = format_type
        self.filter_spec = filter_spec
    
    def run(self):
        """Run logcat streaming."""
        try:
            # Emit that we're starting immediately
            self.stream_status_changed.emit(True)
            self.logger.info(f"LogcatWorker thread started for device: {self.device_id}")
            
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._stream_logcat())
            finally:
                loop.close()
        except Exception as e:
            self.logger.error(f"Logcat worker error: {e}")
            self.error_occurred.emit(str(e))
            self.stream_status_changed.emit(False)
    
    async def _stream_logcat(self):
        """Stream logcat asynchronously."""
        try:
            self.logger.info(f"Starting logcat stream for device: {self.device_id}")
            
            async for log_entry in self.logcat_handler.start_logcat_stream(
                buffer=self.buffer,
                filter_spec=self.filter_spec,
                format_type=self.format_type
            ):
                if self.should_stop:
                    self.logger.info("Logcat streaming stopped by user request")
                    break
                    
                if log_entry:
                    self.log_entry_received.emit(log_entry)
        
        except asyncio.CancelledError:
            self.logger.info("Logcat streaming was cancelled")
        except Exception as e:
            self.logger.error(f"Logcat streaming error: {e}")
            self.error_occurred.emit(str(e))
        
        finally:
            try:
                await self.logcat_handler.stop_logcat_stream()
                self.logger.info("Logcat handler stopped successfully")
            except Exception as e:
                self.logger.error(f"Error stopping logcat handler: {e}")
            self.stream_status_changed.emit(False)
    
    def stop_streaming(self):
        """Stop logcat streaming."""
        self.should_stop = True
        # Don't try to call async functions from here
        # The async loop will check should_stop flag


class Logging(QWidget):
    """Logging widget for viewing and filtering device logs."""
    
    def __init__(self, device_id: str):
        super().__init__()
        self.device_id = device_id
        self.logger = get_logger(__name__)
        self.is_capturing = False
        self.log_entries: List[LogEntry] = []
        self.filtered_entries: List[LogEntry] = []
        self.tag_filters: Set[str] = set()
        self.highlight_keywords: List[str] = []
        
        # Logcat components
        self.logcat_handler = LogcatHandler(device_id)
        self.logcat_worker = None
        
        # Statistics
        self.entry_count = 0
        self.last_entry_count = 0
        self.entries_per_second = 0
        
        self.logger.info(f"Initializing logcat viewer for device: {device_id}")
        self.init_ui()
        self.setup_timer()
        self.setup_logcat_callbacks()
        
        # Apply current theme after UI initialization with proper timing
        QApplication.processEvents()  # Process any pending events first
        
        # Apply theme immediately but efficiently
        self.refresh_theme()
        
        # Schedule only one delayed theme refresh to ensure full application
        QTimer.singleShot(100, self.refresh_theme_optimized)
        
        self.logger.info("Logcat viewer initialization complete")
    
    def setup_logcat_callbacks(self):
        """Setup callbacks for logcat handler."""
        self.logcat_handler.on_log_entry = self.on_new_log_entry
        self.logcat_handler.on_error = self.on_logcat_error
        self.logcat_handler.on_stream_status = self.on_stream_status_changed
    
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
        
        # Logcat format selection
        controls_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(LOGCAT_FORMATS)
        self.format_combo.setCurrentText("time")
        controls_layout.addWidget(self.format_combo)
        
        # Logcat buffer selection
        controls_layout.addWidget(QLabel("Buffer:"))
        self.buffer_combo = QComboBox()
        self.buffer_combo.addItems(LOGCAT_BUFFERS)
        self.buffer_combo.setCurrentText("main")
        controls_layout.addWidget(self.buffer_combo)
        
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
        self.search_input.setEnabled(True)  # Ensure it's enabled immediately
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
        
        # Set up QTextEdit to be more responsive to theme changes
        self.log_display.setAutoFillBackground(True)
        self.log_display.setBackgroundRole(QPalette.ColorRole.Base)
        
        # Remove hardcoded styling - let theme manager handle it
        layout.addWidget(self.log_display)
        
        # Auto-scroll checkbox
        auto_scroll_layout = QHBoxLayout()
        self.auto_scroll_checkbox = QCheckBox("Auto-scroll to bottom")
        self.auto_scroll_checkbox.setChecked(True)
        auto_scroll_layout.addWidget(self.auto_scroll_checkbox)
        
        auto_scroll_layout.addStretch()
        
        # Buffer size
        buffer_label = QLabel("Buffer size:")
        buffer_label.setMinimumWidth(80)  # Ensure label has sufficient width
        auto_scroll_layout.addWidget(buffer_label)
        self.buffer_size_spin = QSpinBox()
        self.buffer_size_spin.setRange(100, 10000)
        self.buffer_size_spin.setValue(1000)
        self.buffer_size_spin.setSuffix(" lines")
        self.buffer_size_spin.setMinimumWidth(120)  # Increase width for better visibility
        self.buffer_size_spin.setMinimumHeight(25)  # Increase height for better visibility
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
            # Remove hardcoded color styling - let theme manager handle it
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
        self.highlight_input.returnPressed.connect(self.add_highlight_keyword)  # Add Enter key support
        self.highlight_input.setEnabled(True)  # Ensure it's enabled immediately
        highlight_input_layout.addWidget(self.highlight_input)
        
        add_highlight_btn = QPushButton("Add")
        add_highlight_btn.clicked.connect(self.add_highlight_keyword)
        highlight_input_layout.addWidget(add_highlight_btn)
        
        clear_highlight_btn = QPushButton("Clear All")
        clear_highlight_btn.clicked.connect(self.clear_highlight_keywords)
        highlight_input_layout.addWidget(clear_highlight_btn)
        
        highlight_layout.addLayout(highlight_input_layout)
        
        # Add label to show current keywords
        self.keywords_label = QLabel("Keywords: None")
        # Remove hardcoded styling - let theme manager handle it
        self.keywords_label.setWordWrap(True)
        highlight_layout.addWidget(self.keywords_label)
        
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
        """Setup timer for statistics update."""
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
        try:
            # Provide immediate feedback and enable UI elements
            self.is_capturing = True
            self.start_btn.setText("⏸️ Pause")
            self.stop_btn.setEnabled(True)
            self.status_label.setText("Status: Starting...")
            
            # Ensure search and highlight functionality is immediately available
            self.search_input.setEnabled(True)
            self.highlight_input.setEnabled(True)
            
            # Process UI events IMMEDIATELY to show feedback
            QApplication.processEvents()
            
            # Get selected parameters
            buffer = self.buffer_combo.currentText()
            format_type = self.format_combo.currentText()
            
            # Create and start worker immediately for instant response
            try:
                self.logcat_worker = LogcatWorker(self.device_id)
                self.logcat_worker.set_parameters(buffer, format_type)
                self.logcat_worker.log_entry_received.connect(self.on_log_entry_received)
                self.logcat_worker.stream_status_changed.connect(self.on_stream_status_changed)
                self.logcat_worker.error_occurred.connect(self.on_logcat_error)
                
                # Start worker immediately
                self.logcat_worker.start()
                
                # Update status immediately
                self.status_label.setText("Status: Capturing...")
                
            except Exception as e:
                self.logger.error(f"Failed to create logcat worker: {e}")
                self.on_logcat_error(str(e))
            
            self.logger.info(f"Started logcat capture for device: {self.device_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to start capture: {e}")
            self.on_logcat_error(str(e))
            self.stop_capture()
    
    def stop_capture(self):
        """Stop capturing logs."""
        # Provide immediate feedback
        self.is_capturing = False
        self.start_btn.setText("▶️ Start Capture")
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: Stopping...")
        
        # Process UI events to show immediate feedback
        QApplication.processEvents()
        
        if self.logcat_worker and self.logcat_worker.isRunning():
            try:
                # Start non-blocking stop process
                self.logcat_worker.stop_streaming()
                
                # Use QTimer for non-blocking cleanup
                self.cleanup_timer = QTimer()
                self.cleanup_timer.setSingleShot(True)
                self.cleanup_timer.timeout.connect(self._cleanup_worker)
                self.cleanup_timer.start(100)  # Check after 100ms
                
            except Exception as e:
                self.logger.error(f"Error stopping worker: {e}")
                self._cleanup_worker()
        else:
            self.status_label.setText("Status: Stopped")
            self.logger.info("Logcat capture stopped")
    
    def _cleanup_worker(self):
        """Clean up worker thread (called by timer)."""
        if not self.logcat_worker:
            return
            
        try:
            if not self.logcat_worker.isRunning():
                # Worker stopped gracefully
                self.logcat_worker = None
                self.status_label.setText("Status: Stopped")
                self.logger.info("Logcat capture stopped")
                return
            
            # Check if we should wait more or force stop
            if not hasattr(self, '_stop_attempts'):
                self._stop_attempts = 0
            
            self._stop_attempts += 1
            
            if self._stop_attempts < 10:  # Wait up to 1 second (10 * 100ms)
                self.cleanup_timer.start(100)  # Check again in 100ms
            else:
                # Force terminate after 1 second
                self.logger.warning("Worker thread didn't stop gracefully, terminating...")
                self.logcat_worker.terminate()
                if not self.logcat_worker.wait(500):
                    self.logcat_worker.kill()
                self.logcat_worker = None
                self._stop_attempts = 0
                self.status_label.setText("Status: Stopped")
                self.logger.info("Logcat capture stopped (forced)")
                
        except Exception as e:
            self.logger.error(f"Error in worker cleanup: {e}")
            self.logcat_worker = None
            self._stop_attempts = 0
            self.status_label.setText("Status: Stopped")
    
    def on_log_entry_received(self, log_entry):
        """Handle new log entry from worker thread."""
        try:
            # log_entry is already a LogEntry from logcat_handler
            self.log_entries.append(log_entry)
            
            # Maintain buffer size
            if len(self.log_entries) > MAX_LOG_BUFFER_SIZE:
                self.log_entries = self.log_entries[-MAX_LOG_BUFFER_SIZE:]
            
            # Apply filters and update display
            if self.passes_filters(log_entry):
                self.filtered_entries.append(log_entry)
                self.display_log_entry(log_entry)
            
            # Update statistics
            self.update_entry_count()
            
        except Exception as e:
            self.logger.error(f"Error processing log entry: {e}")
    
    def update_entry_count(self):
        """Update the entry count display."""
        self.entry_count_label.setText(f"Entries: {len(self.log_entries)} (Filtered: {len(self.filtered_entries)})")
    
    def on_new_log_entry(self, log_entry):
        """Handle new log entry."""
        # Add to buffer
        self.log_entries.append(log_entry)
        
        # Maintain buffer size
        max_size = self.buffer_size_spin.value()
        if len(self.log_entries) > max_size:
            self.log_entries = self.log_entries[-max_size:]
        
        # Update count
        self.entry_count += 1
        
        # Apply filters and update display
        self.apply_filters()
    
    def on_stream_status_changed(self, is_streaming):
        """Handle stream status change."""
        if is_streaming:
            self.status_label.setText("Status: Capturing...")
        else:
            if self.is_capturing:
                self.status_label.setText("Status: Stream ended")
                self.stop_capture()
    
    def on_logcat_error(self, error_msg):
        """Handle logcat error."""
        self.logger.error(f"Logcat error: {error_msg}")
        self.status_label.setText(f"Status: Error - {error_msg}")
        QMessageBox.warning(self, "Logcat Error", f"Logcat error occurred:\n{error_msg}")
        self.stop_capture()
    
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
        
        # PID filter (skip for entries without PID like raw format)
        if self.pid_filter_enabled.isChecked() and entry.pid:
            try:
                if int(entry.pid) != self.pid_filter_input.value():
                    return False
            except ValueError:
                # Skip entries with non-numeric PIDs
                pass
        
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
        
        # Format log line based on entry content
        if entry.tag == "raw" or (not entry.timestamp and not entry.pid):
            # Raw format - display just the message
            log_line = entry.message
        else:
            # Structured format - display with metadata
            timestamp_part = f"{entry.timestamp} " if entry.timestamp else ""
            pid_part = f"({entry.pid})" if entry.pid else ""
            log_line = f"{timestamp_part}{entry.level}/{entry.tag}{pid_part}: {entry.message}"
        
        # Add to display
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Check if we have highlight keywords
        highlight_keywords = getattr(self, 'highlight_keywords', [])
        
        if highlight_keywords:
            # Apply highlighting by inserting text with different formats
            self._insert_highlighted_text(cursor, log_line, entry.level, colors, highlight_keywords)
        else:
            # Set color based on log level
            format = QTextCharFormat()
            format.setForeground(QColor(colors.get(entry.level, "#ffffff")))
            cursor.setCharFormat(format)
            cursor.insertText(log_line)
        
        cursor.insertText("\n")
        
        # Auto-scroll if enabled
        if self.auto_scroll_checkbox.isChecked():
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.log_display.setTextCursor(cursor)
    
    def clear_logs(self):
        """Clear all logs."""
        reply = QMessageBox.question(
            self, 
            "Clear Logs", 
            "Clear all logs? This will also clear the device logcat buffer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear local buffer
            self.log_entries.clear()
            self.filtered_entries.clear()
            self.log_display.clear()
            self.entry_count = 0
            self.last_entry_count = 0
            
            # Clear device logcat buffer asynchronously
            self._clear_device_logcat_async()
            
            self.entry_count_label.setText("Entries: 0 (Filtered: 0)")
            self.logger.info("Logs cleared")
    
    def _clear_device_logcat_async(self):
        """Clear device logcat buffer asynchronously."""
        import threading
        
        def clear_logcat():
            try:
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.logcat_handler.clear_logcat())
                    self.logger.info("Device logcat buffer cleared")
                finally:
                    loop.close()
            except Exception as e:
                self.logger.error(f"Error clearing device logcat: {e}")
        
        threading.Thread(target=clear_logcat, daemon=True).start()
    
    def save_logs(self):
        """Save logs to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Logs",
            f"logcat_{self.device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                entries_to_save = self.filtered_entries if self.export_filtered_only.isChecked() else self.log_entries
                success = self.logcat_handler.export_logs(filename, entries_to_save)
                
                if success:
                    QMessageBox.information(self, "Export Successful", f"Logs exported to {filename}")
                    self.logger.info(f"Logs exported to {filename}")
                else:
                    QMessageBox.warning(self, "Export Failed", "Failed to export logs")
                    
            except Exception as e:
                self.logger.error(f"Error saving logs: {e}")
                QMessageBox.critical(self, "Error", f"Failed to save logs: {e}")
    
    def search_logs(self):
        """Search and filter logs based on search criteria."""
        # Add immediate feedback
        search_text = self.search_input.text()
        if search_text:
            self.status_label.setText(f"Status: Searching for '{search_text}'...")
        else:
            self.status_label.setText("Status: Capturing..." if self.is_capturing else "Status: Ready")
        
        # Process UI events for immediate feedback
        QApplication.processEvents()
        
        # Apply filters efficiently
        self.apply_filters_optimized()
    
    def apply_filters_optimized(self):
        """Apply all active filters efficiently."""
        # Clear filtered entries
        self.filtered_entries.clear()
        
        # For large datasets, apply filters more efficiently
        if len(self.log_entries) > 500:
            # Process in batches to maintain UI responsiveness
            batch_size = 100
            processed = 0
            
            for i in range(0, len(self.log_entries), batch_size):
                batch = self.log_entries[i:i + batch_size]
                
                for entry in batch:
                    if self.passes_filters(entry):
                        self.filtered_entries.append(entry)
                
                processed += len(batch)
                
                # Process UI events every batch to maintain responsiveness
                if processed % (batch_size * 2) == 0:  # Every 200 entries
                    QApplication.processEvents()
        else:
            # For smaller datasets, process normally
            for entry in self.log_entries:
                if self.passes_filters(entry):
                    self.filtered_entries.append(entry)
        
        # Update display efficiently
        self.refresh_display()
        self.entry_count_label.setText(f"Entries: {len(self.log_entries)} (Filtered: {len(self.filtered_entries)})")
        
        # Update status
        if self.search_input.text():
            self.status_label.setText(f"Status: Found {len(self.filtered_entries)} matches")
        else:
            self.status_label.setText("Status: Capturing..." if self.is_capturing else "Status: Ready")
    
    def apply_filters(self):
        """Apply all active filters and refresh display."""
        self.apply_filters_optimized()
    
    def refresh_display(self):
        """Refresh the log display with filtered entries."""
        # Use a more efficient approach for large numbers of entries
        if len(self.filtered_entries) > 100:
            # For large datasets, only show recent entries to maintain responsiveness
            recent_entries = self.filtered_entries[-100:]
            self.log_display.clear()
            self.log_display.append("... (showing last 100 entries for performance) ...\n")
        else:
            recent_entries = self.filtered_entries
            self.log_display.clear()
        
        # Batch the text insertion for better performance
        text_to_insert = []
        for entry in recent_entries:
            # Format log line based on entry content
            if entry.tag == "raw" or (not entry.timestamp and not entry.pid):
                log_line = entry.message
            else:
                timestamp_part = f"{entry.timestamp} " if entry.timestamp else ""
                pid_part = f"({entry.pid})" if entry.pid else ""
                log_line = f"{timestamp_part}{entry.level}/{entry.tag}{pid_part}: {entry.message}"
            
            text_to_insert.append(log_line)
        
        # Insert all text at once for better performance
        if text_to_insert:
            combined_text = "\n".join(text_to_insert)
            self.log_display.append(combined_text)
        
        # Auto-scroll if enabled
        if self.auto_scroll_checkbox.isChecked():
            cursor = self.log_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.log_display.setTextCursor(cursor)
    
    def add_tag_filter(self):
        """Add a new tag filter."""
        tag = self.tag_filter_input.text().strip()
        if tag:
            # Add tag to the tag filter list (if we have one)
            # For now, just apply filters to see if tag exists in logs
            self.apply_filters()
            self.tag_filter_input.clear()
            self.logger.info(f"Tag filter applied: {tag}")
    
    def add_highlight_keyword(self, show_dialogs=True):
        """Add a keyword for highlighting."""
        keyword = self.highlight_input.text().strip()
        if keyword:
            # Initialize highlight keywords list if it doesn't exist
            if not hasattr(self, 'highlight_keywords'):
                self.highlight_keywords = []
            
            # Check for duplicates (case-insensitive)
            if any(k.lower() == keyword.lower() for k in self.highlight_keywords):
                if show_dialogs:
                    QMessageBox.information(
                        self,
                        "Duplicate Keyword",
                        f"Keyword '{keyword}' is already in the highlight list."
                    )
                return False  # Indicates duplicate was found
            
            # Add the keyword
            self.highlight_keywords.append(keyword)
            self.highlight_input.clear()
            self.logger.info(f"Highlight keyword added: {keyword}")
            
            # Update keyword display immediately
            self._update_keyword_display()
            
            # Process UI events for immediate feedback
            QApplication.processEvents()
            
            # Refresh display efficiently - only if we have entries to refresh
            if self.filtered_entries and len(self.filtered_entries) < 50:
                # For small datasets, do a full refresh
                self.refresh_display()
            else:
                # For large datasets, just update the display incrementally
                self.logger.info(f"Keyword '{keyword}' will be highlighted in new log entries")
            
            return True  # Indicates success
    
    def _update_keyword_display(self):
        """Update the display of current highlight keywords."""
        if hasattr(self, 'keywords_label') and hasattr(self, 'highlight_keywords'):
            if self.highlight_keywords:
                keywords_text = ", ".join(self.highlight_keywords)
                self.keywords_label.setText(f"Keywords: {keywords_text}")
            else:
                self.keywords_label.setText("Keywords: None")
    
    def clear_highlight_keywords(self):
        """Clear all highlight keywords."""
        if hasattr(self, 'highlight_keywords'):
            self.highlight_keywords.clear()
            self._update_keyword_display()
            self.refresh_display()
            self.logger.info("All highlight keywords cleared")
    
    def export_logs(self):
        """Export logs with current filters applied."""
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Logs", 
            f"logcat_export_{self.device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)"
        )
        
        if filename:
            try:
                # Export currently filtered entries
                success = self.logcat_handler.export_logs(filename, self.filtered_entries)
                
                if success:
                    QMessageBox.information(self, "Export Successful", f"Logs exported to {filename}")
                    self.logger.info(f"Filtered logs exported to {filename}")
                else:
                    QMessageBox.warning(self, "Export Failed", "Failed to export logs")
                    
            except Exception as e:
                self.logger.error(f"Error exporting logs: {e}")
                QMessageBox.critical(self, "Error", f"Failed to export logs: {e}")
    
    def update_capture_rate(self):
        """Update the capture rate display."""
        current_count = len(self.log_entries)
        rate = current_count - self.last_entry_count
        self.last_entry_count = current_count
        self.capture_rate_label.setText(f"Rate: {rate}/sec")
    
    def closeEvent(self, event):
        """Handle widget close event."""
        self.cleanup()
        super().closeEvent(event)
        
    def refresh_theme(self):
        """Refresh theme-related styling for logging components."""
        try:
            # Get current theme from the application's stylesheet
            app = QApplication.instance()
            if not app:
                return
                
            # Check if dark theme is active by looking for dark background colors in stylesheet
            stylesheet = app.styleSheet()
            is_dark_theme = "#1e1e1e" in stylesheet or "#2b2b2b" in stylesheet
            
            # Define theme colors
            if is_dark_theme:
                bg_color = "#1e1e1e"
                text_color = "#ffffff"
                border_color = "#555555"
                selection_bg = "#007acc"
                selection_text = "#ffffff"
                widget_bg = "#2b2b2b"
                input_bg = "#363636"
                groupbox_bg = "#2b2b2b"
                button_bg = "#363636"
                button_hover_bg = "#484848"
                button_pressed_bg = "#555555"
                theme_name = "dark"
            else:  # light theme
                bg_color = "#ffffff"
                text_color = "#000000"
                border_color = "#c0c0c0"
                selection_bg = "#007acc"
                selection_text = "#ffffff"
                widget_bg = "#f0f0f0"
                input_bg = "#ffffff"
                groupbox_bg = "#ffffff"
                button_bg = "#ffffff"
                button_hover_bg = "#e0e0e0"
                button_pressed_bg = "#d0d0d0"
                theme_name = "light"
            
            # Apply comprehensive styling to all logging components
            if hasattr(self, 'log_display') and self.log_display:
                # Method 1: Apply explicit stylesheet with !important
                textedit_style = f"""
                QTextEdit {{
                    background-color: {bg_color} !important;
                    color: {text_color} !important;
                    border: 1px solid {border_color} !important;
                    border-radius: 4px;
                    selection-background-color: {selection_bg};
                    selection-color: {selection_text};
                    font-family: 'Consolas', monospace;
                }}
                QTextEdit:focus {{
                    border-color: {selection_bg} !important;
                }}
                """
                self.log_display.setStyleSheet(textedit_style)
                
                # Method 2: Also set palette colors as backup
                from PyQt6.QtGui import QPalette
                palette = self.log_display.palette()
                palette.setColor(QPalette.ColorRole.Base, QColor(bg_color))
                palette.setColor(QPalette.ColorRole.Text, QColor(text_color))
                palette.setColor(QPalette.ColorRole.Window, QColor(bg_color))
                palette.setColor(QPalette.ColorRole.WindowText, QColor(text_color))
                # Set all color groups to ensure consistency
                for group in [QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive, QPalette.ColorGroup.Disabled]:
                    palette.setColor(group, QPalette.ColorRole.Base, QColor(bg_color))
                    palette.setColor(group, QPalette.ColorRole.Text, QColor(text_color))
                    palette.setColor(group, QPalette.ColorRole.Window, QColor(bg_color))
                    palette.setColor(group, QPalette.ColorRole.WindowText, QColor(text_color))
                self.log_display.setPalette(palette)
                
                # Set auto fill background
                self.log_display.setAutoFillBackground(True)
                self.log_display.setBackgroundRole(QPalette.ColorRole.Base)
                
                # Method 3: Force immediate update
                self.log_display.style().unpolish(self.log_display)
                self.log_display.style().polish(self.log_display)
                self.log_display.update()
                self.log_display.repaint()
                
                # Method 4: Force refresh of viewport (for QTextEdit)
                if hasattr(self.log_display, 'viewport'):
                    viewport = self.log_display.viewport()
                    if viewport:
                        viewport_palette = viewport.palette()
                        viewport_palette.setColor(QPalette.ColorRole.Base, QColor(bg_color))
                        viewport_palette.setColor(QPalette.ColorRole.Text, QColor(text_color))
                        viewport.setPalette(viewport_palette)
                        viewport.update()
                        viewport.repaint()
                
                self.logger.info(f"Applied {theme_name} theme: bg={bg_color}, text={text_color}")
            
            # Apply styling to ALL buttons
            button_style = f"""
            QPushButton {{
                background-color: {button_bg} !important;
                color: {text_color} !important;
                border: 1px solid {border_color} !important;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: normal;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {button_hover_bg} !important;
                border-color: {selection_bg} !important;
            }}
            QPushButton:pressed {{
                background-color: {button_pressed_bg} !important;
            }}
            QPushButton:disabled {{
                background-color: {border_color} !important;
                color: #888888 !important;
            }}
            """
            
            # Apply to all specific buttons
            button_attributes = [
                'start_btn', 'stop_btn', 'clear_btn', 'save_btn'
            ]
            
            for button_attr in button_attributes:
                if hasattr(self, button_attr):
                    button = getattr(self, button_attr)
                    if button:
                        button.setStyleSheet(button_style)
                        button.style().unpolish(button)
                        button.style().polish(button)
                        button.update()
            
            # Apply to ALL QPushButton widgets found in the widget tree
            for button in self.findChildren(QPushButton):
                button.setStyleSheet(button_style)
                button.style().unpolish(button)
                button.style().polish(button)
                button.update()
            
            # Apply styling to search input
            if hasattr(self, 'search_input') and self.search_input:
                search_style = f"""
                QLineEdit {{
                    background-color: {input_bg} !important;
                    color: {text_color} !important;
                    border: 1px solid {border_color} !important;
                    padding: 6px;
                    border-radius: 4px;
                }}
                QLineEdit:focus {{
                    border-color: {selection_bg} !important;
                }}
                """
                self.search_input.setStyleSheet(search_style)
                
            # Apply styling to ALL QLineEdit widgets
            for line_edit in self.findChildren(QLineEdit):
                line_edit_style = f"""
                QLineEdit {{
                    background-color: {input_bg} !important;
                    color: {text_color} !important;
                    border: 1px solid {border_color} !important;
                    padding: 6px;
                    border-radius: 4px;
                }}
                QLineEdit:focus {{
                    border-color: {selection_bg} !important;
                }}
                """
                line_edit.setStyleSheet(line_edit_style)
                line_edit.style().unpolish(line_edit)
                line_edit.style().polish(line_edit)
                line_edit.update()
            
            # Apply styling to ALL QComboBox widgets
            combo_style = f"""
            QComboBox {{
                background-color: {input_bg} !important;
                color: {text_color} !important;
                border: 1px solid {border_color} !important;
                padding: 6px;
                border-radius: 4px;
                min-height: 20px;
            }}
            QComboBox::drop-down {{
                border: none;
                background-color: {border_color};
                border-radius: 2px;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {text_color};
            }}
            QComboBox QAbstractItemView {{
                background-color: {input_bg} !important;
                color: {text_color} !important;
                border: 1px solid {border_color} !important;
                border-radius: 4px;
                selection-background-color: {selection_bg};
            }}
            """
            
            for combo in self.findChildren(QComboBox):
                combo.setStyleSheet(combo_style)
                combo.style().unpolish(combo)
                combo.style().polish(combo)
                combo.update()
            
            # Apply styling to ALL QSpinBox widgets
            spinbox_style = f"""
            QSpinBox {{
                background-color: {input_bg} !important;
                color: {text_color} !important;
                border: 1px solid {border_color} !important;
                padding: 4px 8px;
                border-radius: 4px;
                min-height: 24px;
                min-width: 100px;
                font-size: 12px;
                font-weight: normal;
            }}
            QSpinBox:focus {{
                border-color: {selection_bg} !important;
                border-width: 2px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {button_bg};
                border: 1px solid {border_color};
                width: 18px;
                border-radius: 2px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {button_hover_bg};
            }}
            QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {{
                background-color: {button_pressed_bg};
            }}
            """
            
            for spinbox in self.findChildren(QSpinBox):
                spinbox.setStyleSheet(spinbox_style)
                spinbox.style().unpolish(spinbox)
                spinbox.style().polish(spinbox)
                spinbox.update()
                
            # Apply styling to ALL QLabel widgets (including buffer size label)
            label_style = f"""
            QLabel {{
                color: {text_color} !important;
                background-color: transparent;
                font-size: 12px;
                font-weight: normal;
            }}
            """
            
            for label in self.findChildren(QLabel):
                label.setStyleSheet(label_style)
                label.style().unpolish(label)
                label.style().polish(label)
                label.update()
                
            # Apply styling to ALL QCheckBox widgets
            checkbox_style = f"""
            QCheckBox {{
                color: {text_color} !important;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                background-color: {input_bg} !important;
                border: 1px solid {border_color} !important;
                border-radius: 2px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {selection_bg} !important;
                border-color: {selection_bg} !important;
            }}
            QCheckBox::indicator:hover {{
                border-color: {selection_bg} !important;
            }}
            """
            
            for checkbox in self.findChildren(QCheckBox):
                checkbox.setStyleSheet(checkbox_style)
                checkbox.style().unpolish(checkbox)
                checkbox.style().polish(checkbox)
                checkbox.update()
            
            # Apply styling to ALL QGroupBox widgets
            groupbox_style = f"""
            QGroupBox {{
                color: {text_color} !important;
                border: 1px solid {border_color} !important;
                border-radius: 4px;
                margin: 8px 0px;
                padding-top: 16px;
                background-color: {groupbox_bg} !important;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0px 8px;
                background-color: {groupbox_bg} !important;
                color: {text_color} !important;
                font-weight: bold;
            }}
            """
            
            for groupbox in self.findChildren(QGroupBox):
                groupbox.setStyleSheet(groupbox_style)
                groupbox.style().unpolish(groupbox)
                groupbox.style().polish(groupbox)
                groupbox.update()
            
            # Apply styling to ALL QScrollArea widgets
            scroll_area_style = f"""
            QScrollArea {{
                background-color: {widget_bg} !important;
                border: 1px solid {border_color} !important;
                border-radius: 4px;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {widget_bg} !important;
            }}
            QScrollBar:vertical {{
                background-color: {input_bg} !important;
                width: 12px;
                border-radius: 6px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {border_color} !important;
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {selection_bg} !important;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: none;
                border: none;
            }}
            QScrollBar:horizontal {{
                background-color: {input_bg} !important;
                height: 12px;
                border-radius: 6px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {border_color} !important;
                border-radius: 6px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {selection_bg} !important;
            }}
            """
            
            for scroll_area in self.findChildren(QScrollArea):
                scroll_area.setStyleSheet(scroll_area_style)
                scroll_area.style().unpolish(scroll_area)
                scroll_area.style().polish(scroll_area)
                scroll_area.update()
                    
            # Apply styling to ALL QLabel widgets
            for label in self.findChildren(QLabel):
                label.setStyleSheet(f"""
                QLabel {{
                    color: {text_color} !important;
                    background-color: transparent;
                }}
                """)
                label.style().unpolish(label)
                label.style().polish(label)
                label.update()
                    
            # Apply styling to ALL QFrame widgets
            for frame in self.findChildren(QFrame):
                frame.setStyleSheet(f"""
                QFrame {{
                    border: 1px solid {border_color} !important;
                    border-radius: 4px;
                    background-color: {widget_bg} !important;
                }}
                """)
                frame.style().unpolish(frame)
                frame.style().polish(frame)
                frame.update()
            
            # Apply styling to ALL QWidget widgets (catch-all for any remaining elements)
            widget_style = f"""
            QWidget {{
                background-color: {widget_bg};
                color: {text_color};
            }}
            """
            
            # Apply to the main widget itself
            self.setStyleSheet(f"""
            QWidget#logging_main {{
                background-color: {widget_bg} !important;
                color: {text_color} !important;
            }}
            {widget_style}
            """)
            
            # Force refresh on ALL child widgets
            for child in self.findChildren(QWidget):
                try:
                    child.style().unpolish(child)
                    child.style().polish(child)
                    child.update()
                except:
                    pass  # Ignore errors for widgets that might not support styling
            
            # Force a full repaint of the entire widget hierarchy
            self.style().unpolish(self)
            self.style().polish(self)
            self.update()
            self.repaint()
            
            # Also force update on parent if it exists
            if self.parent():
                self.parent().update()
            
            self.logger.info(f"Logging theme comprehensively refreshed to {theme_name} mode - ALL elements styled")
            
        except Exception as e:
            self.logger.error(f"Error refreshing logging theme: {e}")
    
    def refresh_theme_optimized(self):
        """Optimized theme refresh that doesn't block UI."""
        try:
            # Only refresh if the widget is still visible and active
            if not self.isVisible():
                return
            
            # Use a more efficient approach - only refresh key components
            app = QApplication.instance()
            if not app:
                return
                
            stylesheet = app.styleSheet()
            is_dark_theme = "#1e1e1e" in stylesheet or "#2b2b2b" in stylesheet
            
            if is_dark_theme:
                bg_color = "#1e1e1e"
                text_color = "#ffffff"
            else:
                bg_color = "#ffffff"
                text_color = "#000000"
            
            # Only update the most critical components for immediate responsiveness
            if hasattr(self, 'log_display') and self.log_display:
                self.log_display.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {bg_color} !important;
                    color: {text_color} !important;
                    border: 1px solid #555555;
                    border-radius: 4px;
                }}
                """)
            
            # Update search and highlight inputs for immediate functionality
            if hasattr(self, 'search_input') and self.search_input:
                self.search_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {bg_color} !important;
                    color: {text_color} !important;
                    border: 1px solid #555555;
                    padding: 6px;
                    border-radius: 4px;
                }}
                """)
            
            if hasattr(self, 'highlight_input') and self.highlight_input:
                self.highlight_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {bg_color} !important;
                    color: {text_color} !important;
                    border: 1px solid #555555;
                    padding: 6px;
                    border-radius: 4px;
                }}
                """)
            
            self.logger.info("Optimized theme refresh completed")
            
        except Exception as e:
            self.logger.error(f"Error in optimized theme refresh: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if self.is_capturing:
                self.stop_capture()
            
            # Ensure worker is properly terminated
            if self.logcat_worker and self.logcat_worker.isRunning():
                self.logcat_worker.terminate()
                self.logcat_worker.wait(1000)
                
            self.logger.info("Logging widget cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def _insert_highlighted_text(self, cursor, text, log_level, colors, highlight_keywords):
        """Insert text with keyword highlighting."""
        import re
        
        # Create base format for log level
        base_format = QTextCharFormat()
        base_format.setForeground(QColor(colors.get(log_level, "#ffffff")))
        
        # Create highlight format
        highlight_format = QTextCharFormat()
        highlight_format.setForeground(QColor("#000000"))  # Black text
        highlight_format.setBackground(QColor("#ffff00"))  # Yellow background
        
        # Find all keyword matches
        remaining_text = text
        while remaining_text:
            # Find the earliest keyword match
            earliest_match = None
            earliest_pos = len(remaining_text)
            earliest_keyword = None
            
            for keyword in highlight_keywords:
                # Case-insensitive search
                match = re.search(re.escape(keyword), remaining_text, re.IGNORECASE)
                if match and match.start() < earliest_pos:
                    earliest_pos = match.start()
                    earliest_match = match
                    earliest_keyword = keyword
            
            if earliest_match:
                # Insert text before the match with normal formatting
                if earliest_pos > 0:
                    cursor.setCharFormat(base_format)
                    cursor.insertText(remaining_text[:earliest_pos])
                
                # Insert the highlighted keyword
                cursor.setCharFormat(highlight_format)
                cursor.insertText(remaining_text[earliest_match.start():earliest_match.end()])
                
                # Update remaining text
                remaining_text = remaining_text[earliest_match.end():]
            else:
                # No more matches, insert remaining text with normal formatting
                cursor.setCharFormat(base_format)
                cursor.insertText(remaining_text)
                break
