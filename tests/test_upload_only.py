#!/usr/bin/env python3
"""
Test script that only tests Google Drive upload functionality
"""

import os
import tempfile
from google_drive_uploader import GoogleDriveUploader

def test_upload_only():
    """Test Google Drive upload with a dummy session folder"""
    print("🧪 Testing Google Drive upload only...")
    
    # Create a dummy session folder for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        session_dir = os.path.join(temp_dir, "test_session_20250130_120000")
        os.makedirs(session_dir, exist_ok=True)
        
        # Create some dummy files
        with open(os.path.join(session_dir, "test_file.txt"), "w") as f:
            f.write("This is a test file for upload verification")
        
        with open(os.path.join(session_dir, "baseline_data.json"), "w") as f:
            f.write('{"test": "data"}')
        
        print(f"📁 Created test session directory: {session_dir}")
        
        # Test Google Drive upload
        print("☁️ Testing Google Drive upload...")
        uploader = GoogleDriveUploader()
        
        if uploader.upload_session(session_dir):
            print("✅ Upload test successful!")
            return True
        else:
            print("❌ Upload test failed - check credentials.json")
            return False

if __name__ == "__main__":
    test_upload_only()
