"""
Quick test for live editor functionality
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services.live_editor import LiveEditorService


def test_editor_detection():
    """Test editor detection and selection."""
    print("🔍 Testing Live Editor Service...")
    
    # Create service
    service = LiveEditorService()
    
    # Test VS Code path detection specifically
    print(f"\n🔍 VS Code path detection:")
    username = os.environ.get('USERNAME', '')
    vscode_paths = [
        "code",  # Try PATH first
        r"C:\Program Files\Microsoft VS Code\bin\code.cmd",
        rf"C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd",
        r"C:\Program Files (x86)\Microsoft VS Code\bin\code.cmd"
    ]
    
    for path in vscode_paths:
        if path == "code":
            available = service.is_command_in_path("code")
            print(f"   {'✅' if available else '❌'} {path} (in PATH: {available})")
        else:
            exists = os.path.exists(path)
            print(f"   {'✅' if exists else '❌'} {path} (exists: {exists})")
    
    # Test default editors
    print(f"\n📋 Default editors for {sys.platform}:")
    default_editors = service.get_default_editors()
    for name, command in default_editors.items():
        available = service.is_editor_available(command)
        print(f"   {name}: {command} {'✅' if available else '❌'}")
    
    # Test available editors
    print(f"\n✅ Available editors on your system:")
    available_editors = service.get_available_editors()
    if available_editors:
        for editor in available_editors:
            print(f"   ✓ {editor['name']} ({editor['command']})")
    else:
        print("   ❌ No editors found!")
    
    # Test default editor command
    default_command = service.get_default_editor_command()
    print(f"\n🎯 Default editor command: {default_command}")
    
    # Cleanup
    service.cleanup()
    print(f"\n🎉 Test completed!")


if __name__ == "__main__":
    test_editor_detection()
