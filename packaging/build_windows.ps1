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

# PyInstaller command:
# Include shotgun.wav and config.json as data assets if present
$DataArgs = @()
if (Test-Path "$ProjectRoot\config.json") {
    $DataArgs += "--add-data=config.json;."
}
if (Test-Path "$ProjectRoot\shotgun.wav") {
    $DataArgs += "--add-data=shotgun.wav;."
}

Write-Host "Executing PyInstaller build..." -ForegroundColor Green
& $PythonPath -m PyInstaller `
    --name="KeyboardShotgun" `
    --onedir `
    --windowed `
    --noconfirm `
    --clean `
    @DataArgs `
    --hidden-import="platforms" `
    --hidden-import="platforms.windows" `
    --hidden-import="pynput.keyboard._win32" `
    --hidden-import="pynput.mouse._win32" `
    --hidden-import="pygame" `
    --hidden-import="numpy" `
    --hidden-import="PySide6.QtCore" `
    --hidden-import="PySide6.QtGui" `
    --hidden-import="PySide6.QtWidgets" `
    main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "Build complete! Executable located at: dist\KeyboardShotgun\KeyboardShotgun.exe" -ForegroundColor Green
    Write-Host "If shotgun.wav was not embedded, make sure to copy shotgun.wav into dist\KeyboardShotgun\" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host "PyInstaller build failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit 1
}
