"""
Script to create PyPotteryLayout executable (Flask Version)
"""

import subprocess
import sys
import os

def create_executable():
    """Create executable using PyInstaller"""
    
    # PyInstaller options for Flask app
    options = [
        "flask_launcher.py",  # Main script (Flask launcher)
        "--onefile",   # Create single executable file
        "--noconsole",   # Hide console window
        "--name=PyPotteryLayout",  # Executable name
        "--icon=icon_app.ico",  # Application icon
        
        # Include templates and static files (essential for Flask)
        "--add-data=templates;templates",
        "--add-data=static;static",
        
        # Include images folder if it exists
        "--add-data=imgs;imgs" if os.path.exists("imgs") else "",
        
        # Hidden imports that PyInstaller might miss
        "--hidden-import=flask",
        "--hidden-import=werkzeug",
        "--hidden-import=jinja2",
        "--hidden-import=PIL",
        "--hidden-import=openpyxl",
        "--hidden-import=rectpack",
        "--hidden-import=backend_logic",
        
        "--clean",     # Clean cache
        "--noconfirm", # Don't ask for confirmation
    ]
    
    # Remove empty options
    options = [opt for opt in options if opt]
    
    # Remove icon option if file doesn't exist
    if not os.path.exists("icon_app.ico"):
        options = [opt for opt in options if not opt.startswith("--icon")]
    
    # Run PyInstaller
    cmd = [sys.executable, "-m", "PyInstaller"] + options
    
    print("=" * 70)
    print("Creating PyPotteryLayout executable (Flask version)...")
    print("=" * 70)
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Executable created successfully!")
        if result.stdout:
            print(f"\nBuild output:\n{result.stdout}")
        
        # Find executable file
        exe_path = os.path.join("dist", "PyPotteryLayout.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024*1024)
            print("\n" + "=" * 70)
            print(f"📦 Executable location: {os.path.abspath(exe_path)}")
            print(f"📊 Size: {size_mb:.1f} MB")
            print("=" * 70)
            print("\nℹ️  How to use:")
            print("   1. Run PyPotteryLayout.exe")
            print("   2. The browser will open automatically")
            print("   3. Use the app in your browser")
            print("   4. Press CTRL+C in the console to stop the server")
        else:
            print("\n⚠️  Warning: Executable file not found in dist/ folder")
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error creating executable:")
        if e.stderr:
            print(f"Error details:\n{e.stderr}")
        print(f"Return code: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_executable()
    if success:
        print("\n✅ Process completed successfully!")
    else:
        print("\n❌ Error creating executable")
        sys.exit(1)
