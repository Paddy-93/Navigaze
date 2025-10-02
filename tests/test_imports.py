#!/usr/bin/env python3
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

print("\n🎯 All import tests completed!")
input("Press Enter to exit...")
