#!/usr/bin/env python3
"""
Build script for Windows executable
"""

import subprocess
import sys
import os
import platform

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("[OK] PyInstaller already installed")
        return True
    except ImportError:
        print("[INFO] Installing PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("[OK] PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to install PyInstaller: {e}")
            return False

def build_windows_executable():
    """Build executable for Windows"""
    print("[INFO] Building Windows executable...")
    
    # PyInstaller command for Windows
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console", 
        "--name", "NavigazeGazeTester_Windows",
        "--add-data", "gaze_reporting/gaze_detector_interface.py:.",
        "--add-data", "gaze_reporting/real_gaze_detector.py:.",
        "--add-data", "gaze_reporting/simulated_gaze_detector.py:.",
        "--add-data", "gaze_reporting/google_drive_uploader.py:.",
        "--add-data", "gaze_reporting/config.py:.",
        "--add-data", "gaze_reporting/eye_tracking:eye_tracking",
        "--add-data", "gaze_reporting/comprehensive_gaze_tester_refactored.py:.",
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
        "--debug", "all",
        "gaze_reporting/gaze_reporter.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("[OK] Windows executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Build failed: {e}")
        return False

def create_windows_distribution():
    """Create distribution package for Windows"""
    print("[INFO] Creating Windows distribution...")
    
    dist_dir = "builder/NavigazeGazeTester_Windows_Distribution"
    
    # Remove existing distribution
    if os.path.exists(dist_dir):
        import shutil
        shutil.rmtree(dist_dir)
    
    os.makedirs(dist_dir, exist_ok=True)
    
    # Copy executable (check both .exe and no extension)
    exe_path = None
    if os.path.exists("dist/NavigazeGazeTester_Windows.exe"):
        exe_path = "dist/NavigazeGazeTester_Windows.exe"
    elif os.path.exists("dist/NavigazeGazeTester_Windows"):
        exe_path = "dist/NavigazeGazeTester_Windows"
    
    if exe_path:
        import shutil
        shutil.copy2(exe_path, f"{dist_dir}/NavigazeGazeTester_Windows")
        print(f"[OK] Copied executable to {dist_dir}/")
    else:
        print("[ERROR] Executable not found in dist/")
        return False
    
    # Copy additional files
    files_to_copy = [
        "gaze_reporting/README.md"
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            import shutil
            filename = os.path.basename(file)
            shutil.copy2(file, f"{dist_dir}/{filename}")
            print(f"[OK] Copied {filename}")
    
    # Create README for Windows
    readme_content = """# Navigaze Gaze Tester - Windows Version

## Quick Start
1. Double-click NavigazeGazeTester_Windows.exe to run
2. Follow the on-screen instructions
3. Check console output for any errors

## Google Drive Upload (Optional)
1. Get credentials.json from Google Cloud Console
2. Place it in the same folder as the executable
3. Run the application - it will authenticate once

## System Requirements
- Windows 10/11 (64-bit)
- Webcam
- 4GB RAM minimum
- Good lighting for face detection

## Debug Information
This is the debug version with console output.
If you see errors, check the console window for details.

## Troubleshooting
- If camera is not detected, close other camera applications
- Make sure you have good lighting for face detection
- Check that your webcam is not being used by other programs
"""
    
    with open(f"{dist_dir}/README.txt", "w") as f:
        f.write(readme_content)
    
    # Create batch file to run
    batch_content = """@echo off
echo Starting Navigaze Gaze Tester (Windows)...
NavigazeGazeTester_Windows.exe
pause
"""
    
    with open(f"{dist_dir}/Run_Windows.bat", "w") as f:
        f.write(batch_content)
    
    print(f"[OK] Windows distribution created: {dist_dir}/")
    return True

def main():
    print("Navigaze Gaze Tester - Windows Builder")
    print("=" * 50)
    
    # Check current platform
    current_platform = platform.system()
    print(f"[INFO] Current platform: {current_platform}")
    
    if current_platform != "Windows":
        print("[WARN] You're not on Windows - this will build for Windows")
        print("   The executable will work on Windows but may not run on your current system")
    else:
        print("[OK] You're on Windows - this will build natively")
    
    print()
    
    # Install PyInstaller
    if not install_pyinstaller():
        return False
    
    # Build executable
    if not build_windows_executable():
        return False
    
    # Create distribution
    if not create_windows_distribution():
        return False
    
    print("\n[SUCCESS] Windows build completed successfully!")
    print("\n[INFO] Your Windows executable is in: builder/NavigazeGazeTester_Windows_Distribution/")
    print("\n[INFO] To distribute:")
    print("1. Zip the builder/NavigazeGazeTester_Windows_Distribution folder")
    print("2. Send the zip file to Windows users")
    print("3. Users extract and run NavigazeGazeTester_Windows.exe")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
