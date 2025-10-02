#!/usr/bin/env python3
"""
Real Gaze Detector
Implementation of GazeDetectorInterface using actual camera and gaze detection
"""

import cv2
import time
import mediapipe as mp
import numpy as np
from typing import Dict, Any, Optional, Tuple
from gaze_detector_interface import GazeDetectorInterface
from eye_tracking.face_landmarks import FaceLandmarks
from eye_tracking.gaze_detector import GazeDetector

class RealGazeDetector(GazeDetectorInterface):
    """Real gaze detector using camera and face landmarks"""
    
    def __init__(self):
        self.cap = None
        self.face_mesh = None
        self.face_landmarks = None
        self.gaze_detector = None
        self.initialized = False
        self.ready = False
        
    def initialize(self) -> bool:
        """Initialize the real gaze detector"""
        try:
            # Initialize camera
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("❌ Failed to open camera")
                return False
                
            # Initialize MediaPipe Face Mesh (same as main script)
            mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            # Initialize face landmarks processor
            self.face_landmarks = FaceLandmarks()
            
            # Initialize gaze detector
            self.gaze_detector = GazeDetector()
            
            # Establish baseline (same as main script)
            print("🔍 Establishing gaze baseline...")
            baseline_data = []
            start_time = time.time()
            while time.time() - start_time < 3:  # Wait 3 seconds for baseline
                ret, frame = self.cap.read()
                if ret:
                    h, w = frame.shape[:2]
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = self.face_mesh.process(rgb_frame)
                    
                    if results.multi_face_landmarks:
                        landmarks = results.multi_face_landmarks[0]
                        avg_pupil_y, forehead_y, chin_y, pupil_relative, is_blinking = self.face_landmarks.get_gaze_metrics(landmarks, w, h)
                        baseline_data.append(avg_pupil_y)
                
            if baseline_data:
                baseline = sum(baseline_data) / len(baseline_data)
                self.gaze_detector.baseline_y = baseline
                print(f"✅ Baseline established: {baseline:.3f}")
            else:
                print("⚠️ No baseline data collected, using default")
                
            self.initialized = True
            self.ready = True
            print("✅ Real gaze detector initialized")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize real gaze detector: {e}")
            return False
    
    def update(self) -> Optional[Dict[str, Any]]:
        """Update gaze detection and return current gaze state"""
        if not self.ready or not self.cap or not self.face_mesh:
            return None
            
        try:
            # Read frame from camera
            ret, frame = self.cap.read()
            if not ret:
                return None
                
            h, w = frame.shape[:2]
            
            # Convert BGR to RGB for MediaPipe (same as main script)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Check if face_mesh is still valid before processing
            if not self.face_mesh:
                return None
                
            results = self.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0]
                
                # Get gaze metrics (same as main script)
                avg_pupil_y, forehead_y, chin_y, pupil_relative, is_blinking = self.face_landmarks.get_gaze_metrics(landmarks, w, h)
                
                # Process with gaze detector (same as main script)
                gaze_result = self.gaze_detector.update(pupil_relative, head_moving=False, is_blinking=is_blinking)
                
                # Add pupil_relative for calibration purposes
                if gaze_result:
                    gaze_result['pupil_relative'] = pupil_relative
                
                return gaze_result
            else:
                return None
                
        except Exception as e:
            # Don't print every frame error to avoid spam
            if not hasattr(self, '_update_error_logged'):
                print(f"❌ Error in gaze detection: {e}")
                self._update_error_logged = True
            return None
    
    def get_current_frame(self):
        """Get the current camera frame for video recording"""
        try:
            if hasattr(self, 'cap') and self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    return frame
        except Exception as e:
            print(f"Error getting camera frame: {e}")
        return None
    
    
    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            # Set flags first to prevent further access
            self.initialized = False
            self.ready = False
            
            # Close camera first
            if self.cap:
                self.cap.release()
                self.cap = None
            
            # Close MediaPipe with better error handling
            if self.face_mesh:
                try:
                    self.face_mesh.close()
                except (ValueError, AttributeError, RuntimeError) as e:
                    # Already closed or other cleanup error, ignore
                    pass
                finally:
                    self.face_mesh = None
            
            # Clear other references
            if hasattr(self, 'face_landmarks'):
                self.face_landmarks = None
            if hasattr(self, 'gaze_detector'):
                self.gaze_detector = None
                
            print("✅ Real gaze detector cleaned up")
            
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")
            # Force cleanup even if there are errors
            self.initialized = False
            self.ready = False
    
    def is_ready(self) -> bool:
        """Check if the gaze detector is ready for use"""
        return self.ready
    
    def calibrate(self, frame_data: Dict[str, Any]) -> bool:
        """Perform calibration with the given frame data"""
        # For real gaze detector, calibration is done during the first step
        # This method is called by the comprehensive tester but we don't need to do anything
        # The actual calibration happens in the calibration step using update()
        return True
    
    def reset_calibration(self) -> None:
        """Reset the gaze detector's calibration"""
        if self.gaze_detector:
            self.gaze_detector.reset()
    
    def get_gaze_result(self) -> Optional[Dict[str, Any]]:
        """Return the latest gaze detection result"""
        # This method is not used in the current implementation
        # The update() method returns the result directly
        return None
    
    def release(self) -> None:
        """Release any resources held by the gaze detector"""
        self.cleanup()
