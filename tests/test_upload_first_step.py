#!/usr/bin/env python3
"""
Test script that runs only the first step and tests auto-upload
"""

import sys
import os
import time
import tkinter as tk
from comprehensive_gaze_tester_refactored import ComprehensiveGazeTester
from simulated_gaze_detector import SimulatedGazeDetector
from google_drive_uploader import GoogleDriveUploader

def test_upload_first_step():
    """Test the first step only and then test upload"""
    print("🧪 Testing first step + auto-upload...")
    
    # Create Tkinter root window
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    # Create simulated gaze detector
    gaze_detector = SimulatedGazeDetector()
    
    # Create tester
    tester = ComprehensiveGazeTester(root, gaze_detector)
    
    # Modify test steps to only run the first step
    tester.test_steps = [
        {
            'name': 'Initial Calibration',
            'type': 'calibration',
            'instruction': 'Look at the red dot and keep your head still. Wait for the beep to begin.'
        }
    ]
    
    # Set up UI (minimal for testing)
    tester.setup_ui()
    
    # Start the test
    print("🚀 Starting test with first step only...")
    tester.start_test()
    
    # Wait for test to complete
    while tester.test_running:
        time.sleep(0.1)
    
    print("✅ Test completed!")
    
    # Test upload if session directory exists
    if tester.session_dir and os.path.exists(tester.session_dir):
        print(f"📁 Session directory: {tester.session_dir}")
        
        # Test Google Drive upload
        print("☁️ Testing Google Drive upload...")
        uploader = GoogleDriveUploader()
        
        if uploader.upload_session(tester.session_dir):
            print("✅ Upload successful!")
        else:
            print("❌ Upload failed - check credentials.json")
    else:
        print("❌ No session directory found")
    
    # Cleanup
    if hasattr(tester, 'gaze_detector'):
        tester.gaze_detector.release()

if __name__ == "__main__":
    test_upload_first_step()
