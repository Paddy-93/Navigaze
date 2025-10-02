#!/usr/bin/env python3
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
        print("\n1. Testing basic imports...")
        import os
        import time
        import json
        print("✅ Basic imports OK")
        
        print("\n2. Testing OpenCV...")
        import cv2
        print(f"✅ OpenCV version: {cv2.__version__}")
        
        print("\n3. Testing MediaPipe...")
        import mediapipe as mp
        print(f"✅ MediaPipe version: {mp.__version__}")
        
        print("\n4. Testing NumPy...")
        import numpy as np
        print(f"✅ NumPy version: {np.__version__}")
        
        print("\n5. Testing Tkinter...")
        import tkinter as tk
        print("✅ Tkinter OK")
        
        print("\n6. Testing custom modules...")
        from gaze_detector_interface import GazeDetectorInterface
        print("✅ GazeDetectorInterface imported")
        
        from real_gaze_detector import RealGazeDetector
        print("✅ RealGazeDetector imported")
        
        from simulated_gaze_detector import SimulatedGazeDetector
        print("✅ SimulatedGazeDetector imported")
        
        print("\n7. Testing comprehensive tester import...")
        from comprehensive_gaze_tester_refactored import ComprehensiveGazeTester
        print("✅ ComprehensiveGazeTester imported")
        
        print("\n8. Testing main script import...")
        import comprehensive_gaze_tester_real
        print("✅ comprehensive_gaze_tester_real imported")
        
        print("\n🎉 All imports successful!")
        print("\nThe issue might be in the main() function or GUI initialization.")
        
    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ Test failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    input("\nPress Enter to exit...")
