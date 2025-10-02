@echo off
echo 🚀 Navigaze Gaze Tester - Windows Debug Builder
echo ================================================

echo.
echo 📦 Installing PyInstaller...
python -m pip install pyinstaller

echo.
echo 🔨 Building debug executable...
python -m PyInstaller --onefile --console --name NavigazeGazeTester_Debug --add-data "gaze_detector_interface.py;." --add-data "real_gaze_detector.py;." --add-data "simulated_gaze_detector.py;." --add-data "google_drive_uploader.py;." --add-data "config.py;." --add-data "eye_tracking;eye_tracking" --add-data "input_processing;input_processing" --add-data "user_interface;user_interface" --hidden-import cv2 --hidden-import mediapipe --hidden-import mediapipe.python.solutions.face_mesh --hidden-import mediapipe.python.solutions.face_detection --hidden-import numpy --hidden-import pyttsx3 --hidden-import googleapiclient --hidden-import "google.auth.transport.requests" --hidden-import "google_auth_oauthlib.flow" --collect-data mediapipe --debug all comprehensive_gaze_tester_real.py

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Build failed!
    pause
    exit /b 1
)

echo.
echo 📦 Creating debug distribution package...

if exist "NavigazeGazeTester_Debug_Distribution" rmdir /s /q "NavigazeGazeTester_Debug_Distribution"
mkdir "NavigazeGazeTester_Debug_Distribution"

copy "dist\NavigazeGazeTester_Debug.exe" "NavigazeGazeTester_Debug_Distribution\"
copy "google_drive_uploader.py" "NavigazeGazeTester_Debug_Distribution\"
copy "README_GOOGLE_DRIVE.md" "NavigazeGazeTester_Debug_Distribution\"

echo # Navigaze Gaze Tester - Debug Version > "NavigazeGazeTester_Debug_Distribution\README.txt"
echo. >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo ## Quick Start >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo 1. Double-click NavigazeGazeTester_Debug.exe to run >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo 2. Follow the on-screen instructions >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo 3. Check console output for any errors >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo. >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo ## Google Drive Upload (Optional) >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo 1. Get credentials.json from Google Cloud Console >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo 2. Place it in the same folder as the executable >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo 3. Run the application - it will authenticate once >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo. >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo ## System Requirements >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo - Windows 10/11 (64-bit) >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo - Webcam >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo - 4GB RAM minimum >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo - Good lighting for face detection >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo. >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo ## Debug Information >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo This is the debug version with console output. >> "NavigazeGazeTester_Debug_Distribution\README.txt"
echo If you see errors, check the console window for details. >> "NavigazeGazeTester_Debug_Distribution\README.txt"

echo @echo off > "NavigazeGazeTester_Debug_Distribution\Run_Debug.bat"
echo echo Starting Navigaze Gaze Tester Debug... >> "NavigazeGazeTester_Debug_Distribution\Run_Debug.bat"
echo NavigazeGazeTester_Debug.exe >> "NavigazeGazeTester_Debug_Distribution\Run_Debug.bat"
echo pause >> "NavigazeGazeTester_Debug_Distribution\Run_Debug.bat"

echo.
echo 🎉 Debug build completed successfully!
echo.
echo 📁 Your debug executable is in: NavigazeGazeTester_Debug_Distribution\
echo.
echo 📋 To distribute:
echo 1. Zip the NavigazeGazeTester_Debug_Distribution folder
echo 2. Send the zip file to users
echo 3. Users extract and run NavigazeGazeTester_Debug.exe
echo.
pause
