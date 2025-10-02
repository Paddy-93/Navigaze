# Navigaze 🚀

**Professional Gaze-Controlled Navigation System**

Navigaze enables hands-free computer navigation and text input using only eye movements. Navigate through applications, input text via Morse code, and control your computer with precision gaze detection.

## ✨ Features

- **🎯 Gaze Navigation**: Tab through UI elements, scroll pages using UP/DOWN eye movements
- **📝 Morse Text Input**: Type text using gaze-based Morse code patterns
- **🔄 Mode Switching**: Seamless switching between navigation and text modes
- **📊 Real-time Status**: Live status display via system tray (Windows)
- **⚡ Sequence Commands**: Execute commands via gaze patterns
- **🎛️ Calibration System**: Automatic baseline calibration for accurate detection

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Webcam
- Windows/macOS/Linux

### Installation

```bash
# Clone or download the repository
cd Navigaze

# Install dependencies
pip install -r requirements.txt

# Run Navigaze
python main.py
```

### First Run

1. **Calibration**: Look at the red dot for 5 seconds when prompted
2. **Navigation**: Use UP/DOWN gazes to navigate through interface elements
3. **Text Input**: Focus on text fields for 3 seconds to enter TEXT mode
4. **Commands**: Use gaze sequences for special actions

## 🎮 Usage

### Navigation Modes

- **TAB Mode** (Default): UP = Tab forward, DOWN = Tab backward
- **SCROLL Mode**: UP = Scroll up, DOWN = Scroll down
- **TEXT Mode**: Morse code input via gaze patterns

### Gaze Sequences

Execute these patterns by looking UP/DOWN in sequence:

- `UP-DOWN-UP-DOWN`: Switch between TAB/SCROLL modes
- `DOWN-UP-DOWN-UP`: Send Enter key
- `UP-UP-DOWN-DOWN`: Send Escape key
- `DOWN-DOWN-UP-UP`: Send Windows/Cmd key

### Morse Code Input

When in TEXT mode:

- **Quick UP**: Dot (.)
- **Quick DOWN**: Dash (-)
- **1s UP hold**: Space
- **1s DOWN hold**: Backspace
- **1s neutral hold**: Complete letter
- **3s neutral hold**: Submit text and exit TEXT mode

### Text Mode Activation

1. **Focus on any text field** (click or tab to it)
2. **Hold neutral gaze for 3 seconds** → TEXT mode activates automatically
3. **Use morse code** to input text
4. **Hold neutral for 3 seconds** to exit back to navigation mode

## 🏗️ Project Structure

The project is organized by **functionality**, making it easy to understand what each part does:

```
Navigaze/
├── main.py                    # 🚀 Main application entry point
├── config.py                  # ⚙️ All configuration settings
├── requirements.txt           # 📦 Python dependencies
├── eye_tracking/              # 👁️ Everything related to detecting eye movements
│   ├── calibration_popup.py   #   📍 Calibrates the eye tracking system
│   ├── face_landmarks.py      #   🎯 Processes face landmarks from camera
│   └── gaze_detector.py       #   🔍 Detects UP/DOWN eye movements
├── input_processing/          # ⌨️ Converts eye movements into actions
│   ├── sequence_manager.py    #   🔄 Recognizes gaze patterns (UP-DOWN-UP-DOWN)
│   ├── morse_handler.py       #   📝 Converts gaze to morse code text
│   ├── morse_dict.py          #   📚 Morse code dictionary
│   └── command_executor.py    #   ⚡ Executes keyboard commands (Tab, Enter, etc.)
└── user_interface/            # 🖥️ Shows status and detects text fields
    ├── appbar.py              #   📊 Shows status bar (Windows only)
    ├── advanced_uia_detector.py #   🔍 Detects text fields automatically
    └── visualization.py       #   🎨 Drawing and visualization functions
```

### What Each Directory Does

- **👁️ eye_tracking/**: Takes camera input → detects where you're looking
- **⌨️ input_processing/**: Takes eye movements → converts to keyboard actions
- **🖥️ user_interface/**: Shows you what's happening + detects text fields

## ⚙️ Configuration

Edit `config.py` to customize:

- **Gaze detection thresholds**: Sensitivity for UP/DOWN detection
- **Timing parameters**: Hold times, timeouts, cooldowns
- **Morse code mappings**: Custom morse patterns
- **Display settings**: Colors, sizes, positions

### Key Configuration Options

```python
# Gaze Detection
GAZE_CONFIG = {
    'threshold_up': 0.012,     # UP gaze sensitivity
    'threshold_down': 0.006,   # DOWN gaze sensitivity
    'cooldown_ms': 200,        # Time between detections
}

# Morse Code Input
MORSE_CONFIG = {
    'up_hold_time': 1000,      # 1 second for space
    'neutral_hold_time': 1000, # 1 second for letter completion
    'down_hold_time': 1000,    # 1 second for backspace
    'neutral_timeout': 3000,   # 3 seconds to exit text mode
}
```

## 🛠️ Command Line Options

```bash
python main.py --help           # Show all options
python main.py --camera 1       # Use camera 1 instead of default (0)
python main.py --version        # Show version information
```

## 🔧 Troubleshooting

### Common Issues

**Gaze not detected:**

- Ensure good lighting on your face
- Position camera at eye level
- Restart calibration if needed

**Text fields not detected:**

- Make sure to click/focus the text field first
- Windows: Requires `pywin32` and `uiautomation` packages
- macOS/Linux: Limited text field detection

**AppBar not visible (Windows):**

- Check if `pywin32` is installed
- Run as administrator if needed
- AppBar appears at top of screen

**Performance issues:**

- Close other camera applications
- Ensure good camera quality
- Reduce other running applications

### Debug Mode

Add debug prints by modifying the configuration in `config.py`.

## 📋 System Requirements

- **Camera**: Any webcam for face/eye tracking
- **Python**: 3.8 or higher
- **Memory**: 2GB RAM minimum
- **OS**: Windows 10+, macOS 10.14+, or Linux

### Dependencies

- `opencv-python` - Computer vision
- `mediapipe` - Face and eye detection
- `numpy` - Numerical processing
- `pynput` - Keyboard/mouse control
- `pywin32` - Windows integration (Windows only)
- `uiautomation` - Text field detection (Windows only)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

Built with:

- [MediaPipe](https://mediapipe.dev/) - Face and eye detection
- [OpenCV](https://opencv.org/) - Computer vision processing
- [pynput](https://pypi.org/project/pynput/) - Cross-platform input control

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the configuration options
3. Ensure all dependencies are installed correctly
4. Test with different lighting conditions

---

**Navigaze** - Navigate with your gaze 👁️

_Empowering hands-free computer interaction through advanced eye tracking technology._
