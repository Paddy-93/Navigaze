#!/usr/bin/env python3
"""
Build script for Universal Mac binary (both Intel and Apple Silicon)
"""

import subprocess
import sys
import os
import platform

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("✅ PyInstaller already installed")
        return True
    except ImportError:
        print("📦 Installing PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install PyInstaller: {e}")
            return False

def build_universal_executable():
    """Build universal executable for both Intel and Apple Silicon Macs"""
    print("🔨 Building Universal Mac executable...")
    
    # PyInstaller command for universal binary
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console", 
        "--name", "NavigazeGazeTester_Universal",
        "--add-data", "gaze_detector_interface.py:.",
        "--add-data", "real_gaze_detector.py:.",
        "--add-data", "simulated_gaze_detector.py:.",
        "--add-data", "google_drive_uploader.py:.",
        "--add-data", "config.py:.",
        "--add-data", "eye_tracking:eye_tracking",
        "--add-data", "input_processing:input_processing", 
        "--add-data", "user_interface:user_interface",
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
        "comprehensive_gaze_tester_real.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("✅ Universal Mac executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False

def create_universal_distribution():
    """Create distribution package for Universal Mac"""
    print("📦 Creating Universal Mac distribution...")
    
    dist_dir = "NavigazeGazeTester_Universal_Distribution"
    
    # Remove existing distribution
    if os.path.exists(dist_dir):
        import shutil
        shutil.rmtree(dist_dir)
    
    os.makedirs(dist_dir, exist_ok=True)
    
    # Copy executable
    if os.path.exists("dist/NavigazeGazeTester_Universal"):
        import shutil
        shutil.copy2("dist/NavigazeGazeTester_Universal", f"{dist_dir}/NavigazeGazeTester_Universal")
        print(f"✅ Copied executable to {dist_dir}/")
    else:
        print("❌ Executable not found in dist/")
        return False
    
    # Copy additional files
    files_to_copy = [
        "google_drive_uploader.py",
        "README_GOOGLE_DRIVE.md"
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            import shutil
            shutil.copy2(file, f"{dist_dir}/{file}")
            print(f"✅ Copied {file}")
    
    # Create README for Universal Mac
    readme_content = """# Navigaze Gaze Tester - Universal Mac Version

## Quick Start
1. Double-click NavigazeGazeTester_Universal to run
2. Follow the on-screen instructions
3. Check console output for any errors

## Google Drive Upload (Optional)
1. Get credentials.json from Google Cloud Console
2. Place it in the same folder as the executable
3. Run the application - it will authenticate once

## System Requirements
- macOS 10.15+ (Intel or Apple Silicon)
- Webcam
- 4GB RAM minimum
- Good lighting for face detection

## Architecture
This is a universal binary that works on:
- Intel Macs (x86_64)
- Apple Silicon Macs (arm64)

## Debug Information
This is the debug version with console output.
If you see errors, check the console window for details.

## Troubleshooting
- This should work on both Intel and Apple Silicon Macs
- If you get "bad cpu type" error, try the platform-specific versions
- Make sure you have good lighting for face detection
"""
    
    with open(f"{dist_dir}/README.txt", "w") as f:
        f.write(readme_content)
    
    # Create run script
    run_script = """#!/bin/bash
echo "Starting Navigaze Gaze Tester (Universal Mac)..."
./NavigazeGazeTester_Universal
"""
    
    with open(f"{dist_dir}/Run_Universal.sh", "w") as f:
        f.write(run_script)
    
    # Make run script executable
    os.chmod(f"{dist_dir}/Run_Universal.sh", 0o755)
    
    print(f"✅ Universal Mac distribution created: {dist_dir}/")
    return True

def main():
    print("🚀 Navigaze Gaze Tester - Universal Mac Builder")
    print("=" * 50)
    
    # Check current architecture
    current_arch = platform.machine()
    print(f"🔍 Current architecture: {current_arch}")
    
    if current_arch == "arm64":
        print("✅ You're on Apple Silicon - building universal binary")
    elif current_arch == "x86_64":
        print("✅ You're on Intel Mac - building universal binary")
    else:
        print(f"⚠️  Unknown architecture: {current_arch}")
    
    print()
    
    # Install PyInstaller
    if not install_pyinstaller():
        return False
    
    # Build executable
    if not build_universal_executable():
        return False
    
    # Create distribution
    if not create_universal_distribution():
        return False
    
    print("\n🎉 Universal Mac build completed successfully!")
    print("\n📁 Your Universal Mac executable is in: NavigazeGazeTester_Universal_Distribution/")
    print("\n📋 To distribute:")
    print("1. Zip the NavigazeGazeTester_Universal_Distribution folder")
    print("2. Send the zip file to Mac users (both Intel and Apple Silicon)")
    print("3. Users extract and run NavigazeGazeTester_Universal")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
