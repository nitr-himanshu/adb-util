"""
Main Application Window

Main window class that contains the tab management system and overall application layout.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QMenuBar, QStatusBar, QLabel, 
    QPushButton, QListWidget, QGridLayout, QFrame,
    QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont, QAction

from utils.logger import get_logger


class MainWindow(QMainWindow):
    """Main application window with tab management."""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.tab_widget = None
        self.device_list = None
        self.status_label = None
        
        self.logger.info("Initializing main window...")
        self.init_ui()
        self.logger.info("Main window initialization complete")
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("ADB-UTIL - Android Debug Bridge Utility")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create device panel (left side)
        device_panel = self.create_device_panel()
        splitter.addWidget(device_panel)
        
        # Create main content area (right side)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        splitter.addWidget(self.tab_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.create_status_bar()
        
        # Show home tab by default
        self.show_home_tab()
    
    def create_device_panel(self):
        """Create the device selection panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumWidth(350)
        
        layout = QVBoxLayout(panel)
        
        # Title
        title_label = QLabel("Connected Devices")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Device list
        self.device_list = QListWidget()
        self.device_list.addItem("📱 Device 1 (emulator-5554)")
        self.device_list.addItem("📱 Device 2 (ABC123DEF456)")
        self.device_list.addItem("📱 Device 3 (192.168.1.100:5555)")
        layout.addWidget(self.device_list)
        
        # Device actions
        actions_label = QLabel("Device Actions")
        actions_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(actions_label)
        
        # Action buttons in grid
        actions_layout = QGridLayout()
        
        file_manager_btn = QPushButton("📁 File Manager")
        file_manager_btn.clicked.connect(lambda: self.open_device_tab("file_manager"))
        actions_layout.addWidget(file_manager_btn, 0, 0)
        
        terminal_btn = QPushButton("💻 Terminal")
        terminal_btn.clicked.connect(lambda: self.open_device_tab("terminal"))
        actions_layout.addWidget(terminal_btn, 0, 1)
        
        logging_btn = QPushButton("📊 Logging")
        logging_btn.clicked.connect(lambda: self.open_device_tab("logging"))
        actions_layout.addWidget(logging_btn, 1, 0)
        
        utils_btn = QPushButton("🛠️ Utils")
        utils_btn.clicked.connect(lambda: self.open_device_tab("utils"))
        actions_layout.addWidget(utils_btn, 1, 1)
        
        layout.addLayout(actions_layout)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Devices")
        refresh_btn.clicked.connect(self.refresh_devices)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        
        return panel
    
    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_connection_action = QAction("&New Connection", self)
        new_connection_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_connection_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        preferences_action = QAction("&Preferences", self)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.triggered.connect(self.show_preferences)
        tools_menu.addAction(preferences_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_status_bar(self):
        """Create the status bar."""
        status_bar = self.statusBar()
        
        self.status_label = QLabel("Ready")
        status_bar.addWidget(self.status_label)
        
        # Device count
        device_count_label = QLabel("Devices: 3")
        status_bar.addPermanentWidget(device_count_label)
        
        # ADB status
        adb_status_label = QLabel("ADB: Connected")
        status_bar.addPermanentWidget(adb_status_label)
    
    def show_home_tab(self):
        """Show the home/welcome tab."""
        home_widget = self.create_home_widget()
        self.tab_widget.addTab(home_widget, "🏠 Home")
    
    def create_home_widget(self):
        """Create the home/welcome widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Welcome message
        welcome_label = QLabel("Welcome to ADB-UTIL")
        welcome_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)
        
        subtitle_label = QLabel("Android Debug Bridge Utility")
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: gray;")
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(30)
        
        # Quick start instructions
        instructions_label = QLabel("""
        Getting Started:
        
        1. Select a device from the left panel
        2. Choose an operation mode:
           📁 File Manager - Transfer files between device and computer
           💻 Terminal - Execute ADB commands
           📊 Logging - View real-time logcat output
           🛠️ Utils - Network info and port forwarding
        
        3. Click the mode button to open a new tab
        """)
        instructions_label.setFont(QFont("Arial", 12))
        instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions_label.setStyleSheet("background-color: #f0f0f0; padding: 20px; border-radius: 10px;")
        layout.addWidget(instructions_label)
        
        return widget
    
    def open_device_tab(self, mode):
        """Open a new tab for the selected device and mode."""
        if not self.device_list.currentItem():
            self.logger.warning("Attempted to open device tab without selecting a device")
            QMessageBox.warning(self, "No Device Selected", "Please select a device first.")
            return
        
        device_text = self.device_list.currentItem().text()
        device_id = device_text.split("(")[1].split(")")[0]  # Extract device ID
        
        self.logger.info(f"Opening {mode} tab for device: {device_id}")
        
        tab_title = f"{device_id}-{mode}"
        
        # Check if tab already exists
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == tab_title:
                self.logger.debug(f"Tab {tab_title} already exists, switching to it")
                self.tab_widget.setCurrentIndex(i)
                return
        
        # Create new tab based on mode
        try:
            if mode == "file_manager":
                from gui.file_manager import FileManager
                widget = FileManager(device_id)
            elif mode == "terminal":
                from gui.terminal import Terminal
                widget = Terminal(device_id)
            elif mode == "logging":
                from gui.logging import Logging
                widget = Logging(device_id)
            elif mode == "utils":
                from gui.utils import Utils
                widget = Utils(device_id)
            else:
                self.logger.warning(f"Unknown mode requested: {mode}")
                widget = QLabel(f"Mode '{mode}' not implemented yet")
            
            self.tab_widget.addTab(widget, tab_title)
            self.tab_widget.setCurrentWidget(widget)
            self.logger.info(f"Successfully created {mode} tab for device {device_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to create {mode} tab for device {device_id}: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to create {mode} tab: {str(e)}")
    
    def close_tab(self, index):
        """Close a tab."""
        if index > 0:  # Don't close the home tab
            tab_name = self.tab_widget.tabText(index)
            self.logger.info(f"Closing tab: {tab_name}")
            self.tab_widget.removeTab(index)
        else:
            self.logger.debug("Attempted to close home tab - ignored")
    
    def refresh_devices(self):
        """Refresh the device list."""
        self.logger.info("Refreshing device list...")
        self.status_label.setText("Refreshing devices...")
        # TODO: Implement actual device discovery
        self.status_label.setText("Devices refreshed")
        self.logger.info("Device list refresh completed")
    
    def show_about(self):
        """Show about dialog."""
        self.logger.debug("Showing about dialog")
        QMessageBox.about(
            self,
            "About ADB-UTIL",
            "ADB-UTIL v1.0.0\n\n"
            "A comprehensive Python-based desktop application\n"
            "for Android Debug Bridge (ADB) operations.\n\n"
            "Built with PyQt6"
        )
    
    def show_preferences(self):
        """Show preferences dialog."""
        self.logger.debug("Opening preferences dialog")
        try:
            from gui.preferences import PreferencesDialog
            preferences_dialog = PreferencesDialog(self)
            preferences_dialog.exec()
        except Exception as e:
            self.logger.error(f"Error opening preferences dialog: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open preferences: {e}")
