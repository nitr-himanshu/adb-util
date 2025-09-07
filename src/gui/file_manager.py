"""
File Manager UI

Dual-pane file browser with drag & drop support for file operations.
"""

import os
import asyncio
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeView, QLabel, QPushButton, QProgressBar,
    QLineEdit, QTextEdit, QTabWidget, QFrame,
    QToolBar, QFileDialog, QMessageBox, QListWidget,
    QComboBox, QSpinBox, QInputDialog, QListWidgetItem,
    QAbstractItemView, QMenu, QApplication
)
from PyQt6.QtCore import Qt, QDir, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont, QFileSystemModel, QAction

from adb.file_operations import FileOperations, FileInfo
from utils.logger import get_logger, log_file_operation
from services.config_manager import ConfigManager


class FileTransferWorker(QThread):
    """Worker thread for file transfer operations."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    transfer_completed = pyqtSignal(bool, str)
    
    def __init__(self, operation: str, file_ops: FileOperations, 
                 source: str, destination: str):
        super().__init__()
        self.operation = operation
        self.file_ops = file_ops
        self.source = source
        self.destination = destination
        self.logger = get_logger(__name__)
    
    def run(self):
        """Execute the file transfer operation."""
        try:
            # Create event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                if self.operation == "push":
                    result = loop.run_until_complete(
                        self.file_ops.push_file(Path(self.source), self.destination)
                    )
                elif self.operation == "pull":
                    result = loop.run_until_complete(
                        self.file_ops.pull_file(self.source, Path(self.destination))
                    )
                elif self.operation == "delete":
                    result = loop.run_until_complete(
                        self.file_ops.delete_file(self.source)
                    )
                elif self.operation == "delete_dir":
                    result = loop.run_until_complete(
                        self.file_ops.delete_directory(self.source)
                    )
                elif self.operation == "create_dir":
                    result = loop.run_until_complete(
                        self.file_ops.create_directory(self.source)
                    )
                else:
                    result = False
                
                message = f"{self.operation.title()} completed successfully" if result else f"{self.operation.title()} failed"
                self.transfer_completed.emit(result, message)
                
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Error in file transfer worker: {e}")
            self.transfer_completed.emit(False, f"Error: {str(e)}")


class DirectoryListWorker(QThread):
    """Worker thread for directory listing operations."""
    
    listing_completed = pyqtSignal(list)
    listing_failed = pyqtSignal(str)
    
    def __init__(self, file_ops: FileOperations, path: str):
        super().__init__()
        self.file_ops = file_ops
        self.path = path
        self.logger = get_logger(__name__)
    
    def run(self):
        """Execute the directory listing operation."""
        try:
            # Create event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # First test device connection
                self.logger.info(f"Testing device connection before listing {self.path}")
                connection_ok = loop.run_until_complete(
                    self.file_ops.test_device_connection()
                )
                
                if not connection_ok:
                    self.listing_failed.emit(f"Cannot connect to device {self.file_ops.device_id}")
                    return
                
                # Now try to list the directory
                self.logger.info(f"Listing directory {self.path}")
                files = loop.run_until_complete(
                    self.file_ops.list_directory(self.path)
                )
                
                self.logger.info(f"Directory listing returned {len(files)} files")
                self.listing_completed.emit(files)
                
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Error in directory listing worker: {e}")
            import traceback
            traceback.print_exc()
            self.listing_failed.emit(f"Error listing directory: {str(e)}")


class FileManager(QWidget):
    """File manager widget with local and device file browsers."""
    
    def __init__(self, device_id: str):
        super().__init__()
        self.device_id = device_id
        self.logger = get_logger(__name__)
        self.local_model = None
        self.device_model = None
        self.current_device_path = "/sdcard/"
        self.file_ops = FileOperations(device_id)
        self.transfer_worker = None
        self.listing_worker = None
        self.config = ConfigManager()
        
        # Load last used paths
        self.current_local_path = self.config.get_last_path("local")
        self.current_device_path = self.config.get_last_path("device")
        
        self.logger.info(f"Initializing file manager for device: {device_id}")
        self.init_ui()
        self.load_device_directory()
        self.logger.info("File manager initialization complete")
    
    def get_short_device_name(self, device_id: str) -> str:
        """Get a short, user-friendly device name."""
        if not device_id:
            return "Unknown Device"
        
        # If it's an emulator, show just "Emulator-XXXX"
        if "emulator" in device_id.lower():
            port = device_id.split('-')[-1]
            return f"Emulator-{port}"
        
        # If it's a long serial number, show brand info if possible + last chars
        if len(device_id) > 12:
            # Try to identify common device patterns
            if device_id.startswith('R58'):  # Pixel devices often start with this
                return f"Pixel-{device_id[-6:]}"
            elif device_id.startswith('RF8') or device_id.startswith('RF9'):
                return f"Samsung-{device_id[-6:]}"
            elif len(device_id) > 16:  # Very long serial
                return f"Device-{device_id[-8:]}"
            else:
                return f"Device-{device_id[-6:]}"
        
        # Otherwise show the full device ID but limit length
        return device_id[:25] + "..." if len(device_id) > 25 else device_id
    
    def get_short_device_name(self, device_id: str) -> str:
        """Get a short, user-friendly device name."""
        if not device_id:
            return "Unknown Device"
        
        # If it's an emulator, show just "Emulator-XXXX"
        if "emulator" in device_id.lower():
            return f"Emulator-{device_id.split('-')[-1]}"
        
        # If it's a serial number, show last 8 characters
        if len(device_id) > 12:
            return f"Device-{device_id[-8:]}"

        # Otherwise show the full device ID but limit length
        return device_id[:20] + "..." if len(device_id) > 20 else device_id

    def init_ui(self):
        """Initialize the file manager UI."""
        layout = QVBoxLayout(self)
        
        # Create toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Create local file panel
        local_panel = self.create_local_panel()
        splitter.addWidget(local_panel)
        
        # Create transfer controls
        transfer_panel = self.create_transfer_panel()
        splitter.addWidget(transfer_panel)
        
        # Create device file panel
        device_panel = self.create_device_panel()
        splitter.addWidget(device_panel)
        
        # Set splitter proportions - larger file panels, smaller transfer panel
        splitter.setSizes([450, 80, 450])
        
        # Create progress panel
        progress_panel = self.create_progress_panel()
        layout.addWidget(progress_panel)
    
    def create_toolbar(self):
        """Create the file manager toolbar."""
        toolbar_frame = QFrame()
        toolbar_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar_frame.setMaximumHeight(35)  # Make toolbar very compact
        toolbar_frame.setMinimumHeight(35)
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(5, 2, 5, 2)  # Smaller margins
        toolbar_layout.setSpacing(5)  # Smaller spacing
        
        # Device info - show short device name only
        short_device_name = self.get_short_device_name(self.device_id)
        device_label = QLabel(f"📱 {short_device_name}")
        device_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))  # Even smaller font
        device_label.setMaximumWidth(180)  # Slightly larger width for name
        device_label.setStyleSheet("color: #4CAF50;")  # Green color to make it stand out
        device_label.setToolTip(f"Full Device ID: {self.device_id}")  # Show full ID in tooltip
        toolbar_layout.addWidget(device_label)
        
        toolbar_layout.addStretch()
        
        # Action buttons - auto-size based on text content
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Refresh files")
        refresh_btn.setMaximumHeight(28)
        refresh_btn.setSizePolicy(refresh_btn.sizePolicy().horizontalPolicy(), refresh_btn.sizePolicy().verticalPolicy())
        refresh_btn.clicked.connect(self.refresh_files)
        toolbar_layout.addWidget(refresh_btn)
        
        new_folder_btn = QPushButton("📁 New")
        new_folder_btn.setToolTip("New Folder")
        new_folder_btn.setMaximumHeight(28)
        new_folder_btn.setSizePolicy(new_folder_btn.sizePolicy().horizontalPolicy(), new_folder_btn.sizePolicy().verticalPolicy())
        new_folder_btn.clicked.connect(self.create_new_folder)
        toolbar_layout.addWidget(new_folder_btn)
        
        # Quick navigation buttons - auto-size based on text
        home_btn = QPushButton("🏠 Home")
        home_btn.setToolTip("Home (/sdcard/)")
        home_btn.setMaximumHeight(28)
        home_btn.setSizePolicy(home_btn.sizePolicy().horizontalPolicy(), home_btn.sizePolicy().verticalPolicy())
        home_btn.clicked.connect(lambda: self.navigate_to_device_path("/sdcard/"))
        toolbar_layout.addWidget(home_btn)
        
        root_btn = QPushButton("📂 Root")
        root_btn.setToolTip("Root (/)")
        root_btn.setMaximumHeight(28)
        root_btn.setSizePolicy(root_btn.sizePolicy().horizontalPolicy(), root_btn.sizePolicy().verticalPolicy())
        root_btn.clicked.connect(lambda: self.navigate_to_device_path("/"))
        toolbar_layout.addWidget(root_btn)
        
        # Test connection button - auto-size based on text
        test_btn = QPushButton("🔗 Test")
        test_btn.setToolTip("Test device connection")
        test_btn.setMaximumHeight(28)
        test_btn.setSizePolicy(test_btn.sizePolicy().horizontalPolicy(), test_btn.sizePolicy().verticalPolicy())
        test_btn.clicked.connect(self.test_device_connection)
        toolbar_layout.addWidget(test_btn)
        
        return toolbar_frame
    
    def create_local_panel(self):
        """Create the local file system panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Header - more compact
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(2, 1, 2, 1)  # Even smaller margins
        header_layout.setSpacing(3)  # Smaller spacing
        header_label = QLabel("💻 Local")  # Shorter text
        header_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))  # Smaller font
        header_label.setMaximumWidth(80)  # Compact width
        header_layout.addWidget(header_label)
        
        # Path input with history and bookmarks
        path_layout = QHBoxLayout()
        
        # Path ComboBox with history - make it much larger for long paths
        self.local_path_combo = QComboBox()
        self.local_path_combo.setEditable(True)
        self.local_path_combo.setMinimumWidth(500)  # Much larger for long paths
        self.local_path_combo.setMaximumHeight(26)  # Slightly taller for readability
        self.local_path_combo.currentTextChanged.connect(self.on_local_path_changed)
        self.local_path_combo.lineEdit().returnPressed.connect(self.navigate_local_folder)
        self.populate_local_path_combo()
        path_layout.addWidget(self.local_path_combo)
        
        # Browse button - proper size for text
        browse_btn = QPushButton("Browse")
        browse_btn.setMinimumWidth(65)  # Ensure text fits
        browse_btn.setMaximumWidth(65)
        browse_btn.setMaximumHeight(26)  # Match ComboBox height
        browse_btn.clicked.connect(self.browse_local_folder)
        path_layout.addWidget(browse_btn)
        
        # Bookmark button
        bookmark_local_btn = QPushButton("⭐")
        bookmark_local_btn.setMinimumWidth(28)
        bookmark_local_btn.setMaximumWidth(28)
        bookmark_local_btn.setMaximumHeight(26)  # Match ComboBox height
        bookmark_local_btn.setToolTip("Bookmark this location")
        bookmark_local_btn.clicked.connect(self.bookmark_local_path)
        path_layout.addWidget(bookmark_local_btn)
        
        header_layout.addLayout(path_layout)
        
        layout.addLayout(header_layout)
        
        # File tree view
        self.local_tree = QTreeView()
        self.local_model = QFileSystemModel()
        self.local_model.setRootPath(self.current_local_path)
        self.local_tree.setModel(self.local_model)
        self.local_tree.setRootIndex(self.local_model.index(self.current_local_path))
        
        # Enable multi-selection
        self.local_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
        # Hide unnecessary columns initially
        self.local_tree.hideColumn(1)  # Size (we'll show it later)
        self.local_tree.hideColumn(2)  # Type
        self.local_tree.hideColumn(3)  # Date Modified
        
        # Context menu
        self.local_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.local_tree.customContextMenuRequested.connect(self.show_local_context_menu)
        
        layout.addWidget(self.local_tree)
        
        # Local file actions - adjust button width based on text
        local_actions = QHBoxLayout()
        local_actions.setSpacing(5)
        
        upload_btn = QPushButton("⬆️ Upload")
        # Calculate width based on text length + padding for icon
        upload_btn.setMinimumWidth(90)  # Fits "⬆️ Upload" properly
        upload_btn.setMaximumWidth(90)
        upload_btn.setMaximumHeight(28)
        upload_btn.clicked.connect(self.upload_selected_files)
        local_actions.addWidget(upload_btn)
        
        delete_local_btn = QPushButton("🗑️ Delete")
        delete_local_btn.setMinimumWidth(85)  # Fits "🗑️ Delete" properly
        delete_local_btn.setMaximumWidth(85)
        delete_local_btn.setMaximumHeight(28)
        delete_local_btn.clicked.connect(self.delete_local_file)
        local_actions.addWidget(delete_local_btn)
        
        local_actions.addStretch()  # Push buttons to left
        
        layout.addLayout(local_actions)
        
        return panel
    
    def create_device_panel(self):
        """Create the device file system panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Header - more compact
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(2, 1, 2, 1)  # Even smaller margins
        header_layout.setSpacing(3)  # Smaller spacing
        header_label = QLabel("📱 Device")  # Shorter text
        header_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))  # Smaller font
        header_label.setMaximumWidth(80)  # Compact width
        header_layout.addWidget(header_label)
        
        # Path input with history and bookmarks
        path_layout = QHBoxLayout()
        
        # Path ComboBox with history - make it much larger for long paths
        self.device_path_combo = QComboBox()
        self.device_path_combo.setEditable(True)
        self.device_path_combo.setMinimumWidth(450)  # Much larger for long paths
        self.device_path_combo.setMaximumHeight(26)  # Slightly taller for readability
        self.device_path_combo.currentTextChanged.connect(self.on_device_path_changed)
        self.device_path_combo.lineEdit().returnPressed.connect(self.navigate_device_folder)
        self.populate_device_path_combo()
        path_layout.addWidget(self.device_path_combo)
        
        # Navigate button - proper size for text
        navigate_btn = QPushButton("Go")
        navigate_btn.setMinimumWidth(40)
        navigate_btn.setMaximumWidth(40)
        navigate_btn.setMaximumHeight(26)  # Match ComboBox height
        navigate_btn.clicked.connect(self.navigate_device_folder)
        path_layout.addWidget(navigate_btn)
        
        # Up button
        up_btn = QPushButton("⬆️")
        up_btn.setMinimumWidth(28)
        up_btn.setMaximumWidth(28)
        up_btn.setMaximumHeight(26)  # Match ComboBox height
        up_btn.setToolTip("Go up one level")
        up_btn.clicked.connect(self.go_up_device_directory)
        path_layout.addWidget(up_btn)
        
        # Bookmark button
        bookmark_device_btn = QPushButton("⭐")
        bookmark_device_btn.setMinimumWidth(28)
        bookmark_device_btn.setMaximumWidth(28)
        bookmark_device_btn.setMaximumHeight(26)  # Match ComboBox height
        bookmark_device_btn.setToolTip("Bookmark this location")
        bookmark_device_btn.clicked.connect(self.bookmark_device_path)
        path_layout.addWidget(bookmark_device_btn)
        
        header_layout.addLayout(path_layout)
        
        layout.addLayout(header_layout)
        
        # Device file list
        self.device_list = QListWidget()
        self.device_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
        # Enable double-click to navigate
        self.device_list.itemDoubleClicked.connect(self.device_item_double_clicked)
        
        # Context menu
        self.device_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.device_list.customContextMenuRequested.connect(self.show_device_context_menu)
        
        layout.addWidget(self.device_list)
        
        # Device file actions
        device_actions = QHBoxLayout()
        device_actions.setSpacing(4)  # Minimal spacing
        
        download_btn = QPushButton("⬇️ Download")
        download_btn.setMinimumWidth(100)  # Fits "⬇️ Download" properly
        download_btn.setMaximumWidth(100)
        download_btn.setMaximumHeight(28)
        download_btn.clicked.connect(self.download_selected_files)
        device_actions.addWidget(download_btn)
        
        delete_device_btn = QPushButton("🗑️ Delete")
        delete_device_btn.setMinimumWidth(85)  # Fits "🗑️ Delete" properly
        delete_device_btn.setMaximumWidth(85)
        delete_device_btn.setMaximumHeight(28)
        delete_device_btn.clicked.connect(self.delete_device_file)
        device_actions.addWidget(delete_device_btn)
        
        layout.addLayout(device_actions)
        
        return panel
    
    def create_transfer_panel(self):
        """Create the transfer controls panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumWidth(90)  # Reduced from 120
        panel.setMinimumWidth(90)
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)  # Reduced spacing
        
        # Transfer buttons - more compact
        push_btn = QPushButton("➡️\nPush")
        push_btn.setMinimumHeight(50)  # Reduced from 60
        push_btn.clicked.connect(self.push_file)
        push_btn.setToolTip("Push selected local files to device")
        layout.addWidget(push_btn)
        
        pull_btn = QPushButton("⬅️\nPull")
        pull_btn.setMinimumHeight(50)  # Reduced from 60
        pull_btn.clicked.connect(self.pull_file)
        pull_btn.setToolTip("Pull selected device files to local")
        layout.addWidget(pull_btn)
        
        sync_btn = QPushButton("🔄\nSync")
        sync_btn.setMinimumHeight(50)  # Reduced from 60
        sync_btn.clicked.connect(self.sync_folders)
        sync_btn.setToolTip("Sync folders between local and device")
        layout.addWidget(sync_btn)
        
        layout.addStretch()
        
        return panel
    
    def create_progress_panel(self):
        """Create the file transfer progress panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumHeight(30)  # Reduced height since no theme button
        panel.setMinimumHeight(30)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 2, 4, 2)  # Minimal margins
        layout.setSpacing(2)  # Small spacing
        
        # Progress info
        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(6)
        
        self.progress_label = QLabel("Ready")
        self.progress_label.setFont(QFont("Arial", 8))
        progress_layout.addWidget(self.progress_label)
        
        progress_layout.addStretch()
        
        self.speed_label = QLabel("")
        self.speed_label.setFont(QFont("Arial", 8))
        progress_layout.addWidget(self.speed_label)
        
        layout.addLayout(progress_layout)
        
        # Progress bar - inline with text
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(6)  # Very thin progress bar
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return panel
    
    def load_device_directory(self):
        """Load the current device directory."""
        if self.listing_worker and self.listing_worker.isRunning():
            return
        
        self.progress_label.setText(f"Loading {self.current_device_path}...")
        self.device_list.clear()
        
        # Add a loading indicator
        loading_item = QListWidgetItem("⏳ Loading...")
        self.device_list.addItem(loading_item)
        
        # Start directory listing in background thread
        self.listing_worker = DirectoryListWorker(self.file_ops, self.current_device_path)
        self.listing_worker.listing_completed.connect(self.on_device_listing_completed)
        self.listing_worker.listing_failed.connect(self.on_device_listing_failed)
        self.listing_worker.start()
    
    def on_device_listing_completed(self, files: List[FileInfo]):
        """Handle completed device directory listing."""
        self.device_list.clear()
        
        self.logger.info(f"Received {len(files)} files from directory listing")
        
        if not files:
            # Add a message item if no files found
            item = QListWidgetItem("📂 No files found or empty directory")
            self.device_list.addItem(item)
            self.progress_label.setText(f"No files found in {self.current_device_path}")
            return
        
        # Sort files: directories first, then files
        files.sort(key=lambda f: (not f.is_directory, f.name.lower()))
        
        for file_info in files:
            self.logger.debug(f"Adding file to list: {file_info}")
            
            # Ensure we have a valid name
            if not file_info.name or file_info.name.strip() == "":
                self.logger.warning(f"Skipping file with empty name: {file_info}")
                continue
            
            icon = "📁" if file_info.is_directory else "📄"
            size_text = ""
            if not file_info.is_directory and file_info.size > 0:
                size_text = f" ({self.format_file_size(file_info.size)})"
            
            item_text = f"{icon} {file_info.name}{size_text}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, file_info)
            self.device_list.addItem(item)
        
        actual_count = self.device_list.count()
        self.progress_label.setText(f"Loaded {actual_count} items from {self.current_device_path}")
        self.logger.info(f"Successfully added {actual_count} items to device list")
    
    def on_device_listing_failed(self, error_message: str):
        """Handle failed device directory listing."""
        self.progress_label.setText(f"Failed to load directory: {error_message}")
        QMessageBox.warning(self, "Directory Error", f"Failed to load directory:\n{error_message}")
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def browse_local_folder(self):
        """Browse for local folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", self.current_local_path)
        if folder:
            self.navigate_to_local_path(folder)
    
    def navigate_local_folder(self):
        """Navigate to the folder specified in local path combo."""
        path = self.local_path_combo.currentText()
        if path:
            self.navigate_to_local_path(path)
    
    def navigate_device_folder(self):
        """Navigate to device folder."""
        path = self.device_path_combo.currentText().strip()
        if path:
            self.navigate_to_device_path(path)
    
    def navigate_to_device_path(self, path: str):
        """Navigate to specific device path."""
        # Normalize path for Unix-style Android paths
        path = path.strip()
        if not path:
            path = '/'
        
        # Ensure path starts with /
        if not path.startswith('/'):
            path = '/' + path
            
        # Remove double slashes but preserve root /
        while '//' in path:
            path = path.replace('//', '/')
            
        # Store normalized path (always ends with / for directories)
        if path != '/' and not path.endswith('/'):
            path += '/'
            
        self.current_device_path = path
        
        # Add to history and save last path
        self.config.add_to_history(self.current_device_path, "device")
        self.config.set_last_path(self.current_device_path, "device")
        
        # Update combo box
        self.populate_device_path_combo()
        
        self.load_device_directory()
    
    def go_up_device_directory(self):
        """Go up one level in device directory."""
        if self.current_device_path != "/":
            # Handle Unix-style path navigation manually
            current = self.current_device_path.rstrip('/')
            
            # If we're at root, stay at root
            if current == '' or current == '/':
                parent_path = '/'
            else:
                # Find last slash and get parent
                last_slash = current.rfind('/')
                if last_slash <= 0:  # If slash is at position 0 or not found
                    parent_path = '/'
                else:
                    parent_path = current[:last_slash] + '/'
                    
            self.navigate_to_device_path(parent_path)
    
    def device_item_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on device item."""
        file_info = item.data(Qt.ItemDataRole.UserRole)
        if file_info and file_info.is_directory:
            self.navigate_to_device_path(file_info.path)
    
    def get_selected_local_files(self) -> List[str]:
        """Get list of selected local file paths."""
        selected_indexes = self.local_tree.selectedIndexes()
        file_paths = []
        
        for index in selected_indexes:
            if index.column() == 0:  # Only process the first column
                file_path = self.local_model.filePath(index)
                if file_path not in file_paths:
                    file_paths.append(file_path)
        
        return file_paths
    
    def get_selected_device_files(self) -> List[FileInfo]:
        """Get list of selected device files."""
        selected_items = self.device_list.selectedItems()
        files = []
        
        for item in selected_items:
            file_info = item.data(Qt.ItemDataRole.UserRole)
            if file_info:
                files.append(file_info)
        
        return files
    
    def upload_selected_files(self):
        """Upload selected local files to device."""
        selected_files = self.get_selected_local_files()
        if not selected_files:
            QMessageBox.information(self, "No Selection", "Please select files to upload.")
            return
        
        for file_path in selected_files:
            local_path = Path(file_path)
            if local_path.is_file():
                device_path = f"{self.current_device_path}{local_path.name}"
                self.start_file_transfer("push", str(local_path), device_path)
                break  # For now, upload one file at a time
    
    def download_selected_files(self):
        """Download selected device files to local."""
        selected_files = self.get_selected_device_files()
        if not selected_files:
            QMessageBox.information(self, "No Selection", "Please select files to download.")
            return
        
        # Get download directory
        download_dir = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if not download_dir:
            return
        
        for file_info in selected_files:
            if not file_info.is_directory:
                local_path = Path(download_dir) / file_info.name
                self.start_file_transfer("pull", file_info.path, str(local_path))
                break  # For now, download one file at a time
    
    def push_file(self):
        """Push file from local to device."""
        self.upload_selected_files()
    
    def pull_file(self):
        """Pull file from device to local."""
        self.download_selected_files()
    
    def sync_folders(self):
        """Sync folders between local and device."""
        QMessageBox.information(self, "Sync Folders", "Folder sync feature coming soon!")
    
    def delete_local_file(self):
        """Delete selected local file."""
        selected_files = self.get_selected_local_files()
        if not selected_files:
            QMessageBox.information(self, "No Selection", "Please select files to delete.")
            return
        
        reply = QMessageBox.question(
            self, 
            "Delete Files", 
            f"Are you sure you want to delete {len(selected_files)} selected file(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                for file_path in selected_files:
                    path = Path(file_path)
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        import shutil
                        shutil.rmtree(path)
                
                self.progress_label.setText(f"Deleted {len(selected_files)} local file(s)")
                # Refresh local view
                current_path = self.current_local_path
                self.local_tree.setRootIndex(self.local_model.index(current_path))
                
            except Exception as e:
                QMessageBox.critical(self, "Delete Error", f"Failed to delete files: {str(e)}")
    
    def delete_device_file(self):
        """Delete selected device file."""
        selected_files = self.get_selected_device_files()
        if not selected_files:
            QMessageBox.information(self, "No Selection", "Please select files to delete.")
            return
        
        reply = QMessageBox.question(
            self, 
            "Delete Files", 
            f"Are you sure you want to delete {len(selected_files)} selected file(s) from device?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for file_info in selected_files:
                operation = "delete_dir" if file_info.is_directory else "delete"
                self.start_file_transfer(operation, file_info.path, "")
                break  # Delete one at a time for now
    
    def create_new_folder(self):
        """Create new folder on device."""
        folder_name, ok = QInputDialog.getText(
            self, 
            "New Folder", 
            "Enter folder name:"
        )
        
        if ok and folder_name.strip():
            folder_path = f"{self.current_device_path}{folder_name.strip()}"
            self.start_file_transfer("create_dir", folder_path, "")
    
    def test_device_connection(self):
        """Test device connection manually."""
        self.progress_label.setText("Testing device connection...")
        
        # Create a simple worker to test connection
        class ConnectionTestWorker(QThread):
            test_completed = pyqtSignal(bool, str)
            
            def __init__(self, file_ops):
                super().__init__()
                self.file_ops = file_ops
            
            def run(self):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        result = loop.run_until_complete(
                            self.file_ops.test_device_connection()
                        )
                        
                        if result:
                            self.test_completed.emit(True, "Device connection successful")
                        else:
                            self.test_completed.emit(False, "Device connection failed")
                    finally:
                        loop.close()
                        
                except Exception as e:
                    self.test_completed.emit(False, f"Connection test error: {str(e)}")
        
        def on_test_completed(success, message):
            self.progress_label.setText(message)
            if success:
                QMessageBox.information(self, "Connection Test", message)
            else:
                QMessageBox.warning(self, "Connection Test", message)
        
        self.test_worker = ConnectionTestWorker(self.file_ops)
        self.test_worker.test_completed.connect(on_test_completed)
        self.test_worker.start()
    
    def refresh_files(self):
        """Refresh both file panels."""
        # Refresh local view
        if hasattr(self, 'local_model') and self.local_model:
            self.local_tree.setRootIndex(self.local_model.index(self.current_local_path))
        
        # Refresh device view
        self.load_device_directory()
    
    def start_file_transfer(self, operation: str, source: str, destination: str):
        """Start a file transfer operation in background thread."""
        if self.transfer_worker and self.transfer_worker.isRunning():
            QMessageBox.warning(self, "Transfer in Progress", "Please wait for current transfer to complete.")
            return
        
        self.show_progress(f"Starting {operation}...")
        
        # Start transfer in background thread
        self.transfer_worker = FileTransferWorker(operation, self.file_ops, source, destination)
        self.transfer_worker.progress_updated.connect(self.update_progress)
        self.transfer_worker.status_updated.connect(self.update_status)
        self.transfer_worker.transfer_completed.connect(self.on_transfer_completed)
        self.transfer_worker.start()
    
    def on_transfer_completed(self, success: bool, message: str):
        """Handle completed file transfer."""
        self.progress_bar.setVisible(False)
        self.progress_label.setText(message)
        
        if success:
            # Refresh device view after successful operations
            self.load_device_directory()
        
        # Log the operation
        operation = self.transfer_worker.operation if self.transfer_worker else "unknown"
        status = "completed" if success else "failed"
        log_file_operation(operation, self.transfer_worker.source if self.transfer_worker else "", 
                          self.transfer_worker.destination if self.transfer_worker else "", status)
    
    def update_progress(self, value: int):
        """Update progress bar."""
        self.progress_bar.setValue(value)
    
    def update_status(self, message: str):
        """Update status message."""
        self.progress_label.setText(message)
    
    def show_progress(self, message: str):
        """Show progress for operations."""
        self.progress_label.setText(message)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
    
    def show_local_context_menu(self, position):
        """Show context menu for local files."""
        menu = QMenu(self)
        
        upload_action = QAction("⬆️ Upload to Device", self)
        upload_action.triggered.connect(self.upload_selected_files)
        menu.addAction(upload_action)
        
        delete_action = QAction("🗑️ Delete", self)
        delete_action.triggered.connect(self.delete_local_file)
        menu.addAction(delete_action)
        
        menu.exec(self.local_tree.mapToGlobal(position))
    
    def show_device_context_menu(self, position):
        """Show context menu for device files."""
        menu = QMenu(self)
        
        download_action = QAction("⬇️ Download to Local", self)
        download_action.triggered.connect(self.download_selected_files)
        menu.addAction(download_action)
        
        delete_action = QAction("🗑️ Delete", self)
        delete_action.triggered.connect(self.delete_device_file)
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        new_folder_action = QAction("📁 New Folder", self)
        new_folder_action.triggered.connect(self.create_new_folder)
        menu.addAction(new_folder_action)
        
        menu.exec(self.device_list.mapToGlobal(position))
    
    # Bookmark and History Management Methods
    
    def populate_local_path_combo(self):
        """Populate local path combo with history and bookmarks."""
        self.local_path_combo.clear()
        
        # Add current path
        current_path = self.current_local_path
        self.local_path_combo.addItem(current_path)
        self.local_path_combo.setCurrentText(current_path)
        
        # Add separator
        self.local_path_combo.insertSeparator(1)
        
        # Add bookmarks
        bookmarks = self.config.get_bookmarks("local")
        if bookmarks:
            for bookmark in bookmarks:
                self.local_path_combo.addItem(f"⭐ {bookmark['name']}", bookmark['path'])
            self.local_path_combo.insertSeparator(self.local_path_combo.count())
        
        # Add history (excluding current path)
        history = self.config.get_history("local")
        for path in history:
            if path != current_path:
                self.local_path_combo.addItem(f"🕐 {Path(path).name} - {path}", path)
    
    def populate_device_path_combo(self):
        """Populate device path combo with history and bookmarks."""
        self.device_path_combo.clear()
        
        # Add current path
        current_path = self.current_device_path
        self.device_path_combo.addItem(current_path)
        self.device_path_combo.setCurrentText(current_path)
        
        # Add separator
        self.device_path_combo.insertSeparator(1)
        
        # Add bookmarks
        bookmarks = self.config.get_bookmarks("device")
        if bookmarks:
            for bookmark in bookmarks:
                self.device_path_combo.addItem(f"⭐ {bookmark['name']}", bookmark['path'])
            self.device_path_combo.insertSeparator(self.device_path_combo.count())
        
        # Add history (excluding current path)
        history = self.config.get_history("device")
        for path in history:
            if path != current_path:
                path_name = Path(path).name or path.split('/')[-1] or path
                self.device_path_combo.addItem(f"🕐 {path_name} - {path}", path)
    
    def on_local_path_changed(self, text):
        """Handle local path combo text change."""
        # Get the actual path from item data if available
        index = self.local_path_combo.currentIndex()
        if index >= 0:
            item_data = self.local_path_combo.itemData(index)
            if item_data:
                text = item_data
        
        # Navigate to the path if it's different
        if text and text != self.current_local_path:
            self.navigate_to_local_path(text)
    
    def on_device_path_changed(self, text):
        """Handle device path combo text change."""
        # Get the actual path from item data if available
        index = self.device_path_combo.currentIndex()
        if index >= 0:
            item_data = self.device_path_combo.itemData(index)
            if item_data:
                text = item_data
        
        # Navigate to the path if it's different
        if text and text != self.current_device_path:
            self.navigate_to_device_path(text)
    
    def navigate_to_local_path(self, path: str):
        """Navigate to a specific local path."""
        try:
            path_obj = Path(path)
            if path_obj.exists() and path_obj.is_dir():
                self.current_local_path = str(path_obj)
                
                # Add to history
                self.config.add_to_history(self.current_local_path, "local")
                self.config.set_last_path(self.current_local_path, "local")
                
                # Update file system model
                if self.local_model:
                    self.local_tree.setRootIndex(self.local_model.index(self.current_local_path))
                
                # Refresh combo
                self.populate_local_path_combo()
                
        except Exception as e:
            self.logger.error(f"Error navigating to local path {path}: {e}")
            QMessageBox.warning(self, "Navigation Error", f"Could not navigate to: {path}")
    
    def bookmark_local_path(self):
        """Bookmark current local path."""
        current_path = self.local_path_combo.currentText()
        if not current_path:
            return
        
        # Get bookmark name from user
        name, ok = QInputDialog.getText(
            self, 
            "Add Bookmark", 
            "Enter bookmark name:",
            text=Path(current_path).name
        )
        
        if ok and name:
            self.config.add_bookmark(current_path, "local", name)
            self.populate_local_path_combo()
            QMessageBox.information(self, "Bookmark Added", f"Bookmarked: {name}")
    
    def bookmark_device_path(self):
        """Bookmark current device path."""
        current_path = self.device_path_combo.currentText()
        if not current_path:
            return
        
        # Get bookmark name from user
        path_name = Path(current_path).name or current_path.split('/')[-1] or current_path
        name, ok = QInputDialog.getText(
            self, 
            "Add Bookmark", 
            "Enter bookmark name:",
            text=path_name
        )
        
        if ok and name:
            self.config.add_bookmark(current_path, "device", name)
            self.populate_device_path_combo()
            QMessageBox.information(self, "Bookmark Added", f"Bookmarked: {name}")
    
    def closeEvent(self, event):
        """Handle widget close event."""
        self.cleanup()
        super().closeEvent(event)
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if self.transfer_worker and self.transfer_worker.isRunning():
                self.transfer_worker.terminate()
                self.transfer_worker.wait(1000)
            
            if self.listing_worker and self.listing_worker.isRunning():
                self.listing_worker.terminate()
                self.listing_worker.wait(1000)
                
            self.logger.info("File manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error reloading device list model: {e}")
                
    def refresh_theme(self):
        """Refresh theme-related styling for file manager components."""
        try:
            # Force style refresh on tree views
            if hasattr(self, 'local_tree') and self.local_tree:
                self.local_tree.style().unpolish(self.local_tree)
                self.local_tree.style().polish(self.local_tree)
                self.local_tree.update()
                
            if hasattr(self, 'device_list') and self.device_list:
                self.device_list.style().unpolish(self.device_list)
                self.device_list.style().polish(self.device_list)
                self.device_list.update()
                
            # Force refresh on the entire widget
            self.style().unpolish(self)
            self.style().polish(self)
            self.update()
            
            self.logger.info("File manager theme refreshed")
            
        except Exception as e:
            self.logger.error(f"Error refreshing file manager theme: {e}")

    def cleanup(self):
        """Clean up resources."""
        try:
            if self.transfer_worker and self.transfer_worker.isRunning():
                self.transfer_worker.terminate()
                self.transfer_worker.wait(1000)
            
            if self.listing_worker and self.listing_worker.isRunning():
                self.listing_worker.terminate()
                self.listing_worker.wait(1000)
                
            self.logger.info("File manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
