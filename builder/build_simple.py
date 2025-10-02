#!/usr/bin/env python3
"""
Simple build script for Navigaze Gaze Tester executable
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not present"""
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
        except subprocess.CalledProcessError:
            print("❌ Failed to install PyInstaller")
            return False

def build_executable():
    """Build the executable"""
    print("🔨 Building executable...")
    
    # PyInstaller command - detect OS for correct separator
    separator = ";" if os.name == "nt" else ":"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",  # Directory instead of single file for .app bundles
        "--windowed",  # No console window
        "--name", "NavigazeGazeTester",
        "--add-data", f"gaze_detector_interface.py{separator}.",
        "--add-data", f"real_gaze_detector.py{separator}.",
        "--add-data", f"simulated_gaze_detector.py{separator}.",
        "--add-data", f"google_drive_uploader.py{separator}.",
        "--add-data", f"config.py{separator}.",
        "--add-data", f"eye_tracking{separator}eye_tracking",
        "--add-data", f"input_processing{separator}input_processing", 
        "--add-data", f"user_interface{separator}user_interface",
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
        "comprehensive_gaze_tester_real.py"
    ]
    
    try:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True)
        print("✅ Executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False

def create_distribution():
    """Create distribution folder with all files"""
    print("📦 Creating distribution package...")
    
    dist_folder = Path("NavigazeGazeTester_Distribution")
    if dist_folder.exists():
        shutil.rmtree(dist_folder)
    dist_folder.mkdir()
    
    # Copy executable (handle both .exe and .app)
    exe_path = Path("dist/NavigazeGazeTester.exe")
    app_path = Path("dist/NavigazeGazeTester.app")
    exe_dir = Path("dist/NavigazeGazeTester")  # Directory version
    
    if exe_path.exists():
        # Windows executable
        shutil.copy2(exe_path, dist_folder / "NavigazeGazeTester.exe")
        print("✅ Windows executable copied")
    elif app_path.exists():
        # Mac app bundle
        shutil.copytree(app_path, dist_folder / "NavigazeGazeTester.app")
        print("✅ Mac app bundle copied")
    elif exe_dir.exists():
        # Mac directory version - create .app bundle
        shutil.copytree(exe_dir, dist_folder / "NavigazeGazeTester.app")
        print("✅ Mac directory copied as .app bundle")
    else:
        print("❌ Executable not found")
        return False
    
    # Copy additional files
    additional_files = [
        "google_drive_uploader.py",
        "README_GOOGLE_DRIVE.md"
    ]
    
    for file in additional_files:
        if Path(file).exists():
            shutil.copy2(file, dist_folder / file)
            print(f"✅ {file} copied")
    
    # Create README for distribution
    readme_content = """# Navigaze Gaze Tester

## Quick Start
1. Double-click `NavigazeGazeTester.exe` to run
2. Follow the on-screen instructions
3. Results will be saved automatically

## Google Drive Upload (Optional)
1. Get `credentials.json` from Google Cloud Console
2. Place it in the same folder as the executable
3. Run the application - it will authenticate once

## System Requirements
- Windows 10/11 (64-bit)
- Webcam
- 4GB RAM minimum
- Good lighting for face detection

## Troubleshooting
- Ensure camera is not used by other apps
- Check camera permissions
- Run as administrator if needed
"""
    
    with open(dist_folder / "README.txt", 'w') as f:
        f.write(readme_content)
    
    print("✅ README.txt created")
    
    # Create batch file for easy running
    batch_content = """@echo off
echo Starting Navigaze Gaze Tester...
NavigazeGazeTester.exe
pause
"""
    
    with open(dist_folder / "Run_Navigaze.bat", 'w') as f:
        f.write(batch_content)
    
    print("✅ Run_Navigaze.bat created")
    print(f"✅ Distribution package created: {dist_folder}/")
    
    return True

def main():
    print("🚀 Navigaze Gaze Tester - Simple Builder")
    print("=" * 45)
    
    # Install PyInstaller
    if not install_pyinstaller():
        return False
    
    # Build executable
    if not build_executable():
        return False
    
    # Create distribution
    if not create_distribution():
        return False
    
    print("\n🎉 Build completed successfully!")
    print("\n📁 Your executable is in: NavigazeGazeTester_Distribution/")
    print("\n📋 To distribute:")
    print("1. Zip the NavigazeGazeTester_Distribution folder")
    print("2. Send the zip file to users")
    print("3. Users extract and run NavigazeGazeTester.exe")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        input("Press Enter to exit...")
        sys.exit(1)
