"""
Config Manager

Application configuration management and settings persistence.
"""

import json
from pathlib import Path
from typing import Any, Dict
from datetime import datetime


class ConfigManager:
    """Manages application configuration and settings."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path.home() / ".adb-util" / config_file
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = self.get_default_config()
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = self.get_default_config()
    
    def save_config(self):
        """Save configuration to file."""
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value
        self.save_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "window_geometry": None,
            "theme": "system",
            "adb_path": "adb",
            "auto_detect_devices": True,
            "log_level": "INFO",
            "max_log_lines": 10000,
            "bookmarks": {
                "local": [],
                "device": []
            },
            "history": {
                "local": [],
                "device": []
            },
            "last_paths": {
                "local": str(Path.home()),
                "device": "/sdcard/"
            },
            "custom_editors": [],
            "default_editor": None,
            "live_edit_enabled": True,
            "auto_upload_on_save": True
        }
    
    def add_bookmark(self, path: str, location_type: str, name: str = None):
        """Add a bookmark for local or device path."""
        if location_type not in ["local", "device"]:
            return
        
        bookmarks = self.get("bookmarks", {})
        if location_type not in bookmarks:
            bookmarks[location_type] = []
        
        # Check if bookmark already exists
        for bookmark in bookmarks[location_type]:
            if bookmark["path"] == path:
                return  # Already bookmarked
        
        # Add new bookmark
        bookmark = {
            "name": name or Path(path).name or path,
            "path": path,
            "created": datetime.now().isoformat()
        }
        
        bookmarks[location_type].append(bookmark)
        self.set("bookmarks", bookmarks)
    
    def remove_bookmark(self, path: str, location_type: str):
        """Remove a bookmark."""
        if location_type not in ["local", "device"]:
            return
        
        bookmarks = self.get("bookmarks", {})
        if location_type not in bookmarks:
            return
        
        bookmarks[location_type] = [
            b for b in bookmarks[location_type] if b["path"] != path
        ]
        self.set("bookmarks", bookmarks)
    
    def get_bookmarks(self, location_type: str) -> list:
        """Get bookmarks for local or device."""
        bookmarks = self.get("bookmarks", {})
        return bookmarks.get(location_type, [])
    
    def add_to_history(self, path: str, location_type: str):
        """Add path to history."""
        if location_type not in ["local", "device"]:
            return
        
        history = self.get("history", {})
        if location_type not in history:
            history[location_type] = []
        
        # Remove if already exists to move to front
        history[location_type] = [p for p in history[location_type] if p != path]
        
        # Add to front
        history[location_type].insert(0, path)
        
        # Keep only last 20 items
        history[location_type] = history[location_type][:20]
        
        self.set("history", history)
    
    def get_history(self, location_type: str) -> list:
        """Get history for local or device."""
        history = self.get("history", {})
        return history.get(location_type, [])
    
    def set_last_path(self, path: str, location_type: str):
        """Set last used path."""
        if location_type not in ["local", "device"]:
            return
        
        last_paths = self.get("last_paths", {})
        last_paths[location_type] = path
        self.set("last_paths", last_paths)
    
    def get_last_path(self, location_type: str) -> str:
        """Get last used path."""
        last_paths = self.get("last_paths", {})
        if location_type == "local":
            return last_paths.get("local", str(Path.home()))
        elif location_type == "device":
            return last_paths.get("device", "/sdcard/")
        return ""
    
    def add_custom_editor(self, name: str, command: str):
        """Add a custom editor."""
        custom_editors = self.get("custom_editors", [])
        
        # Check if editor already exists
        for editor in custom_editors:
            if editor.get("name") == name:
                # Update existing
                editor["command"] = command
                self.set("custom_editors", custom_editors)
                return
        
        # Add new editor
        custom_editors.append({
            "name": name,
            "command": command,
            "added": datetime.now().isoformat()
        })
        self.set("custom_editors", custom_editors)
    
    def remove_custom_editor(self, name: str):
        """Remove a custom editor."""
        custom_editors = self.get("custom_editors", [])
        custom_editors = [e for e in custom_editors if e.get("name") != name]
        self.set("custom_editors", custom_editors)
    
    def get_custom_editors(self) -> list:
        """Get list of custom editors."""
        return self.get("custom_editors", [])
    
    def set_default_editor(self, command: str):
        """Set the default editor command."""
        self.set("default_editor", command)
    
    def get_default_editor(self) -> str:
        """Get the default editor command."""
        return self.get("default_editor", None)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value."""
        return self.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a specific setting value."""
        self.set(key, value)
