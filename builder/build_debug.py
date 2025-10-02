#!/usr/bin/env python3
"""
Debug build script for Navigaze Gaze Tester executable
Creates a version with console output for debugging
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_debug_executable():
    """Build the executable with console output for debugging"""
    print("🔨 Building debug executable...")
    
    # PyInstaller command with console output
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Single executable file
        "--console",  # Show console window for debugging
        "--name", "NavigazeGazeTester_Debug",
        "--add-data", f"gaze_detector_interface.py{':' if os.name != 'nt' else ';'}.",
        "--add-data", f"real_gaze_detector.py{':' if os.name != 'nt' else ';'}.",
        "--add-data", f"simulated_gaze_detector.py{':' if os.name != 'nt' else ';'}.",
        "--add-data", f"google_drive_uploader.py{':' if os.name != 'nt' else ';'}.",
        "--add-data", f"config.py{':' if os.name != 'nt' else ';'}.",
        "--add-data", f"eye_tracking{':' if os.name != 'nt' else ';'}eye_tracking",
        "--add-data", f"input_processing{':' if os.name != 'nt' else ';'}input_processing", 
        "--add-data", f"user_interface{':' if os.name != 'nt' else ';'}user_interface",
        "--hidden-import", "cv2",
        "--hidden-import", "mediapipe",
        "--hidden-import", "numpy",
        "--hidden-import", "pyttsx3",
        "--hidden-import", "googleapiclient",
        "--hidden-import", "google.auth.transport.requests",
        "--hidden-import", "google_auth_oauthlib.flow",
        "comprehensive_gaze_tester_real.py"
    ]
    
    try:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True)
        print("✅ Debug executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False

def create_test_script():
    """Create a simple test script to check imports"""
    test_script = '''#!/usr/bin/env python3
"""
Test script to check if all imports work
"""

print("🧪 Testing imports...")

try:
    print("Testing OpenCV...")
    import cv2
    print("✅ OpenCV imported successfully")
except Exception as e:
    print(f"❌ OpenCV import failed: {e}")

try:
    print("Testing MediaPipe...")
    import mediapipe as mp
    print("✅ MediaPipe imported successfully")
except Exception as e:
    print(f"❌ MediaPipe import failed: {e}")

try:
    print("Testing NumPy...")
    import numpy as np
    print("✅ NumPy imported successfully")
except Exception as e:
    print(f"❌ NumPy import failed: {e}")

try:
    print("Testing Tkinter...")
    import tkinter as tk
    print("✅ Tkinter imported successfully")
except Exception as e:
    print(f"❌ Tkinter import failed: {e}")

try:
    print("Testing pyttsx3...")
    import pyttsx3
    print("✅ pyttsx3 imported successfully")
except Exception as e:
    print(f"❌ pyttsx3 import failed: {e}")

try:
    print("Testing Google APIs...")
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    print("✅ Google APIs imported successfully")
except Exception as e:
    print(f"❌ Google APIs import failed: {e}")

try:
    print("Testing custom modules...")
    from gaze_detector_interface import GazeDetectorInterface
    from real_gaze_detector import RealGazeDetector
    from simulated_gaze_detector import SimulatedGazeDetector
    print("✅ Custom modules imported successfully")
except Exception as e:
    print(f"❌ Custom modules import failed: {e}")

print("\\n🎯 All import tests completed!")
input("Press Enter to exit...")
'''
    
    with open('test_imports.py', 'w') as f:
        f.write(test_script)
    
    print("✅ Test script created: test_imports.py")

def main():
    print("🚀 Navigaze Gaze Tester - Debug Builder")
    print("=" * 45)
    
    # Create test script
    create_test_script()
    
    # Build debug executable
    if not build_debug_executable():
        return False
    
    print("\\n🎉 Debug build completed!")
    print("\\n📁 Files created:")
    print("- NavigazeGazeTester_Debug (executable with console)")
    print("- test_imports.py (test script)")
    print("\\n📋 Next steps:")
    print("1. Run: python test_imports.py (to test imports)")
    print("2. Run: ./NavigazeGazeTester_Debug (to see error messages)")
    print("3. Check console output for crash details")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        input("Press Enter to exit...")
        sys.exit(1)
