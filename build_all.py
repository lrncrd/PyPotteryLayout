#!/usr/bin/env python
"""
Build script for creating standalone executables for all platforms.
Run locally: python build_all.py
"""

import os
import sys
import platform
import subprocess
import shutil

def build_executable():
    """Build the executable for the current platform."""

    print(f"Building PyPotteryLayout for {platform.system()}...")

    # Clean previous builds
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')

    # Determine platform-specific options
    system = platform.system()

    if system == 'Windows':
        icon = '--icon=imgs/icon_app.ico' if os.path.exists('imgs/icon_app.ico') else ''
        separator = ';'
        exe_name = 'PyPotteryLayout.exe'
    elif system == 'Darwin':  # macOS
        icon = '--icon=imgs/icon_app.icns' if os.path.exists('imgs/icon_app.icns') else ''
        separator = ':'
        exe_name = 'PyPotteryLayout'
    else:  # Linux
        icon = ''
        separator = ':'
        exe_name = 'PyPotteryLayout'

    # Build command
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=PyPotteryLayout',
        f'--add-data=imgs{separator}imgs',
    ]

    if icon:
        cmd.append(icon)

    # Add hidden imports
    hidden_imports = [
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'openpyxl',
        'rectpack',
    ]

    for import_name in hidden_imports:
        cmd.append(f'--hidden-import={import_name}')

    # Add the main script
    cmd.append('gui_app.py')

    print("Running:", ' '.join(cmd))

    # Run PyInstaller
    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode == 0:
        print(f"\n✅ Build successful!")
        print(f"Executable location: dist/{exe_name}")

        # Create distribution folder
        dist_folder = f'PyPotteryLayout-{system}'
        if os.path.exists(dist_folder):
            shutil.rmtree(dist_folder)
        os.makedirs(dist_folder)

        # Copy executable
        if system == 'Windows':
            shutil.copy(f'dist/{exe_name}', dist_folder)
        else:
            shutil.copy(f'dist/{exe_name}', dist_folder)
            os.chmod(f'{dist_folder}/{exe_name}', 0o755)

        # Create README
        with open(f'{dist_folder}/README.txt', 'w') as f:
            f.write("PyPotteryLayout v2.0\n")
            f.write("===================\n\n")
            f.write("Authors: Lorenzo Cardarelli and Enzo Cocca\n")
            f.write("License: Apache License 2.0\n\n")
            f.write("How to run:\n")
            if system == 'Windows':
                f.write("- Double-click PyPotteryLayout.exe\n")
            else:
                f.write("- Double-click PyPotteryLayout or\n")
                f.write("- Open terminal and run: ./PyPotteryLayout\n")

        # Create ZIP
        shutil.make_archive(dist_folder, 'zip', dist_folder)
        print(f"📦 Distribution package created: {dist_folder}.zip")

        return True
    else:
        print(f"\n❌ Build failed with return code {result.returncode}")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""

    print("Checking dependencies...")

    try:
        import PIL
        print("✓ Pillow installed")
    except ImportError:
        print("✗ Pillow not found - run: pip install Pillow")
        return False

    try:
        import openpyxl
        print("✓ openpyxl installed")
    except ImportError:
        print("✗ openpyxl not found - run: pip install openpyxl")
        return False

    try:
        import rectpack
        print("✓ rectpack installed")
    except ImportError:
        print("✗ rectpack not found - run: pip install rectpack")
        return False

    # Check for PyInstaller
    result = subprocess.run(['pip', 'show', 'pyinstaller'],
                          capture_output=True, text=True)
    if result.returncode != 0:
        print("✗ PyInstaller not found - run: pip install pyinstaller")
        return False
    print("✓ PyInstaller installed")

    return True

def main():
    """Main build function."""

    print("=" * 50)
    print("PyPotteryLayout Build Script")
    print("=" * 50)
    print()

    # Check Python version
    if sys.version_info < (3, 7):
        print(f"❌ Python 3.7+ required. Current version: {sys.version}")
        return 1

    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print()

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Missing dependencies. Install them and try again.")
        return 1

    print()

    # Build executable
    if build_executable():
        print("\n🎉 Build completed successfully!")
        return 0
    else:
        print("\n❌ Build failed. Check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())