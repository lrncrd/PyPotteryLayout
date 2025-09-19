# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

# Determine the correct separator for data files
separator = ':' if sys.platform != 'win32' else ';'

a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('imgs', 'imgs'),  # Include all images
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'openpyxl',
        'rectpack',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PyPotteryLayout',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for windowed mode
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# For macOS, create an app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='PyPotteryLayout.app',
        icon='imgs/icon_app.icns',
        bundle_identifier='com.pypotterylayout.app',
        info_plist={
            'CFBundleName': 'PyPotteryLayout',
            'CFBundleDisplayName': 'PyPotteryLayout',
            'CFBundleGetInfoString': 'PyPotteryLayout v2.0',
            'CFBundleIdentifier': 'com.pypotterylayout.app',
            'CFBundleVersion': '2.0.0',
            'CFBundleShortVersionString': '2.0',
            'NSHighResolutionCapable': 'True',
            'NSHumanReadableCopyright': 'Copyright © 2025 Lorenzo Cardarelli and Enzo Cocca',
        },
    )