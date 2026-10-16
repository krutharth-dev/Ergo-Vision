# Installation

ErgoVision supports **macOS** and **Windows** as local desktop-style applications. All posture inference stays on the user's computer.

## Recommended: GitHub Releases

Version tags automatically produce:

- `ErgoVision-macOS.zip`
- `ErgoVision-Windows.zip`

The release bundles include the built web interface and MediaPipe model files, so end users do **not** need Node.js. Python 3.11 or 3.12 is still required.

### macOS

1. Download `ErgoVision-macOS.zip` from GitHub Releases.
2. Extract it.
3. Double-click `install-mac.command`.
4. Allow camera access when macOS asks.
5. ErgoVision installs its app files under `~/Library/Application Support/ErgoVision` and creates `~/Applications/ErgoVision.app`.

If macOS blocks the script initially, right-click `install-mac.command` and choose **Open**.

### Windows

1. Install Python 3.11 or 3.12 from python.org and enable **Add Python to PATH**.
2. Download `ErgoVision-Windows.zip` from GitHub Releases and extract it.
3. Open PowerShell in the extracted folder.
4. Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1
```

ErgoVision copies itself to `%LOCALAPPDATA%\ErgoVision`, completes setup, creates **Desktop** and **Start Menu** shortcuts, and opens the local dashboard.

Enable **Settings → Privacy & security → Camera → Let desktop apps access your camera** if Windows asks.

## Install from source

A source checkout requires Git and may require Node.js because `frontend/dist` is normally generated locally.

### macOS

```bash
git clone https://github.com/krutharth-dev/Ergo-Vision.git
cd Ergo-Vision
bash scripts/setup_mac.sh
bash scripts/install_mac_app.sh
```

### Windows

```powershell
git clone https://github.com/krutharth-dev/Ergo-Vision.git
cd Ergo-Vision
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\install_windows_shortcut.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run_windows.ps1
```

## Camera lifecycle

The webcam activates only while at least one ErgoVision dashboard is connected. Closing the final dashboard tab/window releases webcam access while the lightweight local backend may remain running.
