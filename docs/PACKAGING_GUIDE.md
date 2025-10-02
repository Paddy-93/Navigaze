# Navigaze Gaze Tester - Packaging Guide

This guide explains how to package the Navigaze Gaze Tester into a standalone executable for distribution.

## Quick Build (Windows)

### Option 1: Using Batch File (Easiest)
```bash
# Just double-click or run:
build.bat
```

### Option 2: Using Python Script
```bash
python build_simple.py
```

## Manual Build Process

### 1. Install PyInstaller
```bash
pip install pyinstaller
```

### 2. Install All Dependencies
```bash
pip install opencv-python mediapipe numpy pyttsx3 google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 3. Build the Executable
```bash
python -m PyInstaller --onefile --windowed --name NavigazeGazeTester --add-data "gaze_detector_interface.py;." --add-data "real_gaze_detector.py;." --add-data "simulated_gaze_detector.py;." --add-data "google_drive_uploader.py;." --add-data "config.py;." --add-data "core;core" --add-data "detection;detection" --add-data "input;input" --add-data "ui;ui" --add-data "utils;utils" --hidden-import cv2 --hidden-import mediapipe --hidden-import numpy --hidden-import pyttsx3 --hidden-import googleapiclient --hidden-import "google.auth.transport.requests" --hidden-import "google_auth_oauthlib.flow" comprehensive_gaze_tester_real.py
```

## Distribution Package Structure

After building, you'll have:
```
NavigazeGazeTester_Distribution/
├── NavigazeGazeTester.exe          # Main executable
├── google_drive_uploader.py        # Upload script (for reference)
├── README_GOOGLE_DRIVE.md          # Google Drive setup guide
├── README.txt                      # User instructions
└── Run_Navigaze.bat                # Easy launcher
```

## What Gets Included

### [OK] Included in Executable:
- All Python code and dependencies
- OpenCV, MediaPipe, NumPy
- Tkinter GUI framework
- Text-to-speech engine
- Google Drive API libraries
- All custom modules (core, detection, input, ui, utils)

### ❌ Not Included (User Must Provide):
- `credentials.json` (Google Drive API credentials)
- `token.json` (auto-generated after first run)

## File Size

- **Executable**: ~200-300 MB (includes all dependencies)
- **Distribution folder**: ~300-400 MB total
- **Compressed zip**: ~100-150 MB

## System Requirements for Users

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB free space
- **Hardware**: Webcam, microphone (for TTS)
- **Network**: Internet connection (for Google Drive upload)

## Distribution Methods

### 1. Direct Distribution
- Zip the `NavigazeGazeTester_Distribution` folder
- Send via email, cloud storage, or USB drive
- Users extract and run `NavigazeGazeTester.exe`

### 2. Installer Creation (Advanced)
Use tools like:
- **NSIS** (Nullsoft Scriptable Install System)
- **Inno Setup**
- **Advanced Installer**

### 3. Cloud Distribution
- Upload to Google Drive, Dropbox, OneDrive
- Share download link
- Include setup instructions

## Google Drive Setup for Users

### For Users Who Want Upload:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google Drive API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download `credentials.json`
6. Place it in the same folder as `NavigazeGazeTester.exe`
7. Run the application - it will open browser for authentication

### For Users Who Don't Need Upload:
- Just run `NavigazeGazeTester.exe`
- Results will be saved locally
- No Google Drive setup needed

## Testing the Executable

### Before Distribution:
1. Test on a clean Windows machine (without Python installed)
2. Verify camera access works
3. Test Google Drive upload (if credentials provided)
4. Check all test steps complete properly
5. Verify video recording works
6. Test auto-exit functionality

### Common Issues:
- **Camera not detected**: Check permissions, close other camera apps
- **Google Drive upload fails**: Verify credentials.json is present
- **Slow performance**: Close other applications, check lighting
- **TTS not working**: Check audio drivers and permissions

## Troubleshooting Build Issues

### PyInstaller Errors:
```bash
# If missing modules:
--hidden-import MODULE_NAME

# If data files missing:
--add-data "file.py;."

# If too large:
--exclude-module MODULE_NAME
```

### Common Build Problems:
1. **Missing dependencies**: Install all required packages
2. **Path issues**: Use forward slashes in paths
3. **Large file size**: Use `--exclude-module` for unused modules
4. **Import errors**: Add `--hidden-import` for dynamic imports

## Advanced Customization

### Custom Icon:
```bash
--icon=icon.ico
```

### Console Window (for debugging):
```bash
--console  # Instead of --windowed
```

### One Directory (instead of one file):
```bash
--onedir  # Instead of --onefile
```

## Security Considerations

- The executable contains all source code
- Google Drive credentials should be provided separately
- Consider code signing for distribution
- Warn users about antivirus false positives

## Version Control

- Keep track of executable versions
- Include version number in filename
- Document changes between versions
- Test each version before distribution

## Support and Documentation

- Include comprehensive README
- Provide troubleshooting guide
- Include contact information
- Document system requirements clearly
