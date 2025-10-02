@echo off
echo 🚀 Navigaze Gaze Tester - Build Script
echo =====================================

echo.
echo 📦 Installing PyInstaller...
python -m pip install pyinstaller

echo.
echo 🔨 Building executable...
python -m PyInstaller --onefile --windowed --name NavigazeGazeTester --add-data "gaze_detector_interface.py;." --add-data "real_gaze_detector.py;." --add-data "simulated_gaze_detector.py;." --add-data "google_drive_uploader.py;." --add-data "config.py;." --add-data "eye_tracking;eye_tracking" --add-data "input_processing;input_processing" --add-data "user_interface;user_interface" --hidden-import cv2 --hidden-import mediapipe --hidden-import numpy --hidden-import pyttsx3 --hidden-import googleapiclient --hidden-import "google.auth.transport.requests" --hidden-import "google_auth_oauthlib.flow" comprehensive_gaze_tester_real.py

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Build failed!
    pause
    exit /b 1
)

echo.
echo 📦 Creating distribution package...

if exist "NavigazeGazeTester_Distribution" rmdir /s /q "NavigazeGazeTester_Distribution"
mkdir "NavigazeGazeTester_Distribution"

copy "dist\NavigazeGazeTester.exe" "NavigazeGazeTester_Distribution\"
copy "google_drive_uploader.py" "NavigazeGazeTester_Distribution\"
copy "README_GOOGLE_DRIVE.md" "NavigazeGazeTester_Distribution\"

echo # Navigaze Gaze Tester > "NavigazeGazeTester_Distribution\README.txt"
echo. >> "NavigazeGazeTester_Distribution\README.txt"
echo ## Quick Start >> "NavigazeGazeTester_Distribution\README.txt"
echo 1. Double-click NavigazeGazeTester.exe to run >> "NavigazeGazeTester_Distribution\README.txt"
echo 2. Follow the on-screen instructions >> "NavigazeGazeTester_Distribution\README.txt"
echo 3. Results will be saved automatically >> "NavigazeGazeTester_Distribution\README.txt"
echo. >> "NavigazeGazeTester_Distribution\README.txt"
echo ## Google Drive Upload (Optional) >> "NavigazeGazeTester_Distribution\README.txt"
echo 1. Get credentials.json from Google Cloud Console >> "NavigazeGazeTester_Distribution\README.txt"
echo 2. Place it in the same folder as the executable >> "NavigazeGazeTester_Distribution\README.txt"
echo 3. Run the application - it will authenticate once >> "NavigazeGazeTester_Distribution\README.txt"
echo. >> "NavigazeGazeTester_Distribution\README.txt"
echo ## System Requirements >> "NavigazeGazeTester_Distribution\README.txt"
echo - Windows 10/11 (64-bit) >> "NavigazeGazeTester_Distribution\README.txt"
echo - Webcam >> "NavigazeGazeTester_Distribution\README.txt"
echo - 4GB RAM minimum >> "NavigazeGazeTester_Distribution\README.txt"
echo - Good lighting for face detection >> "NavigazeGazeTester_Distribution\README.txt"

echo @echo off > "NavigazeGazeTester_Distribution\Run_Navigaze.bat"
echo echo Starting Navigaze Gaze Tester... >> "NavigazeGazeTester_Distribution\Run_Navigaze.bat"
echo NavigazeGazeTester.exe >> "NavigazeGazeTester_Distribution\Run_Navigaze.bat"
echo pause >> "NavigazeGazeTester_Distribution\Run_Navigaze.bat"

echo.
echo 🎉 Build completed successfully!
echo.
echo 📁 Your executable is in: NavigazeGazeTester_Distribution\
echo.
echo 📋 To distribute:
echo 1. Zip the NavigazeGazeTester_Distribution folder
echo 2. Send the zip file to users
echo 3. Users extract and run NavigazeGazeTester.exe
echo.
pause
