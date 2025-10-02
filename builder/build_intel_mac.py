#!/usr/bin/env python3
"""
Build script for Intel Mac (x86_64) compatibility
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

def build_intel_executable():
    """Build executable for Intel Mac architecture"""
    print("[INFO] Building Intel Mac executable...")
    
    # PyInstaller command for Intel Mac
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console", 
        "--name", "NavigazeGazeTester_Intel",
        "--add-data", "../gaze_reporting/gaze_detector_interface.py:.",
        "--add-data", "../gaze_reporting/real_gaze_detector.py:.",
        "--add-data", "../gaze_reporting/simulated_gaze_detector.py:.",
        "--add-data", "../gaze_reporting/google_drive_uploader.py:.",
        "--add-data", "../gaze_reporting/config.py:.",
        "--add-data", "../gaze_reporting/eye_tracking:eye_tracking",
        "--add-data", "../gaze_reporting/comprehensive_gaze_tester_refactored.py:.",
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
        "../gaze_reporting/gaze_reporter.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("[OK] Intel Mac executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Build failed: {e}")
        return False

def create_intel_distribution():
    """Create distribution package for Intel Mac"""
    print("[INFO] Creating Intel Mac distribution...")
    
    dist_dir = "NavigazeGazeTester_Intel_Distribution"
    
    # Remove existing distribution
    if os.path.exists(dist_dir):
        import shutil
        shutil.rmtree(dist_dir)
    
    os.makedirs(dist_dir, exist_ok=True)
    
    # Copy executable
    if os.path.exists("dist/NavigazeGazeTester_Intel"):
        import shutil
        shutil.copy2("dist/NavigazeGazeTester_Intel", f"{dist_dir}/NavigazeGazeTester_Intel")
        print(f"[OK] Copied executable to {dist_dir}/")
    else:
        print("[ERROR] Executable not found in dist/")
        return False
    
    # Copy additional files
    files_to_copy = [
        "../gaze_reporting/google_drive_uploader.py",
        "../gaze_reporting/README.md"
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            import shutil
            filename = os.path.basename(file)
            shutil.copy2(file, f"{dist_dir}/{filename}")
            print(f"[OK] Copied {filename}")
    
    # Create README for Intel Mac
    readme_content = """# Navigaze Gaze Tester - Intel Mac Version

## Quick Start
1. Double-click NavigazeGazeTester_Intel to run
2. Follow the on-screen instructions
3. Check console output for any errors

## Google Drive Upload (Optional)
1. Get credentials.json from Google Cloud Console
2. Place it in the same folder as the executable
3. Run the application - it will authenticate once

## System Requirements
- macOS 10.15+ (Intel Mac)
- Webcam
- 4GB RAM minimum
- Good lighting for face detection

## Architecture
This version is built for Intel Mac (x86_64) architecture.
If you have an Apple Silicon Mac, use the arm64 version instead.

## Debug Information
This is the debug version with console output.
If you see errors, check the console window for details.
"""
    
    with open(f"{dist_dir}/README.txt", "w") as f:
        f.write(readme_content)
    
    # Create run script
    run_script = """#!/bin/bash
echo "Starting Navigaze Gaze Tester (Intel Mac)..."
./NavigazeGazeTester_Intel
"""
    
    with open(f"{dist_dir}/Run_Intel.sh", "w") as f:
        f.write(run_script)
    
    # Make run script executable
    os.chmod(f"{dist_dir}/Run_Intel.sh", 0o755)
    
    print(f"[OK] Intel Mac distribution created: {dist_dir}/")
    return True

def main():
    print("Navigaze Gaze Tester - Intel Mac Builder")
    print("=" * 50)
    
    # Check current architecture
    current_arch = platform.machine()
    print(f"[INFO] Current architecture: {current_arch}")
    
    if current_arch == "arm64":
        print("[WARN] You're on Apple Silicon - this will build for Intel Mac")
        print("   The executable will work on Intel Macs but may be slower on your Mac")
    elif current_arch == "x86_64":
        print("[OK] You're on Intel Mac - this will build natively")
    else:
        print(f"[WARN] Unknown architecture: {current_arch}")
    
    print()
    
    # Install PyInstaller
    if not install_pyinstaller():
        return False
    
    # Build executable
    if not build_intel_executable():
        return False
    
    # Create distribution
    if not create_intel_distribution():
        return False
    
    print("\n[SUCCESS] Intel Mac build completed successfully!")
    print("\n[INFO] Your Intel Mac executable is in: NavigazeGazeTester_Intel_Distribution/")
    print("\n[INFO] To distribute:")
    print("1. Zip the NavigazeGazeTester_Intel_Distribution folder")
    print("2. Send the zip file to Intel Mac users")
    print("3. Users extract and run NavigazeGazeTester_Intel")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
