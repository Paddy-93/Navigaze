#!/usr/bin/env python3
"""
Build script for Intel Mac (x86_64) compatibility - Fixed version
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

def build_intel_executable():
    """Build executable for Intel Mac architecture using Rosetta"""
    print("🔨 Building Intel Mac executable using Rosetta...")
    
    # Use arch -x86_64 to force Intel architecture
    python_cmd = ["arch", "-x86_64", sys.executable]
    
    # PyInstaller command for Intel Mac
    cmd = python_cmd + [
        "-m", "PyInstaller",
        "--onefile",
        "--console", 
        "--name", "NavigazeGazeTester_Intel_Fixed",
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
        print("✅ Intel Mac executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print("💡 Make sure you have Rosetta 2 installed: softwareupdate --install-rosetta")
        return False

def create_intel_distribution():
    """Create distribution package for Intel Mac"""
    print("📦 Creating Intel Mac distribution...")
    
    dist_dir = "NavigazeGazeTester_Intel_Fixed_Distribution"
    
    # Remove existing distribution
    if os.path.exists(dist_dir):
        import shutil
        shutil.rmtree(dist_dir)
    
    os.makedirs(dist_dir, exist_ok=True)
    
    # Copy executable
    if os.path.exists("dist/NavigazeGazeTester_Intel_Fixed"):
        import shutil
        shutil.copy2("dist/NavigazeGazeTester_Intel_Fixed", f"{dist_dir}/NavigazeGazeTester_Intel_Fixed")
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
    
    # Create README for Intel Mac
    readme_content = """# Navigaze Gaze Tester - Intel Mac Version (Fixed)

## Quick Start
1. Double-click NavigazeGazeTester_Intel_Fixed to run
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
This version is built for Intel Mac (x86_64) architecture using Rosetta 2.
It should work on both Intel Macs and Apple Silicon Macs (via Rosetta).

## Debug Information
This is the debug version with console output.
If you see errors, check the console window for details.

## Troubleshooting
- If you get "bad cpu type" error, this executable is for Intel Macs
- On Apple Silicon Macs, it will run via Rosetta 2
- Make sure you have Rosetta 2 installed if needed
"""
    
    with open(f"{dist_dir}/README.txt", "w") as f:
        f.write(readme_content)
    
    # Create run script
    run_script = """#!/bin/bash
echo "Starting Navigaze Gaze Tester (Intel Mac - Fixed)..."
./NavigazeGazeTester_Intel_Fixed
"""
    
    with open(f"{dist_dir}/Run_Intel_Fixed.sh", "w") as f:
        f.write(run_script)
    
    # Make run script executable
    os.chmod(f"{dist_dir}/Run_Intel_Fixed.sh", 0o755)
    
    print(f"✅ Intel Mac distribution created: {dist_dir}/")
    return True

def check_rosetta():
    """Check if Rosetta 2 is installed"""
    try:
        result = subprocess.run(["arch", "-x86_64", "python", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Rosetta 2 is available")
            return True
        else:
            print("❌ Rosetta 2 not available")
            return False
    except Exception as e:
        print(f"❌ Error checking Rosetta 2: {e}")
        return False

def main():
    print("🚀 Navigaze Gaze Tester - Intel Mac Builder (Fixed)")
    print("=" * 60)
    
    # Check current architecture
    current_arch = platform.machine()
    print(f"🔍 Current architecture: {current_arch}")
    
    if current_arch == "arm64":
        print("⚠️  You're on Apple Silicon - building for Intel Mac using Rosetta 2")
        if not check_rosetta():
            print("💡 Install Rosetta 2: softwareupdate --install-rosetta")
            return False
    elif current_arch == "x86_64":
        print("✅ You're on Intel Mac - this will build natively")
    else:
        print(f"⚠️  Unknown architecture: {current_arch}")
    
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
    
    print("\n🎉 Intel Mac build completed successfully!")
    print("\n📁 Your Intel Mac executable is in: NavigazeGazeTester_Intel_Fixed_Distribution/")
    print("\n📋 To distribute:")
    print("1. Zip the NavigazeGazeTester_Intel_Fixed_Distribution folder")
    print("2. Send the zip file to Intel Mac users")
    print("3. Users extract and run NavigazeGazeTester_Intel_Fixed")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
