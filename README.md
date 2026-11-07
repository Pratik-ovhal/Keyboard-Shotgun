# Keyboard Shotgun 💥

**Keyboard Shotgun** is a cross-platform desktop application that detects global keyboard keypresses and plays realistic shotgun sound effects whenever any key is pressed.

It runs smoothly on **Windows 11** and **macOS** (both Apple Silicon and Intel), offering both a sleek dark desktop GUI for configuration and an unobtrusive background system tray mode.

---

## Features

- **Global Keypress Detection**: Detects all physical keystrokes (letters, numbers, space, enter, modifiers, function keys, arrows) across the entire operating system using `pynput`.
- **Key-Repeat Suppression**: Holding down a key triggers only a single sound; normal OS auto-repeat events are cleanly ignored.
- **Privacy & Security First**: Never records, logs, transmits, or inspects typed text or characters. Only high-resolution timestamp triggers are queued.
- **NumPy Pitch Variation**: Generates 8–12 pitch-shifted variations in memory at startup using high-quality NumPy resampling. Adds realistic acoustic variety without modifying the original WAV file or introducing latency during playback.
- **Ultra-Low Latency Pipeline**: Decouples keyboard event detection from audio playback using a dedicated, thread-safe audio worker thread and lock-free queue. Keyboard-to-audio software dispatch latency is typically under 1 ms.
- **Multi-Channel Polyphony**: Supports up to 8 (or more, configurable) simultaneous playback channels via `pygame.mixer`, allowing overlapping sounds during rapid typing without clipping or cutting off audio tails.
- **Modern PySide6 GUI**: Clean, dark-mode desktop interface with live status badge, master volume slider, mute toggle, test sound button, and comprehensive audio/general settings.
- **Background Tray Integration**: Minimize to the Windows System Tray or macOS Menu Bar. The audio engine keeps running in the background when the GUI is closed.
- **Resilient Configuration**: Stores settings in `config.json`. If missing or corrupted, it automatically recovers with safe defaults instead of crashing.
- **Latency Benchmarking**: Records and displays live software processing delay (trigger to audio dispatch) on the dashboard.

---

## Operating Modes

1. **GUI Mode (Default)**:
   Launches the full desktop interface. You can adjust volume, tune pitch variation intensity, configure channels, toggle mute, and run latency benchmarks.
   ```bash
   python main.py
   ```
   Or explicitly:
   ```bash
   python main.py --gui
   ```

2. **Background Mode**:
   Runs quietly in the system tray with no visible main window. Ideal for daily background use.
   ```bash
   python main.py --background
   ```
   *(You can also enable "Start application in background" in the GUI settings).*

---

## Project Structure

```
KeyboardShotgun/
├── main.py                     # Application entry point and lifecycle manager
├── shotgun.wav                 # Primary shotgun audio source (placed in root)
├── requirements.txt            # Python dependencies
├── config.json                 # Persistent application settings
├── README.md                   # Full documentation and guide
├── .gitignore                  # Git exclusions
│
├── core/
│   ├── __init__.py
│   ├── sound_engine.py         # Pygame audio engine & NumPy pitch shifting
│   ├── keyboard_listener.py    # Global pynput listener with key-repeat filter
│   ├── event_handler.py        # Asynchronous event queue and audio worker
│   └── config_manager.py       # Configuration manager with self-healing recovery
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py          # PySide6 modern dark dashboard
│   ├── tray_manager.py         # System tray icon, notifications, & menu
│   └── styles.py               # Custom QSS stylesheet
│
├── platform/
│   ├── __init__.py             # Cross-platform compatibility layer
│   ├── windows.py              # Windows startup registry integration
│   └── macos.py                # macOS accessibility checks & LaunchAgents
│
├── tests/
│   ├── test_config.py          # Configuration loading, clamping, recovery tests
│   ├── test_audio_engine.py    # NumPy resampling, volume, mute, latency tests
│   ├── test_keyboard_listener.py# Key repeat suppression, bursts, cooldown tests
│   └── test_gui_and_integration.py # Overlap and tray minimization tests
│
└── packaging/
    ├── build_windows.ps1       # Windows standalone PyInstaller build script
    └── build_macos.sh          # macOS standalone .app bundle build script
```

---

## Requirements & Setup

### Prerequisites
- **Python 3.12**
- Audio playback device (speakers or headphones)
- `shotgun.wav` audio file placed in the project root directory

### 1. Clone & Set Up Virtual Environment

