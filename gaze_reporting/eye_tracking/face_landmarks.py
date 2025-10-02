import numpy as np
from config import LANDMARK_INDICES

class FaceLandmarks:
    """Utility class for handling MediaPipe face landmarks"""
    
    def __init__(self):
        self.indices = LANDMARK_INDICES
        # Eye landmarks for blink detection (MediaPipe face mesh landmarks)
        # Left eye: outer corner, top, inner corner, inner corner, bottom, outer corner
        self.LEFT_EYE = [33, 160, 158, 133, 153, 144]
        # Right eye: outer corner, top, inner corner, inner corner, bottom, outer corner  
        self.RIGHT_EYE = [362, 387, 385, 263, 373, 380]
        
        # Temporal blink detection
        self.ear_history = []
        self.ear_history_size = 4  # Require 4 consecutive frames below threshold
        self.blink_threshold = 0.26  # Lower threshold but with temporal filtering
    
    def get_iris_positions(self, landmarks, w, h):
        """Extract left and right iris positions from landmarks"""
        def xy(i): 
            return (landmarks.landmark[i].x * w, landmarks.landmark[i].y * h)
        
        # Get average positions for iris landmarks
        lcx = np.mean([xy(i)[0] for i in self.indices['LEFT_IRIS']])
        lcy = np.mean([xy(i)[1] for i in self.indices['LEFT_IRIS']])
        rcx = np.mean([xy(i)[0] for i in self.indices['RIGHT_IRIS']])
        rcy = np.mean([xy(i)[1] for i in self.indices['RIGHT_IRIS']])
        
        return (lcx, lcy), (rcx, rcy)
    
    def get_face_anchors(self, landmarks, w, h):
        """Extract key face anchor points for head motion detection"""
        def xy(i): 
            return (landmarks.landmark[i].x * w, landmarks.landmark[i].y * h)
        
        # Eye corners
        eye_l = xy(self.indices['L_EYE_CORNER'])
        eye_r = xy(self.indices['R_EYE_CORNER'])
        
        # Forehead and chin
        forehead = xy(self.indices['FOREHEAD'])
        chin = xy(self.indices['CHIN'])
        
        return eye_l, eye_r, forehead, chin
    
    def calculate_face_metrics(self, eye_l, eye_r, forehead, chin):
        """Calculate face metrics for head motion detection"""
        # Face center (between eye corners)
        cx_face = 0.5 * (eye_l[0] + eye_r[0])
        cy_face = 0.5 * (eye_l[1] + eye_r[1])
        
        # Inter-pupil distance (IPD)
        IPD = float(np.hypot(eye_r[0] - eye_l[0], eye_r[1] - eye_l[1])) + 1e-6
        
        # Face height span
        Hspan = float(np.hypot(chin[0] - forehead[0], chin[1] - forehead[1])) + 1e-6
        
        # Head orientation (roll)
        dir_vec = (eye_r[0] - eye_l[0], eye_r[1] - eye_l[1])
        theta = np.arctan2(dir_vec[1], dir_vec[0])
        
        return cx_face, cy_face, IPD, Hspan, theta
    
    def get_gaze_metrics(self, landmarks, w, h):
        """Calculate gaze-related metrics including blink detection"""
        # Get iris positions
        (lcx, lcy), (rcx, rcy) = self.get_iris_positions(landmarks, w, h)
        
        # Average pupil Y position
        avg_pupil_y = (lcy + rcy) / 2.0
        
        # Get forehead and chin Y positions
        forehead_y = landmarks.landmark[self.indices['FOREHEAD']].y * h
        chin_y = landmarks.landmark[self.indices['CHIN']].y * h
        
        # Calculate relative position (simple approach - works best)
        face_height = chin_y - forehead_y
        pupil_relative = (avg_pupil_y - forehead_y) / max(face_height, 1.0)
        
        # Simple blink detection based on eye aspect ratio
        is_blinking = self.detect_blink(landmarks, w, h)
        
        return avg_pupil_y, forehead_y, chin_y, pupil_relative, is_blinking
    
    def detect_blink(self, landmarks, w, h, blink_threshold=None):
        """Detect if eyes are blinking using temporal eye aspect ratio filtering"""
        if blink_threshold is None:
            blink_threshold = self.blink_threshold
            
        def xy(i): 
            return (landmarks.landmark[i].x * w, landmarks.landmark[i].y * h)
        
        def eye_aspect_ratio(eye_points):
            """Calculate eye aspect ratio for given eye landmarks"""
            if len(eye_points) < 6:
                return 0.3  # Default "open" value
            
            points = [xy(i) for i in eye_points]
            
            # Vertical distances (top-bottom of eye)
            v1 = np.hypot(points[1][0] - points[5][0], points[1][1] - points[5][1])
            v2 = np.hypot(points[2][0] - points[4][0], points[2][1] - points[4][1])
            
            # Horizontal distance (left-right corners)
            h1 = np.hypot(points[0][0] - points[3][0], points[0][1] - points[3][1])
            
            # Eye aspect ratio
            return (v1 + v2) / (2.0 * h1 + 1e-6)
        
        # Calculate EAR for both eyes
        left_ear = eye_aspect_ratio(self.LEFT_EYE)
        right_ear = eye_aspect_ratio(self.RIGHT_EYE)
        
        # Average eye aspect ratio
        avg_ear = (left_ear + right_ear) / 2.0
        
        # Add to history
        self.ear_history.append(avg_ear)
        if len(self.ear_history) > self.ear_history_size:
            self.ear_history.pop(0)
        
        # Require multiple consecutive frames below threshold for blink detection
        if len(self.ear_history) >= self.ear_history_size:
            consecutive_low = all(ear < blink_threshold for ear in self.ear_history)
            return consecutive_low
        
        # Not enough history yet
        return False