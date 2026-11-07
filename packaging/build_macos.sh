#!/usr/bin/env bash
# Build script for Keyboard Shotgun on macOS.
# Produces a standalone .app bundle using PyInstaller.
# Note: macOS builds must be performed natively on macOS.

set -e

echo "========================================"
echo "Building Keyboard Shotgun for macOS"
echo "========================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON_CMD="python3"
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
fi

echo "Using Python: $PYTHON_CMD"
ARCH=$($PYTHON_CMD -c "import platform; print(platform.machine())")
echo "Building for target architecture: $ARCH"

# Check PyInstaller
if ! $PYTHON_CMD -m pyinstaller --version >/dev/null 2>&1; then
    echo "Installing PyInstaller..."
    $PYTHON_CMD -m pip install pyinstaller
fi

DATA_ARGS=()
if [ -f "$PROJECT_ROOT/config.json" ]; then
    DATA_ARGS+=("--add-data=config.json:.")
fi
if [ -f "$PROJECT_ROOT/shotgun.wav" ]; then
    DATA_ARGS+=("--add-data=shotgun.wav:.")
fi

echo "Running PyInstaller..."
$PYTHON_CMD -m pyinstaller \
    --name="KeyboardShotgun" \
    --windowed \
    --noconfirm \
    --clean \
    --osx-bundle-identifier="com.keyboardshotgun.app" \
    "${DATA_ARGS[@]}" \
    --hidden-import="pynput.keyboard._darwin" \
    --hidden-import="pynput.mouse._darwin" \
    --hidden-import="pygame" \
    --hidden-import="numpy" \
    --hidden-import="PySide6.QtCore" \
    --hidden-import="PySide6.QtGui" \
    --hidden-import="PySide6.QtWidgets" \
    main.py

echo ""
echo "========================================"
echo "Build complete! Application bundle created at: dist/KeyboardShotgun.app"
echo "Target architecture: $ARCH"
echo ""
echo "Important macOS Permission Notice:"
echo "When launching KeyboardShotgun.app for the first time:"
echo "1. Go to System Settings > Privacy & Security > Accessibility."
echo "2. Add/enable KeyboardShotgun.app to grant global key detection rights."
echo "3. Also check System Settings > Privacy & Security > Input Monitoring."
echo "========================================"

