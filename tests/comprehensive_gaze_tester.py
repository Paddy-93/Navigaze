#!/usr/bin/env python3
"""
Comprehensive Gaze Testing System
Creates recordings of gaze patterns for testing and validation
"""

import cv2
import tkinter as tk
from tkinter import ttk
import threading
import time
import json
import os
from datetime import datetime
import mediapipe as mp
import numpy as np

# Import our existing components
from eye_tracking.face_landmarks import FaceLandmarks
from eye_tracking.gaze_detector import GazeDetector

# TTS support
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("pyttsx3 not available. Audio narration disabled.")

class ComprehensiveGazeTester:
    def __init__(self, master):
        self.root = master
        self.root.title("Comprehensive Gaze Testing System")
        self.root.geometry("1000x700")
        
        # Center the window on screen
        self.center_window()
        
        # Initialize MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Initialize our gaze detection components
        self.face_landmarks = FaceLandmarks()
        self.gaze_detector = GazeDetector()
        
        # Test configuration - 8 main steps with calibration between each
        self.test_steps = [
            {"name": "Initial Calibration", "instruction": "Look at the red dot for 5 seconds", "type": "calibration"},
            {"name": "Long UP Holds", "instruction": "Look UP until you hear a beep, repeat 3 times", "type": "long_up", "duration": 60, "repetitions": 3, "hold_duration": 5},
            {"name": "Recalibration 1", "instruction": "Look at the red dot for 5 seconds", "type": "calibration"},
            {"name": "Long DOWN Holds", "instruction": "Look DOWN until you hear a beep, repeat 3 times", "type": "long_down", "duration": 60, "repetitions": 3, "hold_duration": 5},
            {"name": "Recalibration 2", "instruction": "Look at the red dot for 5 seconds", "type": "calibration"},
            {"name": "Quick UP Gazes", "instruction": "Look UP quickly 5 times (short gazes)", "type": "quick_up", "duration": 15, "repetitions": 5, "target_count": 5},
            {"name": "Recalibration 3", "instruction": "Look at the red dot for 5 seconds", "type": "calibration"},
            {"name": "Quick DOWN Gazes", "instruction": "Look DOWN quickly 5 times (short gazes)", "type": "quick_down", "duration": 15, "repetitions": 5, "target_count": 5},
            {"name": "Recalibration 4", "instruction": "Look at the red dot for 5 seconds", "type": "calibration"},
            {"name": "Neutral Hold", "instruction": "Hold neutral gaze for 5 seconds", "type": "neutral_hold", "duration": 8, "hold_duration": 5},
            {"name": "Recalibration 5", "instruction": "Look at the red dot for 5 seconds", "type": "calibration"},
            {"name": "UP-DOWN-UP-DOWN Sequence", "instruction": "Perform UP→DOWN→UP→DOWN pattern 3 times", "type": "sequence_udud", "duration": 25, "repetitions": 3, "pattern": ["UP", "DOWN", "UP", "DOWN"]},
            {"name": "Recalibration 6", "instruction": "Look at the red dot for 5 seconds", "type": "calibration"},
            {"name": "DOWN-UP-DOWN-UP Sequence", "instruction": "Perform DOWN→UP→DOWN→UP pattern 3 times", "type": "sequence_dudu", "duration": 25, "repetitions": 3, "pattern": ["DOWN", "UP", "DOWN", "UP"]},
            {"name": "Recalibration 7", "instruction": "Look at the red dot for 5 seconds", "type": "calibration"},
            {"name": "DOWN-DOWN-UP-UP Sequence", "instruction": "Perform DOWN→DOWN→UP→UP pattern 3 times", "type": "sequence_dduu", "duration": 25, "repetitions": 3, "pattern": ["DOWN", "DOWN", "UP", "UP"]}
        ]
        
        # Test state
        self.current_step = 0
        self.test_results = []
        self.session_start_time = None
        self.step_start_time = None
        self.step_retry_count = 0
        self.max_retries = 2
        
        # Session recording directory
        self.session_dir = None
        self.current_step_dir = None
        
        # Camera and recording
        self.cap = None
        self.camera_index = 0
        self.recording = False
        self.raw_writer = None
        self.analysis_writer = None
        
        # Calibration state
        self.calibrating = False
        self.calibration_remaining = 0
        
        # Step tracking
        self.step_data = None
        self.repetition_count = 0
        
        # Continuous gaze progress tracking
        self.progress_timer_active = False
        
        # TTS
        if TTS_AVAILABLE:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_queue = []
            self.tts_speaking = False
        else:
            self.tts_engine = None
            self.tts_queue = []
            self.tts_speaking = False
        
        self.setup_ui()
        self.start_camera()
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """Setup the user interface"""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = tk.Label(main_frame, text="Comprehensive Gaze Testing System", 
                              font=("Arial", 18, "bold"), fg="darkblue")
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Large instruction display (centered)
        instruction_frame = ttk.LabelFrame(main_frame, text="Test Instructions", padding="20")
        instruction_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        instruction_frame.columnconfigure(0, weight=1)
        instruction_frame.rowconfigure(0, weight=1)
        
        self.instruction_display = tk.Label(instruction_frame, 
                                          text="Click 'Start Test' to begin comprehensive gaze testing",
                                          font=("Arial", 24, "bold"),
                                          fg="white", bg="darkblue",
                                          width=50, height=15,
                                          wraplength=800,
                                          justify=tk.CENTER)
        self.instruction_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Control panel
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(1, weight=1)
        
        # Buttons
        self.start_button = ttk.Button(control_frame, text="Start Test", command=self.start_test)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.next_button = ttk.Button(control_frame, text="Next Step", command=self.next_step, state=tk.DISABLED)
        self.next_button.grid(row=0, column=1, padx=(0, 10))
        
        self.reset_button = ttk.Button(control_frame, text="Reset Test", command=self.reset_test)
        self.reset_button.grid(row=0, column=2, padx=(0, 10))
        
        self.record_button = ttk.Button(control_frame, text="Toggle Recording", command=self.toggle_recording)
        self.record_button.grid(row=0, column=3)
        
        # Status display
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        # Step info
        ttk.Label(status_frame, text="Step:").grid(row=0, column=0, sticky=tk.W)
        self.step_label = ttk.Label(status_frame, text=f"Step 1/{len(self.test_steps)}: Initial Calibration")
        self.step_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Progress bar
        ttk.Label(status_frame, text="Progress:").grid(row=1, column=0, sticky=tk.W)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        # Recording status
        ttk.Label(status_frame, text="Recording:").grid(row=2, column=0, sticky=tk.W)
        self.recording_status = tk.Label(status_frame, text="● Not Recording", fg="red")
        self.recording_status.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Results display
        results_frame = ttk.LabelFrame(main_frame, text="Test Results", padding="10")
        results_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        self.results_text = tk.Text(results_frame, height=8, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
    
    def start_camera(self):
        """Initialize camera"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                raise Exception("Could not open camera")
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.log_result("✅ Camera initialized successfully")
            self.update_camera()
            
        except Exception as e:
            self.log_result(f"❌ Camera initialization failed: {e}")
    
    def update_camera(self):
        """Update camera feed and process gaze detection"""
        if not self.cap:
            return
        
        ret, frame = self.cap.read()
        if not ret:
            self.root.after(33, self.update_camera)
            return
        
        # Process frame for gaze detection
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)
        
        # Initialize variables
        avg_pupil_y = None
        gaze_result = None
        
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            h, w = frame.shape[:2]
            
            # Get gaze metrics using our existing components
            avg_pupil_y, forehead_y, chin_y, pupil_relative, is_blinking = self.face_landmarks.get_gaze_metrics(landmarks, w, h)
            
            if pupil_relative is not None:
                # Update gaze detector
                gaze_result = self.gaze_detector.update(pupil_relative, head_moving=False, is_blinking=is_blinking)
                
                # Draw gaze overlay
                self.draw_gaze_overlay(frame, w, h, avg_pupil_y, gaze_result)
        
        # Draw calibration overlay if calibrating
        if self.calibrating:
            self.draw_calibration_overlay(frame, w, h)
        
        # Record frames if recording
        if self.recording and self.raw_writer and self.analysis_writer:
            self.raw_writer.write(frame)
            self.analysis_writer.write(frame)
        
        # Process gaze for current step
        if hasattr(self, 'step_data') and gaze_result:
            # Store last gaze result for status checking
            self.last_gaze_result = gaze_result
            
            # Debug logging for gaze detection
            if gaze_result.get('gaze_detected') or gaze_result.get('is_continuous_gaze'):
                direction = gaze_result.get('direction', 'NONE')
                is_continuous = gaze_result.get('is_continuous_gaze', False)
                gaze_detected = gaze_result.get('gaze_detected', False)
                self.log_result(f"👁️ GAZE: {direction} | continuous: {is_continuous} | detected: {gaze_detected}")
            
            # Handle case where continuous gaze stops (user looked away)
            if not gaze_result.get('is_continuous_gaze', False):
                # Require a brief true neutral (no direction) before allowing next hold
                # This avoids multiple registrations during one long gaze
                neutral_now = gaze_result.get('direction') in (None, '', 'NONE')
                now_ts = time.time()

                if not hasattr(self, '_neutral_start_ts'):
                    self._neutral_start_ts = None

                if neutral_now:
                    # Start or continue neutral timer
                    if self._neutral_start_ts is None:
                        self._neutral_start_ts = now_ts
                else:
                    # Not neutral; reset timer
                    self._neutral_start_ts = None

                # When waiting_for_neutral, only reset after sustained neutral
                if hasattr(self.step_data, 'waiting_for_neutral') and self.step_data['waiting_for_neutral']:
                    NEUTRAL_CONFIRM_SEC = 0.30
                    if self._neutral_start_ts is not None and (now_ts - self._neutral_start_ts) >= NEUTRAL_CONFIRM_SEC:
                        self.log_result("🔄 Neutral confirmed - ready for next hold")
                        self.step_data['waiting_for_neutral'] = False
                        self.step_data['currently_in_long_gaze'] = False
                        self._neutral_start_ts = None
                        # Force immediate progress display update when going neutral
                        self.update_step_progress()
                        self.root.update()  # Force immediate GUI update
            
            self.process_step_gaze(gaze_result)
        
        # Schedule next update
        self.root.after(33, self.update_camera)
    
    def draw_gaze_overlay(self, frame, w, h, avg_pupil_y, gaze_result):
        """Draw gaze detection overlay"""
        if not gaze_result:
            return
        
        # Draw gaze direction
        if gaze_result.get('gaze_detected'):
            direction = gaze_result.get('direction', 'NONE')
            offset = gaze_result.get('offset', 0)
            is_continuous = gaze_result.get('is_continuous_gaze', False)
            
            # Color based on gaze type
            color = (0, 255, 255) if is_continuous else (0, 255, 0)  # Yellow for continuous, green for quick
            
            # Draw direction text
            cv2.putText(frame, f"{direction} ({offset:.3f})", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)
            
            # Draw continuous indicator
            if is_continuous:
                cv2.putText(frame, "CONTINUOUS", (10, 70), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
        
        # Draw pupil position indicator
        if avg_pupil_y is not None:
            pupil_y_pixel = int(avg_pupil_y * h)
            cv2.circle(frame, (w - 50, pupil_y_pixel), 5, (255, 0, 0), -1)
    
    def draw_calibration_overlay(self, frame, w, h):
        """Draw calibration overlay"""
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
            self.tts_queue.append(text)
            self._process_tts_queue()
        
        # Also log to results
        self.log_result(f"🔊 {text}")

    def play_beep_async(self):
        """Play a short beep without blocking UI"""
        def _beep():
            try:
                import os
                if os.name == 'nt':
                    import winsound
                    winsound.Beep(800, 200)
                else:
                    os.system('afplay /System/Library/Sounds/Glass.aiff')
            except Exception:
                print('\a')
        threading.Thread(target=_beep, daemon=True).start()
    
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
    
    def show_calibration_display(self):
        """Show calibration display with red dot on instruction screen"""
        calibration_text = "🔴 CALIBRATION 🔴\n\nLook at the RED DOT below\n\n●\n\nStarting in 5.0 seconds..."
        self.instruction_display.config(text=calibration_text, 
                                       font=("Arial", 28, "bold"),
                                       fg="red", bg="black")
    
    def update_calibration_countdown(self, remaining):
        """Update calibration countdown display"""
        calibration_text = f"🔴 CALIBRATION 🔴\n\nLook at the RED DOT below\n\n●\n\n{remaining:.1f} seconds remaining..."
        self.instruction_display.config(text=calibration_text)
        self.root.update_idletasks()
    
    def log_result(self, message):
        """Log a result to the results display"""
        timestamp = time.strftime("[%H:%M:%S]")
        self.results_text.insert(tk.END, f"{timestamp} {message}\n")
        self.results_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_test(self):
        """Start the comprehensive test sequence"""
        try:
            # Create session directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_dir = f"gaze_recordings/session_{timestamp}"
            os.makedirs(self.session_dir, exist_ok=True)
        except Exception as e:
            self.log_result(f"❌ Error creating session directory: {e}")
            return
        
        self.current_step = 0
        self.test_results = []
        self.session_start_time = time.time()
        self.step_retry_count = 0
        
        self.start_button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.NORMAL)
        
        self.speak("Starting comprehensive gaze testing. Please follow the instructions carefully.")
        self.log_result(f"📁 Session directory created: {self.session_dir}")
        
        # Start first step after delay
        self.root.after(2000, self.execute_current_step)
    
    def execute_current_step(self):
        """Execute the current test step"""
        try:
            if self.current_step >= len(self.test_steps):
                self.complete_test()
                return
            
            step = self.test_steps[self.current_step]
            self.step_start_time = time.time()
            
            # Create step directory
            step_name = step['name'].lower().replace(' ', '_').replace('-', '_')
            self.current_step_dir = os.path.join(self.session_dir, f"step_{self.current_step + 1:02d}_{step_name}")
            os.makedirs(self.current_step_dir, exist_ok=True)
        except Exception as e:
            self.log_result(f"❌ Error in execute_current_step: {e}")
            return
        
        # Update UI
        self.step_label.config(text=f"Step {self.current_step + 1}/{len(self.test_steps)}: {step['name']}")
        self.progress_var.set(0)
        
        # Update instruction display
        instruction_text = f"STEP {self.current_step + 1}/{len(self.test_steps)}\n\n{step['name'].upper()}\n\n{step['instruction']}"
        self.instruction_display.config(text=instruction_text, fg="white", bg="darkblue")
        
        # Speak instruction
        self.speak(step['instruction'])
        
        # Add delay for reading instructions before starting
        if step['type'] == 'calibration':
            self.root.after(3000, self.execute_calibration_step)
        else:
            self.root.after(3000, lambda: self.execute_gaze_step(step))
    
    def execute_calibration_step(self):
        """Execute calibration step"""
        def calibration_thread():
            try:
                self.log_result("🎯 Starting calibration...")
                self.speak("Starting calibration. Look at the center of the screen for 5 seconds.")
                
                # Start recording for this step
                self.start_step_recording()
                
                # Set calibrating flag for visual overlay
                self.calibrating = True
                
                # Show calibration display on instruction screen
                self.show_calibration_display()
                
                # Collect calibration data
                calibration_frames = []
                calibration_duration = 5.0
                calibration_start_time = time.time()
                
                while time.time() - calibration_start_time < calibration_duration:
                    ret, frame = self.cap.read()
                    if ret:
                        # Process frame for gaze detection (background)
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        results = self.face_mesh.process(frame_rgb)
                        
                        if results.multi_face_landmarks:
                            landmarks = results.multi_face_landmarks[0]
                            h, w = frame.shape[:2]
                            avg_pupil_y, forehead_y, chin_y, pupil_relative, is_blinking = self.face_landmarks.get_gaze_metrics(landmarks, w, h)
                            if pupil_relative is not None:
                                calibration_frames.append(pupil_relative)
                        
                        # Record the camera frame
                        if self.recording and self.raw_writer and self.analysis_writer:
                            self.raw_writer.write(frame)
                            # Draw overlay on camera frame for analysis recording
                            self.draw_calibration_overlay(frame, frame.shape[1], frame.shape[0])
                            self.analysis_writer.write(frame)
                    
                    # Update countdown on instruction display
                    remaining = calibration_duration - (time.time() - calibration_start_time)
                    self.update_calibration_countdown(remaining)
                    
                    time.sleep(0.1)  # 10 FPS for UI updates
                
                # Clear calibrating flag
                self.calibrating = False
                
                # Stop recording
                self.stop_step_recording()
                
                # Calculate baseline
                if calibration_frames:
                    baseline = sum(calibration_frames) / len(calibration_frames)
                    self.gaze_detector.baseline_y = baseline
                    self.log_result(f"✅ Calibration complete! Baseline: {baseline:.3f} (from {len(calibration_frames)} frames)")
                    self.speak("Calibration complete")
                    
                    # Reset instruction display
                    self.instruction_display.config(text="✅ Calibration Complete!\n\nMoving to next step...", 
                                                   font=("Arial", 24, "bold"),
                                                   fg="white", bg="green")
                    
                    # Record result
                    self.test_results.append({
                        'step': self.current_step,
                        'name': self.test_steps[self.current_step]['name'],
                        'success': True,
                        'duration': time.time() - self.step_start_time,
                        'baseline': baseline
                    })
                    
                    # Move to next step
                    self.root.after(2000, self.next_step)
                else:
                    self.log_result("❌ Calibration failed - no valid frames captured")
                    self.speak("Calibration failed, please try again")
                    
                    # Reset instruction display
                    self.instruction_display.config(text="❌ Calibration Failed\n\nPlease try again...", 
                                                   font=("Arial", 24, "bold"),
                                                   fg="white", bg="red")
                
            except Exception as e:
                self.calibrating = False
                self.stop_step_recording()
                self.log_result(f"❌ Calibration error: {e}")
                self.speak("Calibration error occurred")
        
        threading.Thread(target=calibration_thread, daemon=True).start()
    
    def execute_gaze_step(self, step):
        """Execute a gaze detection step"""
        self.log_result(f"🧪 Starting {step['name']} test...")
        
        # Initialize step data
        self.step_data = {
            'detections': [],
            'start_time': time.time(),
            'step_type': step['type'],
            'repetitions_completed': 0,
            'target_repetitions': step.get('repetitions', 1)
        }
        
        # Start recording for this step
        self.start_step_recording()
        
        # Set timer for step duration
        duration = step.get('duration', 10)
        self.root.after(duration * 1000, self.complete_current_step)
    
    def process_step_gaze(self, gaze_result):
        """Process gaze detection for current step"""
        if not hasattr(self, 'step_data') or not self.step_data:
            return
        
        # Process both new gaze detections and continuous gaze states
        direction = gaze_result.get('direction')
        is_continuous = gaze_result.get('is_continuous_gaze', False)
        gaze_detected = gaze_result.get('gaze_detected', False)
        
        # Debug: Print all gaze results to console (disabled for production)
        # if direction:
        #     print(f"[DEBUG] GAZE: {direction} | continuous: {is_continuous} | detected: {gaze_detected} | offset: {gaze_result.get('offset', 0):.3f}")
        
        # Handle neutral gaze (no direction) - reset hold tracking
        if not direction and hasattr(self, 'step_data') and self.step_data:
            step = self.test_steps[self.current_step]
            if step['type'] in ['long_up', 'long_down']:
                if 'current_gaze_state' in self.step_data and self.step_data['current_gaze_state']:
                    self.step_data['current_gaze_state'] = None
                    self.step_data['hold_start_time'] = None
                    self.log_result("🔄 Gaze neutral - reset hold tracking")
        
        # Process gaze results if we have a direction OR if we're already tracking a hold
        if direction or (hasattr(self, 'step_data') and self.step_data and 
                        'current_gaze_state' in self.step_data and 
                        self.step_data.get('current_gaze_state')):
            if direction:  # Only process if we have a valid direction
                detection = {
                    'timestamp': time.time() - self.step_data['start_time'],
                    'direction': direction,
                    'offset': gaze_result.get('offset', 0),
                    'is_continuous': is_continuous
                }
                
                # Check if we're in a long hold step
                step = self.test_steps[self.current_step]
                if step['type'] in ['long_up', 'long_down']:
                    required_duration = step.get('hold_duration', 5)  # Default 5 seconds
                    target_direction = 'UP' if step['type'] == 'long_up' else 'DOWN'
                    
                    # Initialize tracking variables (only once)
                    if 'current_gaze_state' not in self.step_data:
                        self.step_data['current_gaze_state'] = None
                    if 'hold_start_time' not in self.step_data:
                        self.step_data['hold_start_time'] = None
                    
                    # Track gaze state changes (like the main script does)
                    if direction == target_direction:
                        # We're looking in the target direction
                        if self.step_data['current_gaze_state'] != target_direction:
                            # New gaze detected - record start time
                            self.step_data['current_gaze_state'] = target_direction
                            self.step_data['hold_start_time'] = time.time()
                            self.log_result(f"🎯 Started {target_direction} gaze - hold for {required_duration}s")
                        elif self.step_data['current_gaze_state'] == target_direction:
                            # Continuing the same gaze - check duration
                            if self.step_data['hold_start_time']:
                                hold_duration = time.time() - self.step_data['hold_start_time']
                                
                                # Only log every 0.5 seconds to avoid spam
                                if not hasattr(self.step_data, 'last_log_time') or time.time() - self.step_data['last_log_time'] > 0.5:
                                    self.log_result(f"⏱️ HOLDING {target_direction}: {hold_duration:.1f}s / {required_duration}s")
                                    self.step_data['last_log_time'] = time.time()
                                
                                # Check if hold duration is met
                                if hold_duration >= required_duration:
                                    # Register this hold completion
                                    detection['hold_duration'] = hold_duration
                                    self.step_data['detections'].append(detection)
                                    
                                    # Reset tracking to prevent multiple registrations
                                    self.step_data['current_gaze_state'] = None
                                    self.step_data['hold_start_time'] = None
                                    
                                    self.log_result(f"✅ LONG {target_direction} hold completed ({hold_duration:.1f}s)")
                                    
                                    # Update UI and beep
                                    def _on_hold_complete():
                                        self.update_step_progress()
                                        self.play_beep_async()
                                    self.root.after_idle(_on_hold_complete)
                    else:
                        # Looking in wrong direction - reset tracking
                        if self.step_data['current_gaze_state'] == target_direction:
                            self.step_data['current_gaze_state'] = None
                            self.step_data['hold_start_time'] = None
                            self.log_result(f"🔄 Gaze changed to {direction} - reset hold tracking")
            else:
                # No direction in this frame, but we might be tracking a hold
                if ('current_gaze_state' in self.step_data and 
                    self.step_data['current_gaze_state'] and
                    'hold_start_time' in self.step_data and 
                    self.step_data['hold_start_time']):
                    
                    # Continue tracking the hold even without direction
                    hold_duration = time.time() - self.step_data['hold_start_time']
                    
                    # Only log every 0.5 seconds to avoid spam
                    if not hasattr(self.step_data, 'last_log_time') or time.time() - self.step_data['last_log_time'] > 0.5:
                        self.log_result(f"⏱️ HOLDING {self.step_data['current_gaze_state']}: {hold_duration:.1f}s / {required_duration}s")
                        self.step_data['last_log_time'] = time.time()
                    
                    # Check if hold duration is met
                    if hold_duration >= required_duration:
                        # Register this hold completion
                        detection = {
                            'timestamp': time.time() - self.step_data['start_time'],
                            'direction': self.step_data['current_gaze_state'],
                            'offset': 0,  # No offset available
                            'is_continuous': True,
                            'hold_duration': hold_duration
                        }
                        self.step_data['detections'].append(detection)
                        
                        # Reset tracking to prevent multiple registrations
                        self.step_data['current_gaze_state'] = None
                        self.step_data['hold_start_time'] = None
                        
                        self.log_result(f"✅ LONG {self.step_data['current_gaze_state']} hold completed ({hold_duration:.1f}s)")
                        
                        # Update UI and beep
                        def _on_hold_complete():
                            self.update_step_progress()
                            self.play_beep_async()
                        self.root.after_idle(_on_hold_complete)
                else:
                    # For non-long-hold steps, use the original logic
                    if is_continuous:
                        # For continuous gaze, check if we already registered this one recently
                        recent_continuous = [d for d in self.step_data['detections'] 
                                           if d['direction'] == direction and d['is_continuous'] 
                                           and (detection['timestamp'] - d['timestamp']) < 2.0]
                        
                        if not recent_continuous:
                            self.step_data['detections'].append(detection)
                            self.log_result(f"🔄 CONTINUOUS {direction} gaze registered")
                    else:
                        # Quick gaze - always add
                        self.step_data['detections'].append(detection)
                        self.log_result(f"⚡ QUICK {direction} gaze registered")
                
                # Update progress and check for completion
                self.update_step_progress()
                
                # Check if step is complete and auto-advance
                if self.check_step_completion():
                    self.log_result("🎯 Step target reached! Auto-advancing...")
                    # Cancel the timer and complete step immediately
                    self.complete_current_step()
    
    def update_step_progress(self):
        """Update progress for current step with detailed counts"""
        if not hasattr(self, 'step_data') or not self.step_data:
            return
        
        step = self.test_steps[self.current_step]
        detections = self.step_data['detections']
        
        if step['type'] in ['quick_up', 'quick_down']:
            # Count quick gazes
            target_direction = 'UP' if step['type'] == 'quick_up' else 'DOWN'
            count = len([d for d in detections if d['direction'] == target_direction and not d['is_continuous']])
            target = step.get('target_count', 5)
            progress = min(100, (count / target) * 100)
            self.progress_var.set(progress)
            
            # Update instruction display with progress
            direction_name = target_direction.lower()
            progress_text = f"STEP {self.current_step + 1}/{len(self.test_steps)}\n\n{step['name'].upper()}\n\n{direction_name.upper()} gazes: {count}/{target}\n\n{step['instruction']}"
            self.instruction_display.config(text=progress_text, fg="white", bg="darkblue")
            
        elif step['type'] in ['long_up', 'long_down']:
            # Count long holds (only completed ones with hold_duration)
            target_direction = 'UP' if step['type'] == 'long_up' else 'DOWN'
            count = len([d for d in detections if d['direction'] == target_direction and d.get('hold_duration', 0) > 0])
            target = step.get('repetitions', 3)
            progress = min(100, (count / target) * 100)
            self.progress_var.set(progress)
            
            # Check if we're currently holding
            currently_holding = False
            hold_duration = 0
            if ('current_gaze_state' in self.step_data and 
                self.step_data['current_gaze_state'] == target_direction and
                'hold_start_time' in self.step_data and 
                self.step_data['hold_start_time']):
                currently_holding = True
                hold_duration = time.time() - self.step_data['hold_start_time']
            
            # Update instruction display with progress and status
            direction_name = target_direction.lower()
            status_line = ""
            if count >= target:
                status_line = "\n✅ STEP COMPLETE!"
            elif currently_holding:
                required_duration = step.get('hold_duration', 5)
                status_line = f"\n🔄 Holding {direction_name.upper()} gaze... {hold_duration:.1f}s / {required_duration}s"
            else:
                status_line = f"\n👁️ Ready - Look {direction_name.upper()} until you hear a beep"
            
            progress_text = f"STEP {self.current_step + 1}/{len(self.test_steps)}\n\n{step['name'].upper()}\n\nLong {direction_name.upper()} holds: {count}/{target}\n\n{step['instruction']}{status_line}"
            self.instruction_display.config(text=progress_text, fg="white", bg="darkblue")
            
        elif step['type'] == 'neutral_hold':
            # Count false detections (fewer is better)
            false_detections = len([d for d in detections if d['direction'] in ['UP', 'DOWN']])
            elapsed_time = time.time() - self.step_data['start_time']
            target_duration = step.get('hold_duration', 5)
            
            # Progress based on time elapsed
            progress = min(100, (elapsed_time / target_duration) * 100)
            self.progress_var.set(progress)
            
            # Update instruction display with progress
            progress_text = f"STEP {self.current_step + 1}/{len(self.test_steps)}\n\n{step['name'].upper()}\n\nTime: {elapsed_time:.1f}/{target_duration}s\nFalse detections: {false_detections}\n\n{step['instruction']}"
            self.instruction_display.config(text=progress_text, fg="white", bg="darkblue")
            
        elif step['type'].startswith('sequence_'):
            # Count completed sequences
            directions = [d['direction'] for d in detections if d['direction']]
            pattern = step.get('pattern', [])
            repetitions = step.get('repetitions', 3)
            
            # Count how many complete patterns we've found
            found_patterns = 0
            for i in range(len(directions) - len(pattern) + 1):
                if directions[i:i+len(pattern)] == pattern:
                    found_patterns += 1
            
            progress = min(100, (found_patterns / repetitions) * 100)
            self.progress_var.set(progress)
            
            # Update instruction display with progress
            pattern_str = "→".join(pattern)
            progress_text = f"STEP {self.current_step + 1}/{len(self.test_steps)}\n\n{step['name'].upper()}\n\n{pattern_str} sequences: {found_patterns}/{repetitions}\n\n{step['instruction']}"
            self.instruction_display.config(text=progress_text, fg="white", bg="darkblue")
    
    def check_step_completion(self):
        """Check if current step is complete and should auto-advance"""
        if not hasattr(self, 'step_data') or not self.step_data:
            return False
        
        step = self.test_steps[self.current_step]
        detections = self.step_data['detections']
        
        if step['type'] in ['quick_up', 'quick_down']:
            # Check if we have enough quick gazes
            target_direction = 'UP' if step['type'] == 'quick_up' else 'DOWN'
            count = len([d for d in detections if d['direction'] == target_direction and not d['is_continuous']])
            target = step.get('target_count', 5)
            return count >= target
            
        elif step['type'] in ['long_up', 'long_down']:
            # Check if we have enough long holds (completed ones with hold_duration)
            target_direction = 'UP' if step['type'] == 'long_up' else 'DOWN'
            count = len([d for d in detections if d['direction'] == target_direction and d.get('hold_duration', 0) > 0])
            target = step.get('repetitions', 3)
            return count >= target
            
        elif step['type'] == 'neutral_hold':
            # Check if we've held neutral long enough
            elapsed_time = time.time() - self.step_data['start_time']
            target_duration = step.get('hold_duration', 5)
            return elapsed_time >= target_duration
            
        elif step['type'].startswith('sequence_'):
            # Check if we have enough completed sequences
            directions = [d['direction'] for d in detections if d['direction']]
            pattern = step.get('pattern', [])
            repetitions = step.get('repetitions', 3)
            
            found_patterns = 0
            for i in range(len(directions) - len(pattern) + 1):
                if directions[i:i+len(pattern)] == pattern:
                    found_patterns += 1
            
            return found_patterns >= repetitions
        
        return False
    
    
    def complete_current_step(self):
        """Complete the current test step"""
        if not hasattr(self, 'step_data'):
            return
        
        # Stop recording
        self.stop_step_recording()
        
        step = self.test_steps[self.current_step]
        duration = time.time() - self.step_start_time
        
        # Analyze results
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
        
        # Handle retry logic or move to next step
        if not success and self.step_retry_count < self.max_retries:
            self.step_retry_count += 1
            self.speak(f"Step failed. Retrying attempt {self.step_retry_count} of {self.max_retries}")
            
            retry_text = f"❌ STEP FAILED - RETRY {self.step_retry_count}/{self.max_retries}\n\n{step['name'].upper()}\n\n{step['instruction']}\n\nTry again in 3 seconds..."
            self.instruction_display.config(text=retry_text, fg="white", bg="red")
            
            delattr(self, 'step_data')
            self.root.after(3000, self.execute_current_step)
        else:
            if success:
                self.speak("Step passed")
                self.step_retry_count = 0
            else:
                self.speak(f"Step failed after {self.max_retries} attempts. Moving to next step.")
                self.step_retry_count = 0
            
            # Process video cuts for hold tests
            if step['type'] in ['long_up', 'long_down', 'neutral_hold']:
                self.create_hold_video_cuts()
            
            delattr(self, 'step_data')
            self.root.after(2000, self.next_step)
    
    def analyze_step_results(self, step, step_data):
        """Analyze step results to determine success"""
        detections = step_data['detections']
        if not detections:
            return False
        
        step_type = step['type']
        
        if step_type == 'quick_up':
            up_detections = [d for d in detections if d['direction'] == 'UP' and not d['is_continuous']]
            return len(up_detections) >= step.get('target_count', 5)
        
        elif step_type == 'quick_down':
            down_detections = [d for d in detections if d['direction'] == 'DOWN' and not d['is_continuous']]
            return len(down_detections) >= step.get('target_count', 5)
        
        elif step_type == 'long_up':
            up_holds = [d for d in detections if d['direction'] == 'UP' and d.get('hold_duration', 0) > 0]
            return len(up_holds) >= step.get('repetitions', 3)
        
        elif step_type == 'long_down':
            down_holds = [d for d in detections if d['direction'] == 'DOWN' and d.get('hold_duration', 0) > 0]
            return len(down_holds) >= step.get('repetitions', 3)
        
        elif step_type == 'neutral_hold':
            false_detections = [d for d in detections if d['direction'] in ['UP', 'DOWN']]
            return len(false_detections) < 3
        
        elif step_type.startswith('sequence_'):
            # Analyze sequence patterns
            directions = [d['direction'] for d in detections if d['direction']]
            pattern = step.get('pattern', [])
            repetitions = step.get('repetitions', 3)
            
            found_patterns = 0
            for i in range(len(directions) - len(pattern) + 1):
                if directions[i:i+len(pattern)] == pattern:
                    found_patterns += 1
            
            return found_patterns >= repetitions
        
        return True
    
    def create_hold_video_cuts(self):
        """Create video cuts for hold tests (1s, 2s, 3s, 5s)"""
        if not self.current_step_dir:
            return
        
        try:
            raw_video_path = os.path.join(self.current_step_dir, "raw_recording.mp4")
            if not os.path.exists(raw_video_path):
                return
            
            # Create cuts for different durations
            durations = [1, 2, 3, 5]
            
            for duration in durations:
                output_path = os.path.join(self.current_step_dir, f"hold_{duration}s_cut.mp4")
                
                # Use ffmpeg to create cut (if available)
                try:
                    import subprocess
                    cmd = [
                        'ffmpeg', '-i', raw_video_path,
                        '-t', str(duration),
                        '-c', 'copy',
                        '-y', output_path
                    ]
                    subprocess.run(cmd, check=True, capture_output=True)
                    self.log_result(f"✂️ Created {duration}s cut: {os.path.basename(output_path)}")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    self.log_result(f"⚠️ Could not create {duration}s cut (ffmpeg not available)")
        
        except Exception as e:
            self.log_result(f"❌ Error creating video cuts: {e}")
    
    def start_step_recording(self):
        """Start recording for current step"""
        if not self.current_step_dir:
            return
        
        try:
            # Setup video writers
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = 30
            frame_size = (640, 480)
            
            raw_path = os.path.join(self.current_step_dir, "raw_recording.mp4")
            analysis_path = os.path.join(self.current_step_dir, "analysis_overlay.mp4")
            
            self.raw_writer = cv2.VideoWriter(raw_path, fourcc, fps, frame_size)
            self.analysis_writer = cv2.VideoWriter(analysis_path, fourcc, fps, frame_size)
            
            self.recording = True
            self.recording_status.config(text="● Recording", fg="green")
            self.log_result(f"🎥 Started recording: {os.path.basename(self.current_step_dir)}")
            
        except Exception as e:
            self.log_result(f"❌ Recording start failed: {e}")
    
    def stop_step_recording(self):
        """Stop recording for current step"""
        if self.raw_writer:
            self.raw_writer.release()
            self.raw_writer = None
        
        if self.analysis_writer:
            self.analysis_writer.release()
            self.analysis_writer = None
        
        self.recording = False
        self.recording_status.config(text="● Not Recording", fg="red")
        
        if self.current_step_dir:
            self.log_result(f"🎬 Stopped recording: {os.path.basename(self.current_step_dir)}")
    
    def next_step(self):
        """Move to next test step"""
        self.current_step += 1
        self.step_retry_count = 0
        
        if self.current_step < len(self.test_steps):
            self.execute_current_step()
        else:
            self.complete_test()
    
    def complete_test(self):
        """Complete the entire test sequence"""
        self.speak("Test sequence complete")
        self.log_result("🎉 Test sequence completed!")
        
        # Generate final report
        self.generate_report()
        
        # Reset UI
        self.start_button.config(state=tk.NORMAL)
        self.next_button.config(state=tk.DISABLED)
        
        self.instruction_display.config(text="Test Complete!\n\nCheck the results below and recordings in the session directory.", 
                                       fg="white", bg="green")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        if not self.session_dir:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.session_dir, f"test_report_{timestamp}.json")
        
        # Create summary
        success_rate = (sum(1 for r in self.test_results if r['success']) / len(self.test_results)) * 100 if self.test_results else 0
        
        report = {
            'test_summary': {
                'total_duration_minutes': round((time.time() - self.session_start_time) / 60, 1),
                'total_steps': len(self.test_steps),
                'completed_steps': len(self.test_results),
                'success_rate_percent': round(success_rate, 1),
                'test_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'session_directory': self.session_dir
            },
            'step_results': self.test_results,
            'recordings': {
                'session_dir': self.session_dir,
                'individual_steps': [f"step_{i+1:02d}_{step['name'].lower().replace(' ', '_')}" 
                                   for i, step in enumerate(self.test_steps) if step['type'] != 'calibration']
            }
        }
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            self.log_result(f"📊 Report saved: {os.path.basename(report_file)}")
        except Exception as e:
            self.log_result(f"❌ Could not save report: {e}")
    
    def reset_test(self):
        """Reset the test to beginning"""
        self.current_step = 0
        self.test_results = []
        self.step_retry_count = 0
        
        self.step_label.config(text=f"Step 1/{len(self.test_steps)}: Initial Calibration")
        self.progress_var.set(0)
        
        self.instruction_display.config(text="Click 'Start Test' to begin comprehensive gaze testing", 
                                       fg="white", bg="darkblue")
        
        self.start_button.config(state=tk.NORMAL)
        self.next_button.config(state=tk.DISABLED)
        
        # Clear results
        self.results_text.delete(1.0, tk.END)
        
        self.log_result("🔄 Test reset")
    
    def toggle_recording(self):
        """Toggle manual recording (for testing)"""
        if not self.recording:
            # Create temporary recording
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_dir = f"gaze_recordings/manual_{timestamp}"
            os.makedirs(temp_dir, exist_ok=True)
            self.current_step_dir = temp_dir
            self.start_step_recording()
        else:
            self.stop_step_recording()
    
    def __del__(self):
        """Cleanup on exit"""
        if self.cap:
            self.cap.release()
        if self.raw_writer:
            self.raw_writer.release()
        if self.analysis_writer:
            self.analysis_writer.release()

def main():
    root = tk.Tk()
    app = ComprehensiveGazeTester(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application interrupted")
    finally:
        if hasattr(app, 'cap') and app.cap:
            app.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
