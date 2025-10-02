#!/usr/bin/env python3
"""
Debug build with console output to see crash details
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_debug_console():
    """Build with console output to see errors"""
    print("🔨 Building debug console version...")
    
    # PyInstaller command with console output
    separator = ";" if os.name == "nt" else ":"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Single executable file
        "--console",  # Show console window for debugging
        "--name", "NavigazeGazeTester_Debug",
        "--add-data", f"gaze_detector_interface.py{separator}.",
        "--add-data", f"real_gaze_detector.py{separator}.",
        "--add-data", f"simulated_gaze_detector.py{separator}.",
        "--add-data", f"google_drive_uploader.py{separator}.",
        "--add-data", f"config.py{separator}.",
        "--add-data", f"eye_tracking{separator}eye_tracking",
        "--add-data", f"input_processing{separator}input_processing", 
        "--add-data", f"user_interface{separator}user_interface",
        "--hidden-import", "cv2",
        "--hidden-import", "mediapipe",
        "--hidden-import", "mediapipe.python.solutions.face_mesh",
        "--hidden-import", "mediapipe.python.solutions.face_detection",
        "--hidden-import", "numpy",
        "--hidden-import", "pyttsx3",
        "--hidden-import", "googleapiclient",
        "--hidden-import", "google.auth.transport.requests",
        "--hidden-import", "google_auth_oauthlib.flow",
        "--collect-data", "mediapipe",
        "--debug", "all",  # Enable all debug output
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

def create_simple_test():
    """Create a simple test that just imports and shows errors"""
    test_content = '''#!/usr/bin/env python3
"""
Simple test to debug PyInstaller issues
"""

import sys
import traceback

def main():
    print("🚀 Starting Navigaze Test...")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    try:
        print("\\n1. Testing basic imports...")
        import os
        import time
        import json
        print("✅ Basic imports OK")
        
        print("\\n2. Testing OpenCV...")
        import cv2
        print(f"✅ OpenCV version: {cv2.__version__}")
        
        print("\\n3. Testing MediaPipe...")
        import mediapipe as mp
        print(f"✅ MediaPipe version: {mp.__version__}")
        
        print("\\n4. Testing NumPy...")
        import numpy as np
        print(f"✅ NumPy version: {np.__version__}")
        
        print("\\n5. Testing Tkinter...")
        import tkinter as tk
        print("✅ Tkinter OK")
        
        print("\\n6. Testing custom modules...")
        from gaze_detector_interface import GazeDetectorInterface
        print("✅ GazeDetectorInterface imported")
        
        from real_gaze_detector import RealGazeDetector
        print("✅ RealGazeDetector imported")
        
        from simulated_gaze_detector import SimulatedGazeDetector
        print("✅ SimulatedGazeDetector imported")
        
        print("\\n7. Testing comprehensive tester import...")
        from comprehensive_gaze_tester_refactored import ComprehensiveGazeTester
        print("✅ ComprehensiveGazeTester imported")
        
        print("\\n8. Testing main script import...")
        import comprehensive_gaze_tester_real
        print("✅ comprehensive_gaze_tester_real imported")
        
        print("\\n🎉 All imports successful!")
        print("\\nThe issue might be in the main() function or GUI initialization.")
        
    except Exception as e:
        print(f"\\n❌ Error during import: {e}")
        print("\\nFull traceback:")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\\n❌ Test failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\\n💥 Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    input("\\nPress Enter to exit...")
'''
    
    with open('simple_debug_test.py', 'w') as f:
        f.write(test_content)
    
    print("✅ Simple debug test created: simple_debug_test.py")

def main():
    print("🚀 Navigaze Debug Console Builder")
    print("=" * 40)
    
    # Create simple test
    create_simple_test()
    
    # Build debug executable
    if not build_debug_console():
        return False
    
    print("\\n🎉 Debug build completed!")
    print("\\n📁 Files created:")
    print("- NavigazeGazeTester_Debug (executable with console)")
    print("- simple_debug_test.py (simple test)")
    print("\\n📋 Next steps:")
    print("1. Run: python simple_debug_test.py (test imports)")
    print("2. Run: ./NavigazeGazeTester_Debug (see detailed error messages)")
    print("3. Check console output for crash details")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        input("Press Enter to exit...")
        sys.exit(1)
