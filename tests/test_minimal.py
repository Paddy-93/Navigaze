#!/usr/bin/env python3
"""
Minimal test to isolate the crash issue
"""

import sys
import traceback

def test_basic_imports():
    """Test basic imports one by one"""
    print("🧪 Testing basic imports...")
    
    try:
        print("1. Testing sys...")
        import sys
        print("✅ sys imported")
    except Exception as e:
        print(f"❌ sys failed: {e}")
        return False
    
    try:
        print("2. Testing tkinter...")
        import tkinter as tk
        print("✅ tkinter imported")
    except Exception as e:
        print(f"❌ tkinter failed: {e}")
        return False
    
    try:
        print("3. Testing cv2...")
        import cv2
        print("✅ cv2 imported")
    except Exception as e:
        print(f"❌ cv2 failed: {e}")
        return False
    
    try:
        print("4. Testing mediapipe...")
        import mediapipe as mp
        print("✅ mediapipe imported")
    except Exception as e:
        print(f"❌ mediapipe failed: {e}")
        return False
    
    try:
        print("5. Testing numpy...")
        import numpy as np
        print("✅ numpy imported")
    except Exception as e:
        print(f"❌ numpy failed: {e}")
        return False
    
    return True

def test_mediapipe_initialization():
    """Test MediaPipe initialization"""
    print("\n🔧 Testing MediaPipe initialization...")
    
    try:
        import mediapipe as mp
        print("Creating face mesh...")
        face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        print("✅ Face mesh created successfully")
        
        print("Closing face mesh...")
        face_mesh.close()
        print("✅ Face mesh closed successfully")
        return True
        
    except Exception as e:
        print(f"❌ MediaPipe initialization failed: {e}")
        traceback.print_exc()
        return False

def test_camera_access():
    """Test camera access"""
    print("\n📷 Testing camera access...")
    
    try:
        import cv2
        print("Opening camera...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Camera not opened")
            return False
        
        print("✅ Camera opened successfully")
        
        print("Reading frame...")
        ret, frame = cap.read()
        if not ret:
            print("❌ Could not read frame")
            cap.release()
            return False
        
        print(f"✅ Frame read successfully: {frame.shape}")
        
        print("Releasing camera...")
        cap.release()
        print("✅ Camera released successfully")
        return True
        
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        traceback.print_exc()
        return False

def test_tkinter_gui():
    """Test basic Tkinter GUI"""
    print("\n🖥️ Testing Tkinter GUI...")
    
    try:
        import tkinter as tk
        print("Creating root window...")
        root = tk.Tk()
        root.title("Test Window")
        root.geometry("300x200")
        
        print("Creating label...")
        label = tk.Label(root, text="Test Label")
        label.pack(pady=20)
        
        print("Updating GUI...")
        root.update()
        
        print("✅ GUI created successfully")
        
        print("Destroying GUI...")
        root.destroy()
        print("✅ GUI destroyed successfully")
        return True
        
    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        traceback.print_exc()
        return False

def main():
    print("🚀 Navigaze Minimal Test")
    print("=" * 30)
    
    # Test basic imports
    if not test_basic_imports():
        print("\n❌ Basic imports failed!")
        return False
    
    # Test MediaPipe initialization
    if not test_mediapipe_initialization():
        print("\n❌ MediaPipe initialization failed!")
        return False
    
    # Test camera access
    if not test_camera_access():
        print("\n❌ Camera access failed!")
        return False
    
    # Test Tkinter GUI
    if not test_tkinter_gui():
        print("\n❌ GUI test failed!")
        return False
    
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    input("\nPress Enter to exit...")
