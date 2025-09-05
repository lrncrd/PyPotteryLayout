"""
Script to create PyPotteryLayout executable
"""

import subprocess
import sys
import os

def create_executable():
    """Create executable using PyInstaller"""
    
    # PyInstaller options
    options = [
        "gui_app.py",  # Main script
        "--onefile",   # Create single executable file
        "--windowed",  # Hide console (for GUI apps)
        "--name=PyPotteryLayout",  # Executable name
        "--icon=icon.ico",  # Icon (if available)
        "--add-data=imgs;imgs",  # Include images folder if needed
        "--clean",     # Clean cache
        "--noconfirm", # Don't ask for confirmation
    ]
    
    # Remove icon option if file doesn't exist
    if not os.path.exists("icon.ico"):
        options = [opt for opt in options if not opt.startswith("--icon")]
    
    # Remove images option if folder is not needed for executable
    if not os.path.exists("imgs") or not any(f.endswith(('.py', '.pyd')) for f in os.listdir("imgs") if os.path.isfile(os.path.join("imgs", f))):
        options = [opt for opt in options if not opt.startswith("--add-data")]
    
    # Run PyInstaller
    cmd = [sys.executable, "-m", "PyInstaller"] + options
    
    print("Creating executable...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Executable created successfully!")
        print(f"Output: {result.stdout}")
        
        # Find executable file
        exe_path = os.path.join("dist", "PyPotteryLayout.exe")
        if os.path.exists(exe_path):
            print(f"\nExecutable available at: {os.path.abspath(exe_path)}")
            print(f"Size: {os.path.getsize(exe_path) / (1024*1024):.1f} MB")
        else:
            print("Warning: Executable file not found in dist/ folder")
            
    except subprocess.CalledProcessError as e:
        print(f"Error creating executable:")
        print(f"Stderr: {e.stderr}")
        print(f"Return code: {e.returncode}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_executable()
    if success:
        print("\n✅ Process completed successfully!")
    else:
        print("\n❌ Error creating executable")
        sys.exit(1)
