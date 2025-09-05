"""
File Manager UI

Dual-pane file browser with drag & drop support for file operations.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeView, QLabel, QPushButton, QProgressBar,
    QLineEdit, QTextEdit, QTabWidget, QFrame,
    QToolBar, QFileDialog, QMessageBox, QListWidget,
    QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont, QFileSystemModel


class FileManager(QWidget):
    """File manager widget with local and device file browsers."""
    
    def __init__(self, device_id: str):
        super().__init__()
        self.device_id = device_id
        self.local_model = None
        self.device_model = None
        self.init_ui()
    
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
        
        # Set splitter proportions
        splitter.setSizes([400, 100, 400])
        
        # Create progress panel
        progress_panel = self.create_progress_panel()
        layout.addWidget(progress_panel)
    
    def create_toolbar(self):
        """Create the file manager toolbar."""
        toolbar_frame = QFrame()
        toolbar_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar_layout = QHBoxLayout(toolbar_frame)
        
        # Device info
        device_label = QLabel(f"Device: {self.device_id}")
        device_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        toolbar_layout.addWidget(device_label)
        
        toolbar_layout.addStretch()
        
        # Action buttons
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_files)
        toolbar_layout.addWidget(refresh_btn)
        
        new_folder_btn = QPushButton("📁 New Folder")
        new_folder_btn.clicked.connect(self.create_new_folder)
        toolbar_layout.addWidget(new_folder_btn)
        
        return toolbar_frame
    
    def create_local_panel(self):
        """Create the local file system panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("💻 Local Files")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        # Path input
        self.local_path_input = QLineEdit()
        self.local_path_input.setText(QDir.homePath())
        header_layout.addWidget(self.local_path_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_local_folder)
        header_layout.addWidget(browse_btn)
        
        layout.addLayout(header_layout)
        
        # File tree view
        self.local_tree = QTreeView()
        self.local_model = QFileSystemModel()
        self.local_model.setRootPath(QDir.homePath())
        self.local_tree.setModel(self.local_model)
        self.local_tree.setRootIndex(self.local_model.index(QDir.homePath()))
        
        # Hide unnecessary columns
        self.local_tree.hideColumn(1)  # Size
        self.local_tree.hideColumn(2)  # Type
        self.local_tree.hideColumn(3)  # Date Modified
        
        layout.addWidget(self.local_tree)
        
        # Local file actions
        local_actions = QHBoxLayout()
        
        upload_btn = QPushButton("⬆️ Upload")
        upload_btn.clicked.connect(self.upload_file)
        local_actions.addWidget(upload_btn)
        
        delete_local_btn = QPushButton("🗑️ Delete")
        delete_local_btn.clicked.connect(self.delete_local_file)
        local_actions.addWidget(delete_local_btn)
        
        layout.addLayout(local_actions)
        
        return panel
    
    def create_device_panel(self):
        """Create the device file system panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("📱 Device Files")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        # Path input
        self.device_path_input = QLineEdit()
        self.device_path_input.setText("/sdcard/")
        header_layout.addWidget(self.device_path_input)
        
        navigate_btn = QPushButton("Go")
        navigate_btn.clicked.connect(self.navigate_device_folder)
        header_layout.addWidget(navigate_btn)
        
        layout.addLayout(header_layout)
        
        # Device file list
        self.device_list = QListWidget()
        self.device_list.addItem("📁 Documents")
        self.device_list.addItem("📁 Pictures")
        self.device_list.addItem("📁 Music")
        self.device_list.addItem("📁 Videos")
        self.device_list.addItem("📄 test.txt")
        self.device_list.addItem("📄 config.json")
        layout.addWidget(self.device_list)
        
        # Device file actions
        device_actions = QHBoxLayout()
        
        download_btn = QPushButton("⬇️ Download")
        download_btn.clicked.connect(self.download_file)
        device_actions.addWidget(download_btn)
        
        delete_device_btn = QPushButton("🗑️ Delete")
        delete_device_btn.clicked.connect(self.delete_device_file)
        device_actions.addWidget(delete_device_btn)
        
        layout.addLayout(device_actions)
        
        return panel
    
    def create_transfer_panel(self):
        """Create the transfer controls panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumWidth(120)
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Transfer buttons
        push_btn = QPushButton("➡️\nPush")
        push_btn.setMinimumHeight(60)
        push_btn.clicked.connect(self.push_file)
        layout.addWidget(push_btn)
        
        layout.addSpacing(20)
        
        pull_btn = QPushButton("⬅️\nPull")
        pull_btn.setMinimumHeight(60)
        pull_btn.clicked.connect(self.pull_file)
        layout.addWidget(pull_btn)
        
        layout.addSpacing(20)
        
        sync_btn = QPushButton("🔄\nSync")
        sync_btn.setMinimumHeight(60)
        sync_btn.clicked.connect(self.sync_folders)
        layout.addWidget(sync_btn)
        
        layout.addStretch()
        
        return panel
    
    def create_progress_panel(self):
        """Create the file transfer progress panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumHeight(100)
        layout = QVBoxLayout(panel)
        
        # Progress info
        progress_layout = QHBoxLayout()
        
        self.progress_label = QLabel("Ready")
        progress_layout.addWidget(self.progress_label)
        
        progress_layout.addStretch()
        
        self.speed_label = QLabel("0 KB/s")
        progress_layout.addWidget(self.speed_label)
        
        layout.addLayout(progress_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return panel
    
    def browse_local_folder(self):
        """Browse for local folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.local_path_input.setText(folder)
            self.local_tree.setRootIndex(self.local_model.index(folder))
    
    def navigate_device_folder(self):
        """Navigate to device folder."""
        path = self.device_path_input.text()
        # TODO: Implement device folder navigation
        self.progress_label.setText(f"Navigating to {path}")
    
    def upload_file(self):
        """Upload selected local file to device."""
        # TODO: Implement file upload logic
        self.show_progress("Uploading file...")
    
    def download_file(self):
        """Download selected device file to local."""
        # TODO: Implement file download logic
        self.show_progress("Downloading file...")
    
    def push_file(self):
        """Push file from local to device."""
        # TODO: Implement file push operation
        self.show_progress("Pushing file to device...")
    
    def pull_file(self):
        """Pull file from device to local."""
        # TODO: Implement file pull operation
        self.show_progress("Pulling file from device...")
    
    def sync_folders(self):
        """Sync folders between local and device."""
        # TODO: Implement folder sync
        self.show_progress("Syncing folders...")
    
    def delete_local_file(self):
        """Delete selected local file."""
        reply = QMessageBox.question(
            self, 
            "Delete File", 
            "Are you sure you want to delete the selected file?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement local file deletion
            self.progress_label.setText("Local file deleted")
    
    def delete_device_file(self):
        """Delete selected device file."""
        reply = QMessageBox.question(
            self, 
            "Delete File", 
            "Are you sure you want to delete the selected file from device?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement device file deletion
            self.progress_label.setText("Device file deleted")
    
    def create_new_folder(self):
        """Create new folder on device."""
        # TODO: Implement new folder creation
        self.progress_label.setText("Creating new folder...")
    
    def refresh_files(self):
        """Refresh both file panels."""
        # TODO: Implement file refresh
        self.progress_label.setText("Refreshing files...")
    
    def show_progress(self, message):
        """Show progress for operations."""
        self.progress_label.setText(message)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        # TODO: Implement actual progress tracking
