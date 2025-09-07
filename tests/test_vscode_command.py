"""
Test VS Code command execution
"""

import subprocess
import tempfile
import sys
from pathlib import Path

def test_vscode_command():
    """Test different VS Code command formats."""
    print("🧪 Testing VS Code command execution...")
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test file for VS Code")
        temp_file = Path(f.name)
    
    print(f"📄 Created test file: {temp_file}")
    
    # Test different command formats
    commands_to_test = [
        f'code "{temp_file}"',
        f'"code" "{temp_file}"',
        f'"{Path.home()}/AppData/Local/Programs/Microsoft VS Code/bin/code.cmd" "{temp_file}"'
    ]
    
    for i, command in enumerate(commands_to_test, 1):
        print(f"\n{i}. Testing command: {command}")
        try:
            # Test if the command starts without error
            process = subprocess.Popen(command, shell=True)
            
            # Wait a moment to see if it starts successfully
            import time
            time.sleep(1)
            
            # Check if process is still running or completed successfully
            returncode = process.poll()
            if returncode is None:
                print(f"   ✅ Command started successfully (process still running)")
                # Terminate the process to avoid leaving VS Code open
                process.terminate()
            elif returncode == 0:
                print(f"   ✅ Command completed successfully")
            else:
                print(f"   ❌ Command failed with return code {returncode}")
                
        except Exception as e:
            print(f"   ❌ Command failed with exception: {e}")
    
    # Clean up
    temp_file.unlink(missing_ok=True)
    print(f"\n🧹 Cleaned up test file")

if __name__ == "__main__":
    test_vscode_command()