```bash
# Clone the repository
git clone https://github.com/your-username/KeyboardShotgun.git
cd KeyboardShotgun

# Create Python 3.12 virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Windows (Command Prompt):
.\.venv\Scripts\activate.bat
# macOS / Linux:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Add `shotgun.wav`

Place your `shotgun.wav` file into the root of `KeyboardShotgun/`.
If the audio file is missing, the application will alert you with an actionable notice and allow you to load it once placed.

---

## Running the Application

### Launch with Desktop GUI
```bash
python main.py
```

### Launch in Background Tray Mode
```bash
python main.py --background
```

---

## Configuration (`config.json`)

Settings are stored in `config.json` in the root folder:

```json
{
  "master_volume": 0.8,
  "is_muted": false,
  "pitch_variation_enabled": true,
  "pitch_intensity": 0.08,
  "num_variations": 10,
  "max_channels": 8,
  "cooldown_duration": 0.0,
  "start_in_background": false,
  "minimize_to_tray": true,
  "launch_on_startup": false,
  "show_permission_notifications": true
}
```

- **`master_volume`**: Master gain (0.0 to 1.0).
- **`is_muted`**: Master mute toggle (boolean).
- **`pitch_variation_enabled`**: Whether to play pitch-varied sounds (boolean).
- **`pitch_intensity`**: Amount of pitch variation around the base tone (e.g., `0.08` is ±8%).
- **`num_variations`**: Number of pitch variations generated in memory at startup (8 to 16).
- **`max_channels`**: Number of simultaneous audio playback channels (minimum 4).
- **`cooldown_duration`**: Minimum delay between sounds in seconds (`0.0` for no cooldown).
- **`minimize_to_tray`**: If true, clicking 'X' minimizes to system tray instead of exiting.
- **`launch_on_startup`**: Automatically start on Windows/macOS login.

---

## Platform-Specific Details

### Windows 11
- Global key hooks run in standard user mode without requiring administrator elevation.
- Optional launch-on-startup is managed through `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
- Full system tray integration with double-click restore, notifications, and right-click actions.

### macOS (Intel & Apple Silicon)
- **Accessibility & Input Monitoring Permissions**:
  macOS security requires permission to detect global keyboard input across other applications.
  1. Open **System Settings > Privacy & Security > Accessibility**.
  2. Enable the toggle for **Keyboard Shotgun** (or Terminal / Python if running from source).
  3. Also open **Privacy & Security > Input Monitoring** and verify permission is granted.
  4. Relaunch the application if prompted.
- **Launch on Login**: Managed via `~/Library/LaunchAgents/com.keyboardshotgun.startup.plist`.
- Native builds supported on both Apple Silicon (`arm64`) and Intel (`x86_64`).

---

## Performance & Latency Benchmarks

Keyboard Shotgun is designed for high-performance audio onset:
- **Audio Buffer**: Pygame mixer is initialized with a 512-sample buffer (`~11.6 ms` buffer latency at 44.1 kHz).
- **Zero In-Callback Work**: The keyboard listener only captures `time.perf_counter()` and pushes it to an asynchronous queue. All processing happens on the audio worker thread.
- **Pre-Generated Variations**: NumPy pitch shifting runs **strictly once at application launch**. No audio processing occurs during playback.
- **Software Processing Delay**: The dashboard displays real-time software latency (elapsed time from keyboard event reception to audio hardware dispatch), consistently measuring **< 1.0 ms**.

> **Note on Latency Measurement**: The software latency metric measures event-to-dispatch time inside the operating system and application. It distinguishes software processing delay from physical speaker/DAC output latency, which depends on audio hardware and drivers.

---

## Packaging Standalone Executables

### Building for Windows
Build a standalone Windows executable (requires no Python installation on client machines):

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
```

The resulting executable will be in `dist\KeyboardShotgun\KeyboardShotgun.exe`.

### Building for macOS
Build a standalone `.app` bundle natively on macOS:

```bash
chmod +x packaging/build_macos.sh
./packaging/build_macos.sh
```

The resulting application bundle will be in `dist/KeyboardShotgun.app`.

---

## Running the Test Suite

Run all automated unit and integration tests using `pytest`:

```bash
pytest -v
```

Tests verify:
1. Every keyboard key category triggers audio.
2. OS key-repeat events while holding down keys are suppressed.
3. Rapid bursts of keystrokes do not block or freeze the UI.
4. Polyphonic overlapping sounds play concurrently across channels.
5. Volume adjustments and mute take effect immediately.
6. Pitch variation generation adheres to configured parameters without clipping.
7. Missing and corrupted audio files trigger actionable exceptions.
8. Corrupted or missing configuration safely self-heals with default values.
9. Window close minimizes to tray when enabled.
10. Application exit terminates background threads and cleans up mixer resources.

---

## License

MIT License. Designed with safety, privacy, and low-latency audio performance.

