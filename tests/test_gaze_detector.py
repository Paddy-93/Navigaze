#!/usr/bin/env python3
"""
Test script for gaze detector hybrid approach
Shows quick vs long gaze detection with duration tracking
"""

import cv2
import time
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from eye_tracking.gaze_detector import GazeDetector
from eye_tracking.face_landmarks import FaceLandmarks
from eye_tracking.calibration_popup import start_calibration_popup, is_calibration_complete, get_calibration_baseline
import mediapipe as mp

def test_gaze_detector():
    """Test the gaze detector with duration tracking"""
    
    print("🎯 Testing Gaze Detector with Duration Tracking")
    print("=" * 50)
    print("Look UP or DOWN to test gaze detection")
    print("Quick gaze (< 750ms) = Single action")
    print("Long gaze (> 750ms) = Continuous action")
    print("Press 'q' to quit")
    print("=" * 50)
    
    # Initialize components
    face_landmarks = FaceLandmarks()
    gaze_detector = GazeDetector()
    
    # Initialize MediaPipe face mesh
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    # Open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open camera")
        return
    
    print("📹 Camera opened successfully")
    print("🔍 Starting gaze detection...")
    
    # Calibration
    print("\n🎯 Starting calibration...")
    
    # Start calibration popup
    if not start_calibration_popup(duration=5.0, camera_index=0):
        print("❌ Failed to start calibration")
        return
    
    print("⏳ Calibrating... (stare at the red dot for 5 seconds)")
    
    # Wait for calibration to complete
    while not is_calibration_complete():
        time.sleep(0.1)
    
    # Get calibration baseline
    baseline = get_calibration_baseline()
    if baseline is None:
        print("❌ Calibration failed")
        return
    
    # Set the baseline in the gaze detector
    gaze_detector.set_baseline(baseline)
    
    print("✅ Calibration complete!")
    print("\n👁️  Start looking UP or DOWN...")
    
    # Main detection loop
    frame_count = 0
    last_gaze_type = None
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Process frame with MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0]
                h, w, _ = frame.shape
                
                # Get gaze metrics from landmarks
                avg_pupil_y, forehead_y, chin_y, pupil_relative, is_blinking = face_landmarks.get_gaze_metrics(landmarks, w, h)
                
                # Get gaze result
                gaze_result = gaze_detector.update(pupil_relative, head_moving=False, is_blinking=is_blinking)
                
                if gaze_result and gaze_result.get('gaze_detected', False):
                    direction = gaze_result.get('direction')
                    duration = gaze_result.get('duration', 0)
                    is_long_gaze = gaze_result.get('is_long_gaze', False)
                    
                    # Determine gaze type
                    if is_long_gaze:
                        gaze_type = f"LONG {direction} GAZE"
                    else:
                        gaze_type = f"QUICK {direction} GAZE"
                    
                    # Print when gaze type changes or every 5 frames for long gaze
                    if gaze_type != last_gaze_type or (is_long_gaze and frame_count % 5 == 0):
                        timestamp = time.strftime("%H:%M:%S")
                        print(f"[{timestamp}] {gaze_type} - Duration: {duration}ms")
                        last_gaze_type = gaze_type
                else:
                    # Neutral gaze
                    if last_gaze_type is not None:
                        print(f"[{time.strftime('%H:%M:%S')}] NEUTRAL GAZE - Stopped continuous action")
                        last_gaze_type = None
            
            # Display frame
            cv2.imshow('Gaze Detector Test', frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        face_mesh.close()
        from eye_tracking.calibration_popup import stop_calibration_popup
        stop_calibration_popup()
        print("✅ Test completed")

if __name__ == "__main__":
    test_gaze_detector()
