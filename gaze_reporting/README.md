# Gaze Reporter - Local Executable Version

## Overview

A comprehensive gaze testing system designed for locked-in patients to help them navigate tablets using eye gaze tracking.

## How It Works

- **Real-time gaze detection** using webcam and MediaPipe face landmarks
- **Comprehensive test suite** with calibration, quick gazes, long holds, and sequence patterns
- **Video recording** of each test step with analysis overlays
- **Detailed reporting** with JSON logs and step summaries
- **Google Drive upload** for remote data collection

## Files

### Main Executable

- `gaze_reporter.py` - Main entry point for real gaze testing

### Core Components

- `comprehensive_gaze_tester_refactored.py` - Main test logic and GUI
- `real_gaze_detector.py` - Real camera-based gaze detection
- `simulated_gaze_detector.py` - Simulation for testing without camera
- `gaze_detector_interface.py` - Abstract interface for gaze detectors

### Supporting Files

- `google_drive_uploader.py` - Uploads test results to Google Drive
- `config.py` - Configuration settings
- `eye_tracking/` - Face landmarks and gaze detection algorithms

## Usage

### Run Locally

```bash
python gaze_reporter.py
```

### Build Executable

```bash
# Windows
cd ../builder
build_windows.bat

# Mac Intel
cd ../builder
python build_intel_mac.py

# Mac Universal (Intel + Apple Silicon)
cd ../builder
python build_universal_mac.py
```

## Test Steps

1. **Initial Calibration** - Establish gaze baseline
2. **UP-DOWN-UP-DOWN Sequence** - Pattern recognition test
3. **Quick UP Gazes** - 5 rapid upward gazes
4. **Calibration** - Re-establish baseline
5. **Quick DOWN Gazes** - 5 rapid downward gazes
6. **Long UP Holds** - 3 sustained upward gazes (5 seconds each)
7. **Long DOWN Holds** - 3 sustained downward gazes (5 seconds each)
8. **DOWN-UP-DOWN-UP Sequence** - Alternative pattern test
9. **DOWN-DOWN-UP-UP Sequence** - Complex pattern test

## Results

- **Videos**: Raw camera feed and analysis overlays for each step
- **Logs**: Detailed JSON logs with timestamps and gaze data
- **Uploads**: Automatic Google Drive upload (optional)
- **Location**: `results/` folder with timestamped sessions

## Requirements

- Python 3.8+
- Webcam access
- MediaPipe
- OpenCV
- tkinter (usually included with Python)

## For Remote Users

Users can download the executable and run it locally without needing Python installed.
