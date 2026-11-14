# Build script for Keyboard Shotgun on Windows (PowerShell)
# Produces a standalone, single-directory or single-file executable using PyInstaller.

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Building Keyboard Shotgun for Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$ScriptDir\.."
Set-Location $ProjectRoot

# Verify virtual environment or python
$PythonPath = "$ProjectRoot\.venv\Scripts\python.exe"
if (-not (Test-Path $PythonPath)) {
    $PythonPath = "python"
}

Write-Host "Using Python: $PythonPath" -ForegroundColor Green

# Check PyInstaller installation
& $PythonPath -m PyInstaller --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
    & $PythonPath -m pip install pyinstaller
}

# Ensure config.json exists
if (-not (Test-Path "$ProjectRoot\config.json")) {
    Write-Host "Warning: config.json not found in root, creating default." -ForegroundColor Yellow
    & $PythonPath -c "from core.config_manager import ConfigManager; ConfigManager().reset_to_defaults()"
}

# Verify shotgun.wav notice
if (-not (Test-Path "$ProjectRoot\shotgun.wav")) {
    Write-Host "NOTE: shotgun.wav is not present in root yet. Ensure shotgun.wav is placed alongside the built executable." -ForegroundColor Yellow
}

# Ensure logo.ico exists for executable icon
if (-not (Test-Path "$ProjectRoot\logo.ico") -and (Test-Path "$ProjectRoot\logo.png")) {
    Write-Host "Generating logo.ico from logo.png..." -ForegroundColor Cyan
    & $PythonPath -c "from PySide6.QtGui import QImage; from PySide6.QtCore import Qt; img = QImage('logo.png').scaled(256, 256, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation); img.save('logo.ico', 'ICO')"
}

Write-Host "Executing PyInstaller build using KeyboardShotgun.spec..." -ForegroundColor Green
& $PythonPath -m PyInstaller `
    --noconfirm `
    --clean `
    KeyboardShotgun.spec

if ($LASTEXITCODE -eq 0) {
    # Ensure assets are copied to dist root alongside executable
    Copy-Item -Path "$ProjectRoot\shotgun.wav" -Destination "$ProjectRoot\dist\KeyboardShotgun\" -Force -ErrorAction SilentlyContinue
    Copy-Item -Path "$ProjectRoot\config.json" -Destination "$ProjectRoot\dist\KeyboardShotgun\" -Force -ErrorAction SilentlyContinue
    Copy-Item -Path "$ProjectRoot\logo.png" -Destination "$ProjectRoot\dist\KeyboardShotgun\" -Force -ErrorAction SilentlyContinue
    Copy-Item -Path "$ProjectRoot\logo.ico" -Destination "$ProjectRoot\dist\KeyboardShotgun\" -Force -ErrorAction SilentlyContinue

    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "Build complete! Executable located at: dist\KeyboardShotgun\KeyboardShotgun.exe" -ForegroundColor Green
    Write-Host "Application icon and runtime assets successfully bundled." -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host "PyInstaller build failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit 1
}
