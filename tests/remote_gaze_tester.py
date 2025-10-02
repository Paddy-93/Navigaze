#!/usr/bin/env python3
"""
Remote Gaze Testing Interface
GUI application for testing eye gaze tracking effectiveness with dual recording and audio narration
Uses existing gaze detector and calibration logic for accurate real-time testing
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import time
import threading
import json
import os
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

# Import existing components
from eye_tracking.gaze_detector import GazeDetector
from eye_tracking.face_landmarks import FaceLandmarks
# Removed calibration popup import - using our own calibration method
from config import GAZE_CONFIG, CONTINUOUS_GAZE_CONFIG
import mediapipe as mp

# Try to import text-to-speech
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠️ pyttsx3 not available. Audio narration disabled.")

class RemoteGazeTester:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Remote Gaze Testing Interface")
        self.root.geometry("1200x800")
        
        # Initialize components using existing logic
        self.gaze_detector = GazeDetector()
        self.face_landmarks = FaceLandmarks()
        
        # MediaPipe Face Mesh (same as main.py)
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Test state
        self.current_step = 0
        self.test_steps = [
            {"name": "Initial Calibration", "instruction": "Look at the red dot for 5 seconds", "type": "calibration"},
            {"name": "Quick UP Gazes", "instruction": "Look UP quickly 5 times (short gazes)", "type": "quick_up", "duration": 15, "repetitions": 5, "target_count": 5},
            {"name": "Recalibration 1", "instruction": "Look at the red dot for 5 seconds", "type": "calibration"},
            {"name": "Quick DOWN Gazes", "instruction": "Look DOWN quickly 5 times (short gazes)", "type": "quick_down", "duration": 15, "repetitions": 5, "target_count": 5},
            {"name": "Recalibration 2", "instruction": "Look at the red dot for 5 seconds", "type": "calibration"},
            {"name": "Long UP Holds", "instruction": "Hold UP gaze for 5 seconds, repeat 3 times", "type": "long_up", "duration": 20, "repetitions": 3, "hold_duration": 5},
            {"name": "Recalibration 3", "instruction": "Look at the red dot for 5 seconds", "type": "calibration"},
            {"name": "Long DOWN Holds", "instruction": "Hold DOWN gaze for 5 seconds, repeat 3 times", "type": "long_down", "duration": 20, "repetitions": 3, "hold_duration": 5},
            {"name": "Recalibration 4", "instruction": "Look at the red dot for 5 seconds", "type": "calibration"},
            {"name": "Neutral Hold", "instruction": "Hold neutral gaze for 5 seconds", "type": "neutral_hold", "duration": 8, "hold_duration": 5},
            {"name": "Recalibration 5", "instruction": "Look at the red dot for 5 seconds", "type": "calibration"},
            {"name": "UP-DOWN-UP-DOWN Sequence", "instruction": "Perform UP→DOWN→UP→DOWN pattern 3 times", "type": "sequence_udud", "duration": 25, "repetitions": 3, "pattern": ["UP", "DOWN", "UP", "DOWN"]},
            {"name": "Recalibration 6", "instruction": "Look at the red dot for 5 seconds", "type": "calibration"},
            {"name": "DOWN-UP-DOWN-UP Sequence", "instruction": "Perform DOWN→UP→DOWN→UP pattern 3 times", "type": "sequence_dudu", "duration": 25, "repetitions": 3, "pattern": ["DOWN", "UP", "DOWN", "UP"]},
            {"name": "Recalibration 7", "instruction": "Look at the red dot for 5 seconds", "type": "calibration"},
            {"name": "DOWN-DOWN-UP-UP Sequence", "instruction": "Perform DOWN→DOWN→UP→UP pattern 3 times", "type": "sequence_dduu", "duration": 25, "repetitions": 3, "pattern": ["DOWN", "DOWN", "UP", "UP"]}
        ]
        
        # Camera and recording
        self.cap = None
        self.camera_index = 0
        self.recording = False
        self.raw_writer = None
        self.analysis_writer = None
        
        # Test results
        self.test_results = []
        self.step_start_time = 0
        self.session_start_time = time.time()
        self.step_retry_count = 0
        self.max_retries = 2
        
        # TTS
        if TTS_AVAILABLE:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)  # Slower speech
            self.tts_queue = []
            self.tts_speaking = False
        else:
            self.tts_engine = None
            self.tts_queue = []
            self.tts_speaking = False
        
        self.setup_ui()
        self.start_camera()
        
    def setup_ui(self):
        """Setup the GUI interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Left side - Large instruction display
        instruction_frame = ttk.LabelFrame(main_frame, text="Test Instructions", padding="20")
        instruction_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Large instruction display
        self.instruction_display = tk.Label(instruction_frame, 
                                          text="Click 'Start Test' to begin remote gaze testing",
                                          font=("Arial", 24, "bold"),
                                          fg="white", bg="darkblue",
                                          width=40, height=20,
                                          wraplength=600,
                                          justify=tk.CENTER)
        self.instruction_display.pack(expand=True, fill=tk.BOTH)
        
        # Recording status (hidden but still functional)
        self.recording_frame = ttk.Frame(instruction_frame)
        self.recording_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.recording_status = tk.Label(self.recording_frame, text="● Not Recording", fg="red")
        self.recording_status.pack(side=tk.LEFT)
        
        # Hidden camera labels for recording (not displayed)
        self.camera_label = None
        self.analysis_label = None
        
        # Right side - Instructions and controls
        control_frame = ttk.LabelFrame(main_frame, text="Test Control", padding="5")
        control_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        control_frame.columnconfigure(0, weight=1)
        
        # Current step display
        self.step_label = tk.Label(control_frame, text="Step 1/12: Initial Calibration", 
                                  font=("Arial", 14, "bold"))
        self.step_label.pack(pady=(0, 10))
        
        # Instruction display
        self.instruction_label = tk.Label(control_frame, 
                                        text="Look at the red dot for 5 seconds",
                                        font=("Arial", 12), wraplength=300, justify=tk.CENTER)
        self.instruction_label.pack(pady=(0, 20))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(control_frame, variable=self.progress_var, 
                                          maximum=100, length=300)
        self.progress_bar.pack(pady=(0, 20))
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(pady=(0, 20))
        
        self.start_button = ttk.Button(button_frame, text="Start Test", command=self.start_test)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.next_button = ttk.Button(button_frame, text="Next Step", command=self.next_step, state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.reset_button = ttk.Button(button_frame, text="Reset", command=self.reset_test)
        self.reset_button.pack(side=tk.LEFT)
        
        # Recording controls
        recording_frame = ttk.LabelFrame(control_frame, text="Recording", padding="5")
        recording_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.record_button = ttk.Button(recording_frame, text="Start Recording", command=self.toggle_recording)
        self.record_button.pack()
        
        # Metrics display
        metrics_frame = ttk.LabelFrame(control_frame, text="Current Metrics", padding="5")
        metrics_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.response_time_label = tk.Label(metrics_frame, text="Response Time: 0.0s")
        self.response_time_label.pack()
        
        self.accuracy_label = tk.Label(metrics_frame, text="Accuracy: 0%")
        self.accuracy_label.pack()
        
        self.detection_label = tk.Label(metrics_frame, text="Current Gaze: NEUTRAL")
        self.detection_label.pack()
        
        # Results display
        results_frame = ttk.LabelFrame(main_frame, text="Test Results", padding="5")
        results_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Results text area with scrollbar
        text_frame = ttk.Frame(results_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.results_text = tk.Text(text_frame, height=8, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def start_camera(self):
        """Initialize camera using same logic as main.py"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                raise Exception("Could not open camera")
            
            # Set camera properties (same as main.py)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.update_camera()
            self.log_result("✅ Camera initialized successfully")
            
        except Exception as e:
            self.log_result(f"❌ Camera error: {e}")
            messagebox.showerror("Camera Error", f"Could not initialize camera: {e}")
    
    def update_camera(self):
        """Update camera feed with gaze detection overlay"""
        if self.cap is None:
            return
        
        ret, frame = self.cap.read()
        if not ret:
            self.root.after(33, self.update_camera)  # ~30 FPS
            return
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        
        # Create analysis frame (copy for overlay)
        analysis_frame = frame.copy()
        
        # Process with MediaPipe (same as main.py)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        gaze_result = None
        avg_pupil_y = None  # Initialize variable
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            
            # Get gaze metrics (same as main.py)
            avg_pupil_y, forehead_y, chin_y, pupil_relative, is_blinking = self.face_landmarks.get_gaze_metrics(landmarks, w, h)
            
            # Draw face landmarks on analysis frame
            self.draw_face_landmarks(analysis_frame, landmarks, w, h)
            
            # Process with gaze detector
            gaze_result = self.gaze_detector.update(pupil_relative, head_moving=False, is_blinking=is_blinking)
            
        # Draw gaze analysis overlay
        self.draw_gaze_overlay(analysis_frame, gaze_result, avg_pupil_y, w, h)
        
        # Draw calibration overlay if calibrating
        if hasattr(self, 'calibrating') and self.calibrating:
            self.draw_calibration_overlay(analysis_frame, w, h)
            # Also update instruction display for calibration with visual red dot
            if hasattr(self, 'calibration_remaining'):
                calib_text = f"🔴 CALIBRATION 🔴\n\nLook at the RED DOT below\n\nTime remaining: {self.calibration_remaining:.1f} seconds\n\n\n\n\n\n        🔴\n\n\n\n\n"
                self.instruction_display.config(text=calib_text, fg="red", bg="yellow", font=("Arial", 16, "bold"))
            else:
                calib_text = f"🔴 CALIBRATION 🔴\n\nLook at the RED DOT below\n\nStarting in 3 seconds...\n\n\n\n\n\n        🔴\n\n\n\n\n"
                self.instruction_display.config(text=calib_text, fg="red", bg="yellow", font=("Arial", 16, "bold"))
        
        # Update detection label
        if gaze_result:
            direction = gaze_result.get('direction', 'NEUTRAL')
            is_continuous = gaze_result.get('is_continuous_gaze', False)
            continuous_text = " (CONTINUOUS)" if is_continuous else ""
            self.detection_label.config(text=f"Current Gaze: {direction}{continuous_text}")
        
        # Process current test step
        self.process_test_step(gaze_result)
        
        # Record frames if recording
        if self.recording:
            if self.raw_writer:
                self.raw_writer.write(frame)
            if self.analysis_writer:
                self.analysis_writer.write(analysis_frame)
        
        # Convert to PhotoImage and display
        display_frame = cv2.cvtColor(analysis_frame, cv2.COLOR_BGR2RGB)
        display_frame = cv2.resize(display_frame, (480, 360))  # Resize for display
        
        from PIL import Image, ImageTk
        image = Image.fromarray(display_frame)
        photo = ImageTk.PhotoImage(image)
        
        # Camera display is hidden - only record in background
        # self.camera_label.configure(image=photo)  # Hidden
        # self.camera_label.image = photo  # Keep a reference
        
        # Schedule next update
        self.root.after(33, self.update_camera)  # ~30 FPS
    
    def draw_face_landmarks(self, frame, landmarks, w, h):
        """Draw face landmarks on analysis frame"""
        # Draw key face landmarks as small blue dots
        key_points = [10, 151, 9, 8, 168, 6, 197, 195, 5, 4, 1, 19, 94, 125]  # Key face points
        
        for point_idx in key_points:
            if point_idx < len(landmarks.landmark):
                point = landmarks.landmark[point_idx]
                x = int(point.x * w)
                y = int(point.y * h)
                cv2.circle(frame, (x, y), 2, (255, 0, 0), -1)  # Blue dots
    
    def draw_gaze_overlay(self, frame, gaze_result, pupil_y, w, h):
        """Draw gaze analysis overlay on frame"""
        if not gaze_result:
            return
        
        # Draw pupil position as red dot
        pupil_x = w // 2  # Approximate center
        pupil_screen_y = int(pupil_y) if pupil_y else h // 2
        cv2.circle(frame, (pupil_x, pupil_screen_y), 5, (0, 0, 255), -1)  # Red pupil dot
        
        # Draw baseline if available
        if self.gaze_detector.baseline_y is not None:
            baseline_screen_y = int(self.gaze_detector.baseline_y * h) if self.gaze_detector.baseline_y < 1 else int(self.gaze_detector.baseline_y)
            cv2.line(frame, (50, baseline_screen_y), (w-50, baseline_screen_y), (0, 255, 255), 2)  # Yellow baseline
            cv2.putText(frame, "BASELINE", (60, baseline_screen_y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # Draw gaze direction arrow
        direction = gaze_result.get('direction')
        if direction:
            center_x, center_y = w // 2, h // 2
            arrow_length = 50
            
            if direction == "UP":
                end_point = (center_x, center_y - arrow_length)
                color = (0, 255, 0)  # Green
            elif direction == "DOWN":
                end_point = (center_x, center_y + arrow_length)
                color = (0, 0, 255)  # Red
            else:
                end_point = (center_x, center_y)
                color = (128, 128, 128)  # Gray
            
            cv2.arrowedLine(frame, (center_x, center_y), end_point, color, 3, tipLength=0.3)
        
        # Draw status text
        status_text = f"Gaze: {direction or 'NEUTRAL'}"
        if gaze_result.get('is_continuous_gaze', False):
            status_text += " (CONTINUOUS)"
        
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw confidence bar
        offset = gaze_result.get('offset', 0)
        confidence = min(100, abs(offset) * 1000)  # Convert to percentage
        bar_width = int(confidence * 2)  # Scale for display
        cv2.rectangle(frame, (10, h-30), (10 + bar_width, h-10), (0, 255, 0), -1)
        cv2.putText(frame, f"Confidence: {confidence:.0f}%", (10, h-35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def draw_calibration_overlay(self, frame, w, h):
        """Draw prominent calibration overlay"""
        # Draw large red circle in center
        center_x, center_y = w // 2, h // 2
        cv2.circle(frame, (center_x, center_y), 30, (0, 0, 255), -1)  # Red filled circle
        cv2.circle(frame, (center_x, center_y), 35, (255, 255, 255), 3)  # White border
        
        # Draw calibration text
        cv2.putText(frame, "CALIBRATION", (center_x - 100, center_y - 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3, cv2.LINE_AA)
        cv2.putText(frame, "Look at RED DOT", (center_x - 120, center_y + 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Draw countdown if available
        if hasattr(self, 'calibration_remaining'):
            cv2.putText(frame, f"{self.calibration_remaining:.1f}s", (center_x - 30, center_y + 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2, cv2.LINE_AA)
    
    def speak(self, text):
        """Text-to-speech narration with queue system"""
        if self.tts_engine:
            # Add to queue
            self.tts_queue.append(text)
            self._process_tts_queue()
        
        # Also log to results
        self.log_result(f"🔊 {text}")
    
    def _process_tts_queue(self):
        """Process TTS queue to prevent overlapping speech"""
        if not self.tts_engine or self.tts_speaking or not self.tts_queue:
            return
        
        self.tts_speaking = True
        text = self.tts_queue.pop(0)
        
        def speak_thread():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {e}")
            finally:
                self.tts_speaking = False
                # Process next item in queue
                self.root.after(100, self._process_tts_queue)
        
        threading.Thread(target=speak_thread, daemon=True).start()
    
    def start_test(self):
        """Start the testing sequence"""
        self.current_step = 0
        self.test_results = []
        self.session_start_time = time.time()
        
        self.start_button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.NORMAL)
        
        self.speak("Starting remote gaze testing. Please follow the instructions carefully.")
        
        # Small delay to let user prepare, then start calibration
        self.root.after(1000, self.execute_current_step)
    
    def execute_current_step(self):
        """Execute the current test step"""
        if self.current_step >= len(self.test_steps):
            self.complete_test()
            return
        
        step = self.test_steps[self.current_step]
        self.step_start_time = time.time()
        
        # Update UI
        self.step_label.config(text=f"Step {self.current_step + 1}/{len(self.test_steps)}: {step['name']}")
        self.instruction_label.config(text=step['instruction'])
        self.progress_var.set(0)
        
        # Update large instruction display
        instruction_text = f"STEP {self.current_step + 1}/{len(self.test_steps)}\n\n{step['name'].upper()}\n\n{step['instruction']}"
        self.instruction_display.config(text=instruction_text)
        
        # Speak instruction
        self.speak(step['instruction'])
        
        # Add delay for reading instructions before starting detection
        if step['type'] == 'calibration':
            self.root.after(3000, self.execute_calibration_step)  # 3 second delay
        else:
            self.root.after(3000, lambda: self.execute_gaze_step(step))  # 3 second delay
    
    def execute_calibration_step(self):
        """Execute calibration step using our own camera feed"""
        def calibration_thread():
            try:
                self.log_result("🎯 Starting calibration...")
                self.speak("Starting calibration. Look at the center of the screen for 5 seconds.")
                
                # Set calibrating flag for visual overlay
                self.calibrating = True
                
                # Use our own camera feed for calibration
                calibration_frames = []
                calibration_duration = 5.0  # 5 seconds
                calibration_start_time = time.time()
                
                # Show calibration instructions
                self.log_result("CALIBRATION: Look at center of screen for 5 seconds...")
                
                # Wait for calibration duration
                while time.time() - calibration_start_time < calibration_duration:
                    ret, frame = self.cap.read()
                    if ret:
                        # Process frame for calibration
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        results = self.face_mesh.process(frame_rgb)
                        
                        if results.multi_face_landmarks:
                            landmarks = results.multi_face_landmarks[0]
                            h, w = frame.shape[:2]
                            avg_pupil_y, forehead_y, chin_y, pupil_relative, is_blinking = self.face_landmarks.get_gaze_metrics(landmarks, w, h)
                            if pupil_relative is not None:
                                calibration_frames.append(pupil_relative)
                        
                        # Show countdown
                        remaining = calibration_duration - (time.time() - calibration_start_time)
                        self.calibration_remaining = remaining
                        self.log_result(f"CALIBRATION: Look at center - {remaining:.1f}s remaining")
                        
                        time.sleep(0.1)
                
                # Clear calibrating flag
                self.calibrating = False
                
                # Calculate baseline from calibration data
                if calibration_frames:
                    baseline = sum(calibration_frames) / len(calibration_frames)
                    self.gaze_detector.baseline_y = baseline
                    self.log_result(f"✅ Calibration complete! Baseline: {baseline:.3f} (from {len(calibration_frames)} frames)")
                    self.speak("Calibration complete")
                    
                    # Record result
                    self.test_results.append({
                        'step': self.current_step,
                        'name': self.test_steps[self.current_step]['name'],
                        'success': True,
                        'duration': time.time() - self.step_start_time,
                        'baseline': baseline
                    })
                    
                    # Automatically move to next step after calibration
                    self.root.after(2000, self.next_step)
                else:
                    self.log_result("❌ Calibration failed - no valid frames captured")
                    self.speak("Calibration failed, please try again")
                
            except Exception as e:
                self.calibrating = False
                self.log_result(f"❌ Calibration error: {e}")
                self.speak("Calibration error occurred")
        
        threading.Thread(target=calibration_thread, daemon=True).start()
    
    def execute_gaze_step(self, step):
        """Execute a gaze detection step"""
        self.step_data = {
            'step_type': step['type'],
            'target_direction': step['type'].split('_')[0].upper() if '_' in step['type'] else 'NEUTRAL',
            'duration': step.get('duration', 3),
            'detections': [],
            'start_time': time.time()
        }
        
        self.log_result(f"🧪 Starting {step['name']} test...")
    
    def process_test_step(self, gaze_result):
        """Process gaze result for current test step"""
        if self.current_step >= len(self.test_steps) or not hasattr(self, 'step_data'):
            return
        
        current_time = time.time()
        elapsed = current_time - self.step_start_time
        step = self.test_steps[self.current_step]
        
        # Update progress bar
        if 'duration' in step:
            progress = min(100, (elapsed / step['duration']) * 100)
            self.progress_var.set(progress)
        
        # Record gaze data
        if gaze_result and hasattr(self, 'step_data'):
            detection_data = {
                'timestamp': current_time,
                'elapsed': elapsed,
                'direction': gaze_result.get('direction'),
                'is_continuous': gaze_result.get('is_continuous_gaze', False),
                'offset': gaze_result.get('offset', 0)
            }
            self.step_data['detections'].append(detection_data)
        
        # Check step completion
        if hasattr(self, 'step_data') and 'duration' in step:
            if elapsed >= step['duration']:
                self.complete_current_step()
    
    def complete_current_step(self):
        """Complete the current test step and analyze results"""
        if not hasattr(self, 'step_data'):
            return
        
        step = self.test_steps[self.current_step]
        duration = time.time() - self.step_start_time
        
        # Analyze results based on step type
        success = self.analyze_step_results(step, self.step_data)
        
        # Record result
        result = {
            'step': self.current_step,
            'name': step['name'],
            'success': success,
            'duration': duration,
            'detections': len(self.step_data['detections']),
            'data': self.step_data
        }
        self.test_results.append(result)
        
        # Update UI
        status = "✅ PASSED" if success else "❌ FAILED"
        self.log_result(f"{status} {step['name']} - Duration: {duration:.1f}s")
        
        # Handle retry logic
        if not success and self.step_retry_count < self.max_retries:
            # Retry the step
            self.step_retry_count += 1
            self.speak(f"Step failed. Retrying attempt {self.step_retry_count} of {self.max_retries}")
            
            # Update instruction display for retry
            retry_text = f"❌ STEP FAILED - RETRY {self.step_retry_count}/{self.max_retries}\n\n{step['name'].upper()}\n\n{step['instruction']}\n\nTry again in 3 seconds..."
            self.instruction_display.config(text=retry_text, fg="white", bg="red")
            
            # Clean up step data and retry after 3 seconds
            delattr(self, 'step_data')
            self.root.after(3000, self.execute_current_step)
        else:
            # Step passed or max retries reached
            if success:
                self.speak("Step passed")
                self.step_retry_count = 0  # Reset retry count
            else:
                self.speak(f"Step failed after {self.max_retries} attempts. Moving to next step.")
                self.step_retry_count = 0  # Reset retry count
            
            # Clean up step data
            delattr(self, 'step_data')
            
            # Automatically move to next step after 2 seconds
            self.root.after(2000, self.next_step)
    
    def analyze_step_results(self, step, step_data):
        """Analyze step results to determine success"""
        detections = step_data['detections']
        if not detections:
            return False
        
        step_type = step['type']
        target_direction = step_data['target_direction']
        
        if step_type in ['up_hold', 'down_hold']:
            # Check if target direction was detected and held
            target_detections = [d for d in detections if d['direction'] == target_direction]
            return len(target_detections) >= 3  # At least 3 detections
        
        elif step_type in ['up_continuous', 'down_continuous']:
            # Check for continuous gaze detection
            continuous_detections = [d for d in detections if d['is_continuous'] and d['direction'] == target_direction]
            return len(continuous_detections) >= 5  # At least 5 continuous detections
        
        elif step_type == 'neutral':
            # Check for minimal false detections
            false_detections = [d for d in detections if d['direction'] in ['UP', 'DOWN']]
            return len(false_detections) < 3  # Less than 3 false detections
        
        elif step_type == 'sequence':
            # Command sequence test - need UP, DOWN, UP, DOWN pattern
            directions = [d['direction'] for d in detections if d['direction']]
            if len(directions) < 4:
                return False
            
            # Look for the pattern UP, DOWN, UP, DOWN
            pattern_found = False
            for i in range(len(directions) - 3):
                if (directions[i] == 'UP' and 
                    directions[i+1] == 'DOWN' and 
                    directions[i+2] == 'UP' and 
                    directions[i+3] == 'DOWN'):
                    pattern_found = True
                    break
            
            return pattern_found
        
        return True
    
    def next_step(self):
        """Move to next test step"""
        self.current_step += 1
        self.step_retry_count = 0  # Reset retry count for new step
        if self.current_step < len(self.test_steps):
            self.execute_current_step()
        else:
            self.complete_test()
    
    def complete_test(self):
        """Complete the entire test and generate report"""
        total_duration = time.time() - self.session_start_time
        passed_steps = sum(1 for result in self.test_results if result['success'])
        success_rate = (passed_steps / len(self.test_results)) * 100 if self.test_results else 0
        
        # Update UI
        self.step_label.config(text="Test Complete!")
        self.instruction_label.config(text=f"Success Rate: {success_rate:.1f}% ({passed_steps}/{len(self.test_results)})")
        self.progress_var.set(100)
        
        self.start_button.config(state=tk.NORMAL)
        self.next_button.config(state=tk.DISABLED)
        
        # Generate report
        self.generate_report()
        
        # Speak completion
        self.speak(f"Test complete. Success rate: {success_rate:.0f} percent")
        
        self.log_result(f"🎉 Test completed! Success rate: {success_rate:.1f}% in {total_duration:.1f}s")
    
    def generate_report(self):
        """Generate detailed test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"gaze_test_report_{timestamp}.json"
        
        # Create readable step summary
        step_summary = []
        for i, result in enumerate(self.test_results):
            step_name = result.get('name', f'Step {i+1}')
            status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
            duration = result.get('duration', 0)
            
            step_info = {
                'step_number': i + 1,
                'name': step_name,
                'status': status,
                'duration_seconds': round(duration, 1)
            }
            
            # Add specific metrics for different test types
            if 'detections' in result:
                step_info['detections_count'] = result['detections']
            
            if 'baseline' in result:
                step_info['calibration_baseline'] = round(result['baseline'], 3)
            
            step_summary.append(step_info)
        
        success_rate = (sum(1 for r in self.test_results if r['success']) / len(self.test_results)) * 100 if self.test_results else 0
        
        report = {
            'test_summary': {
                'total_duration_minutes': round((time.time() - self.session_start_time) / 60, 1),
                'total_steps': len(self.test_steps),
                'completed_steps': len(self.test_results),
                'success_rate_percent': round(success_rate, 1),
                'test_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            'step_results': step_summary,
            'detailed_results': self.test_results,
            'recommendations': self._generate_recommendations(step_summary)
        }
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            self.log_result(f"📊 Report saved: {report_file}")
        except Exception as e:
            self.log_result(f"❌ Could not save report: {e}")
    
    def _generate_recommendations(self, step_summary):
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check calibration quality
        calib_steps = [s for s in step_summary if 'calibration' in s['name'].lower()]
        if calib_steps:
            avg_baseline = sum(s.get('calibration_baseline', 0) for s in calib_steps) / len(calib_steps)
            if avg_baseline < 0.2 or avg_baseline > 0.4:
                recommendations.append("⚠️ Calibration baselines are outside optimal range (0.2-0.4). Consider better lighting or positioning.")
        
        # Check detection accuracy
        detection_steps = [s for s in step_summary if 'detection' in s['name'].lower() or 'gaze' in s['name'].lower()]
        failed_detections = [s for s in detection_steps if 'FAILED' in s['status']]
        if len(failed_detections) > len(detection_steps) * 0.3:
            recommendations.append("⚠️ High failure rate in gaze detection. Consider adjusting gaze thresholds or improving lighting.")
        
        # Check sequence test
        sequence_steps = [s for s in step_summary if 'sequence' in s['name'].lower()]
        if sequence_steps and 'FAILED' in sequence_steps[0]['status']:
            recommendations.append("⚠️ Command sequence test failed. This may indicate timing issues for rapid commands in your app.")
        
        # Overall success rate
        success_rate = sum(1 for s in step_summary if 'PASSED' in s['status']) / len(step_summary) * 100
        if success_rate < 70:
            recommendations.append("⚠️ Overall success rate is low. Consider improving test conditions or gaze detection settings.")
        elif success_rate > 90:
            recommendations.append("✅ Excellent performance! Your gaze tracking system is working very well.")
        
        return recommendations
    
    def toggle_recording(self):
        """Toggle video recording"""
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Start dual video recording"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Video codec and settings
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = 30
            frame_size = (640, 480)
            
            # Raw camera feed
            raw_filename = f"raw_camera_{timestamp}.mp4"
            self.raw_writer = cv2.VideoWriter(raw_filename, fourcc, fps, frame_size)
            
            # Analysis feed with overlays
            analysis_filename = f"analysis_{timestamp}.mp4"
            self.analysis_writer = cv2.VideoWriter(analysis_filename, fourcc, fps, frame_size)
            
            if self.raw_writer.isOpened() and self.analysis_writer.isOpened():
                self.recording = True
                self.record_button.config(text="Stop Recording")
                self.recording_status.config(text="● Recording", fg="green")
                self.log_result(f"🎥 Recording started: {raw_filename}, {analysis_filename}")
                self.speak("Recording started")
            else:
                raise Exception("Could not initialize video writers")
                
        except Exception as e:
            self.log_result(f"❌ Recording error: {e}")
            messagebox.showerror("Recording Error", f"Could not start recording: {e}")
    
    def stop_recording(self):
        """Stop video recording"""
        self.recording = False
        
        if self.raw_writer:
            self.raw_writer.release()
            self.raw_writer = None
        
        if self.analysis_writer:
            self.analysis_writer.release()
            self.analysis_writer = None
        
        self.record_button.config(text="Start Recording")
        self.recording_status.config(text="● Not Recording", fg="red")
        self.log_result("🎥 Recording stopped")
        self.speak("Recording stopped")
    
    def reset_test(self):
        """Reset the test to beginning"""
        self.current_step = 0
        self.test_results = []
        
        self.step_label.config(text="Step 1/12: Initial Calibration")
        self.instruction_label.config(text="Look at the red dot for 5 seconds")
        self.progress_var.set(0)
        
        # Reset instruction display
        self.instruction_display.config(text="Click 'Start Test' to begin remote gaze testing", 
                                       fg="white", bg="darkblue")
        
        self.start_button.config(state=tk.NORMAL)
        self.next_button.config(state=tk.DISABLED)
        
        # Clear results
        self.results_text.delete(1.0, tk.END)
        
        self.log_result("🔄 Test reset")
        
        # Automatically start calibration after reset
        self.speak("Test reset. Starting calibration in 2 seconds.")
        self.root.after(2000, self.start_test)
    
    def log_result(self, message):
        """Log result to the results text area"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.results_text.insert(tk.END, log_message)
        self.results_text.see(tk.END)
        print(log_message.strip())  # Also print to console
    
    def cleanup(self):
        """Cleanup resources"""
        if self.recording:
            self.stop_recording()
        
        if self.cap:
            self.cap.release()
        
        cv2.destroyAllWindows()
    
    def run(self):
        """Run the application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
    
    def on_closing(self):
        """Handle window closing"""
        self.cleanup()
        self.root.destroy()

def main():
    """Main function"""
    try:
        app = RemoteGazeTester()
        app.run()
    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
