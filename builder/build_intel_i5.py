#!/usr/bin/env python3
"""
Build script specifically for Intel i5 Macs
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

def build_intel_i5_executable():
    """Build executable specifically for Intel i5 Macs"""
    print("🔨 Building Intel i5 Mac executable...")
    
    # PyInstaller command for Intel Mac
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console", 
        "--name", "NavigazeGazeTester_Intel_i5",
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
        print("✅ Intel i5 Mac executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False

def create_intel_i5_distribution():
    """Create distribution package for Intel i5 Mac"""
    print("📦 Creating Intel i5 Mac distribution...")
    
    dist_dir = "NavigazeGazeTester_Intel_i5_Distribution"
    
    # Remove existing distribution
    if os.path.exists(dist_dir):
        import shutil
        shutil.rmtree(dist_dir)
    
    os.makedirs(dist_dir, exist_ok=True)
    
    # Copy executable
    if os.path.exists("dist/NavigazeGazeTester_Intel_i5"):
        import shutil
        shutil.copy2("dist/NavigazeGazeTester_Intel_i5", f"{dist_dir}/NavigazeGazeTester_Intel_i5")
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
    
    # Create README for Intel i5 Mac
    readme_content = """# Navigaze Gaze Tester - Intel i5 Mac Version

## Quick Start
1. Double-click NavigazeGazeTester_Intel_i5 to run
2. Follow the on-screen instructions
3. Check console output for any errors

## Google Drive Upload (Optional)
1. Get credentials.json from Google Cloud Console
2. Place it in the same folder as the executable
3. Run the application - it will authenticate once

## System Requirements
- macOS 10.15+ (Intel Mac)
- Intel i5 processor or compatible
- Webcam
- 4GB RAM minimum
- Good lighting for face detection

## Architecture
This version is specifically built for Intel Macs (x86_64).
It should work on Intel i5, i7, i9, and other Intel-based Macs.

## Debug Information
This is the debug version with console output.
If you see errors, check the console window for details.

## Troubleshooting
- This executable is built for Intel Macs only
- If you get "bad cpu type" error, you might be on Apple Silicon
- Make sure you have good lighting for face detection
- Close other camera applications if camera is not detected
"""
    
    with open(f"{dist_dir}/README.txt", "w") as f:
        f.write(readme_content)
    
    # Create run script
    run_script = """#!/bin/bash
echo "Starting Navigaze Gaze Tester (Intel i5 Mac)..."
./NavigazeGazeTester_Intel_i5
"""
    
    with open(f"{dist_dir}/Run_Intel_i5.sh", "w") as f:
        f.write(run_script)
    
    # Make run script executable
    os.chmod(f"{dist_dir}/Run_Intel_i5.sh", 0o755)
    
    print(f"✅ Intel i5 Mac distribution created: {dist_dir}/")
    return True

def main():
    print("🚀 Navigaze Gaze Tester - Intel i5 Mac Builder")
    print("=" * 50)
    
    # Check current architecture
    current_arch = platform.machine()
    print(f"🔍 Current architecture: {current_arch}")
    
    if current_arch == "x86_64":
        print("✅ You're on Intel Mac - this will build natively for Intel")
    elif current_arch == "arm64":
        print("⚠️  You're on Apple Silicon - this will build for Intel Mac")
        print("   The executable will work on Intel Macs but may be slower on your Mac")
    else:
        print(f"⚠️  Unknown architecture: {current_arch}")
    
    print()
    
    # Install PyInstaller
    if not install_pyinstaller():
        return False
    
    # Build executable
    if not build_intel_i5_executable():
        return False
    
    # Create distribution
    if not create_intel_i5_distribution():
        return False
    
    print("\n🎉 Intel i5 Mac build completed successfully!")
    print("\n📁 Your Intel i5 Mac executable is in: NavigazeGazeTester_Intel_i5_Distribution/")
    print("\n📋 To distribute:")
    print("1. Zip the NavigazeGazeTester_Intel_i5_Distribution folder")
    print("2. Send the zip file to Intel Mac users")
    print("3. Users extract and run NavigazeGazeTester_Intel_i5")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
