#!/usr/bin/env python3
"""
Simple calibration popup that captures baseline then disappears
Does NOT interfere with existing status bar system
"""

import cv2
import numpy as np
import time
import threading
import platform
import mediapipe as mp
import os
import tempfile

# Import face landmarks for gaze calculation
from eye_tracking.face_landmarks import FaceLandmarks
from config import GAZE_CONFIG, CALIBRATION_CONFIG

# Platform-specific imports for forcing window to front
try:
    if platform.system() == "Windows":
        import win32gui
        import win32con
        import win32api
        WINDOWS_AVAILABLE = True
    else:
        WINDOWS_AVAILABLE = False
except ImportError:
    WINDOWS_AVAILABLE = False

class CalibrationPopup:
    """Simple calibration popup that captures baseline then disappears"""
    
    def __init__(self, calibration_duration=5.0, camera_index=0):
        self.calibration_duration = calibration_duration
        self.is_active = False
        self.calibration_complete = False
        self.start_time = None
        self.window_name = "GazeTalk_Calibration"
        self.thread = None
        
        # Popup dimensions from config
        self.width = CALIBRATION_CONFIG['window_width']
        self.height = CALIBRATION_CONFIG['window_height']
        
        # Real gaze baseline capture
        self.baseline_y = None
        self.gaze_samples = []
        self.baseline_frames = GAZE_CONFIG['baseline_frames']
        
        # Camera and MediaPipe for gaze capture
        self.camera_index = camera_index
        self.cap = None
        self.face_mesh = None
        self.face_landmarks = None
        
    def start_calibration(self):
        """Start calibration popup and capture baseline"""
        if self.is_active:
            return False
        
        # Initialize camera and MediaPipe
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                print("❌ Failed to open camera for calibration")
                return False
            
            # Initialize MediaPipe
            mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            
            # Initialize face landmarks
            self.face_landmarks = FaceLandmarks()
            
        except Exception as e:
            print(f"❌ Failed to initialize camera/MediaPipe: {e}")
            return False
        
        self.is_active = True
        self.calibration_complete = False
        self.start_time = time.time()
        
        # Reset gaze capture
        self.baseline_y = None
        self.gaze_samples = []
        
        # Start display thread
        self.thread = threading.Thread(target=self._display_loop, daemon=True)
        self.thread.start()
        
        return True
    
    def is_calibration_complete(self):
        """Check if calibration is complete"""
        return self.calibration_complete
    
    def get_baseline(self):
        """Get the captured baseline"""
        return self.baseline_y
    
    def stop(self):
        """Stop the calibration popup"""
        self.is_active = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        
        # Clean up camera and MediaPipe
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        if self.face_mesh is not None:
            self.face_mesh.close()
            self.face_mesh = None
        
        try:
            cv2.destroyWindow(self.window_name)
            cv2.waitKey(1)
        except:
            pass
    
    def _display_loop(self):
        """Main display loop - just calibration, then close"""
        try:
            while self.is_active and not self.calibration_complete:
                elapsed = time.time() - self.start_time
                remaining = max(0, self.calibration_duration - elapsed)
                
                # Capture gaze data during calibration
                self._capture_gaze_sample()
                
                # Create calibration image
                samples_collected = len(self.gaze_samples)
                img = self._create_calibration_image(remaining, samples_collected)
                
                # Display popup
                cv2.imshow(self.window_name, img)
                
                # Position in center
                self._position_window_center()
                
                # Force to front
                self._force_window_to_front()
                
                # Check if calibration complete
                if remaining <= 0 or (self.baseline_y is not None and samples_collected >= self.baseline_frames):
                    self.calibration_complete = True
                    print("✅ Calibration complete! Closing calibration popup...")
                    
                    # Signal that calibration is complete
                    try:
                        import tempfile
                        calibration_file = os.path.join(tempfile.gettempdir(), "gazetalk_calibration_complete.txt")
                        with open(calibration_file, 'w') as f:
                            f.write("calibration_complete")
                        print("🎯 Calibration completion signal sent")
                    except Exception as e:
                        print(f"⚠️ Could not create calibration completion file: {e}")
                    
                    break
                
                # Process events
                key = cv2.waitKey(50) & 0xFF
                if key == 27:  # ESC to cancel
                    self.is_active = False
                    break
            
            # Close calibration popup
            try:
                cv2.destroyWindow(self.window_name)
                cv2.waitKey(1)
            except:
                pass
            
        except Exception as e:
            print(f"Error in calibration display: {e}")
            self.is_active = False
    
    def _capture_gaze_sample(self):
        """Capture a gaze sample for baseline calculation"""
        if self.cap is None or self.face_mesh is None or self.face_landmarks is None:
            return
        
        try:
            # Read frame from camera
            ret, frame = self.cap.read()
            if not ret:
                return
            
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0]
                h, w = frame.shape[:2]
                
                # Calculate gaze metrics (same as original system)
                avg_pupil_y, forehead_y, chin_y, pupil_relative, is_blinking = self.face_landmarks.get_gaze_metrics(landmarks, w, h)
                
                # Only collect samples when not blinking
                if not is_blinking and self.baseline_y is None:
                    self.gaze_samples.append(pupil_relative)
                    
                    # Calculate baseline when we have enough samples
                    if len(self.gaze_samples) >= self.baseline_frames:
                        self.baseline_y = float(np.mean(self.gaze_samples))
                        print(f"📊 Gaze baseline captured: {self.baseline_y:.3f} (from {len(self.gaze_samples)} samples)")
                        
        except Exception as e:
            # Silently ignore camera/processing errors during calibration
            pass
    
    def _create_calibration_image(self, remaining_time, samples_collected=0):
        """Create the calibration popup image"""
        # Create black background
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Add border
        cv2.rectangle(img, (0, 0), (self.width-1, self.height-1), (100, 100, 100), 2)
        
        # Add title
        title = "GazeTalk Calibration"
        title_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        title_x = (self.width - title_size[0]) // 2
        cv2.putText(img, title, (title_x, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        # Add instruction
        instruction = "Stare at the RED DOT"
        inst_size = cv2.getTextSize(instruction, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        inst_x = (self.width - inst_size[0]) // 2
        cv2.putText(img, instruction, (inst_x, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        
        # Add sample collection progress
        if samples_collected > 0:
            progress_text = f"Gaze Samples: {samples_collected}/{self.baseline_frames}"
            progress_size = cv2.getTextSize(progress_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            progress_x = (self.width - progress_size[0]) // 2
            cv2.putText(img, progress_text, (progress_x, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # Draw red dot based on config
        center_x = self.width // 2
        
        # Position red dot based on config
        if CALIBRATION_CONFIG['red_dot_position'] == 'center':
            center_y = self.height // 2
        elif CALIBRATION_CONFIG['red_dot_position'] == 'upper_third':
            center_y = self.height // 3
        elif CALIBRATION_CONFIG['red_dot_position'] == 'custom':
            center_y = CALIBRATION_CONFIG['red_dot_custom_y']
        else:
            center_y = self.height // 3  # Default to upper third
        
        # Draw red dot with configurable size
        dot_radius = CALIBRATION_CONFIG['red_dot_size']
        border_width = CALIBRATION_CONFIG['red_dot_border_width']
        cv2.circle(img, (center_x, center_y), dot_radius, (0, 0, 255), -1)  # Red filled circle
        cv2.circle(img, (center_x, center_y), dot_radius + 1, (255, 255, 255), border_width)  # White border
        
        # Add countdown
        countdown_text = f"{remaining_time:.1f}s"
        countdown_size = cv2.getTextSize(countdown_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
        countdown_x = (self.width - countdown_size[0]) // 2
        cv2.putText(img, countdown_text, (countdown_x, center_y + 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
        
        # Add progress bar
        if self.calibration_duration > 0:
            progress = 1.0 - (remaining_time / self.calibration_duration)
        else:
            progress = 1.0  # Complete if duration is 0
        bar_width = 350
        bar_height = 12
        bar_x = (self.width - bar_width) // 2
        bar_y = center_y + 120
        
        # Background bar
        cv2.rectangle(img, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
        
        # Progress bar
        progress_width = int(bar_width * progress)
        if progress_width > 0:
            cv2.rectangle(img, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), (0, 255, 0), -1)
        
        # Add ESC instruction
        esc_text = "Press ESC to cancel"
        esc_size = cv2.getTextSize(esc_text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
        esc_x = (self.width - esc_size[0]) // 2
        cv2.putText(img, esc_text, (esc_x, self.height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (128, 128, 128), 1)
        
        return img
    
    def _position_window_center(self):
        """Position window in center of screen"""
        # Position window based on config
        try:
            if CALIBRATION_CONFIG['position_mode'] == 'center':
                # Center the window on screen
                import tkinter as tk
                root = tk.Tk()
                screen_width = root.winfo_screenwidth()
                screen_height = root.winfo_screenheight()
                root.destroy()
                
                x = (screen_width - self.width) // 2
                y = (screen_height - self.height) // 2
                cv2.moveWindow(self.window_name, x, y)
            elif CALIBRATION_CONFIG['position_mode'] == 'custom':
                # Use custom position from config
                x = CALIBRATION_CONFIG['custom_x']
                y = CALIBRATION_CONFIG['custom_y']
                cv2.moveWindow(self.window_name, x, y)
            else:
                # Auto mode - try center, fallback to custom
                try:
                    import tkinter as tk
                    root = tk.Tk()
                    screen_width = root.winfo_screenwidth()
                    screen_height = root.winfo_screenheight()
                    root.destroy()
                    
                    x = (screen_width - self.width) // 2
                    y = (screen_height - self.height) // 2
                    cv2.moveWindow(self.window_name, x, y)
                except:
                    x = CALIBRATION_CONFIG['fallback_x']
                    y = CALIBRATION_CONFIG['fallback_y']
                    cv2.moveWindow(self.window_name, x, y)
        except:
            # Final fallback
            x = CALIBRATION_CONFIG['fallback_x']
            y = CALIBRATION_CONFIG['fallback_y']
            cv2.moveWindow(self.window_name, x, y)
    
    def _force_window_to_front(self):
        """Force window to front using platform-specific methods"""
        try:
            if WINDOWS_AVAILABLE and platform.system() == "Windows":
                hwnd = win32gui.FindWindow(None, self.window_name)
                if hwnd:
                    # More aggressive window forcing
                    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
                    win32gui.SetForegroundWindow(hwnd)
                    win32gui.BringWindowToTop(hwnd)
        except:
            pass

# Global calibration popup instance
calibration_popup = None

def start_calibration_popup(duration=5.0, camera_index=0):
    """Start the calibration popup"""
    global calibration_popup
    
    if calibration_popup is not None:
        calibration_popup.stop()
    
    calibration_popup = CalibrationPopup(calibration_duration=duration, camera_index=camera_index)
    return calibration_popup.start_calibration()

def is_calibration_complete():
    """Check if calibration is complete"""
    global calibration_popup
    if calibration_popup is None:
        return False
    return calibration_popup.is_calibration_complete()

def get_calibration_baseline():
    """Get the baseline from calibration"""
    global calibration_popup
    if calibration_popup is not None:
        return calibration_popup.get_baseline()
    return None

def stop_calibration_popup():
    """Stop the calibration popup"""
    global calibration_popup
    if calibration_popup is not None:
        calibration_popup.stop()
        calibration_popup = None
