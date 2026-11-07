# -*- mode: python ; coding: utf-8 -*-
import sys

is_darwin = sys.platform == 'darwin'

platform_hidden = (
    ['platforms.macos', 'pynput.keyboard._darwin', 'pynput.mouse._darwin']
    if is_darwin
    else ['platforms.windows', 'pynput.keyboard._win32', 'pynput.mouse._win32']
)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('config.json', '.'), ('shotgun.wav', '.')],
    hiddenimports=[
        'platforms',
        'pygame',
        'numpy',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ] + platform_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='KeyboardShotgun',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='KeyboardShotgun',
)

if is_darwin:
    app = BUNDLE(
        coll,
        name='KeyboardShotgun.app',
        icon=None,
        bundle_identifier='com.keyboardshotgun.app',
        info_plist={
            'CFBundleName': 'Keyboard Shotgun',
            'CFBundleDisplayName': 'Keyboard Shotgun',
            'CFBundleIdentifier': 'com.keyboardshotgun.app',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSAppleEventsUsageDescription': 'Keyboard Shotgun requires Accessibility permission to detect global keypresses.',
            'NSInputMonitoringUsageDescription': 'Keyboard Shotgun requires Input Monitoring permission to detect global keypresses.',
        },
    )

