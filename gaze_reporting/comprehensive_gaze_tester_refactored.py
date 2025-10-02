#!/usr/bin/env python3
"""
Comprehensive Gaze Testing System - Refactored
Uses dependency injection for gaze detection
"""

import cv2
import tkinter as tk
from tkinter import ttk
import threading
import time
import json
import os
import subprocess
import sys
import signal
import atexit
from datetime import datetime
import numpy as np
from typing import Optional, Dict, Any

# Import our gaze detector interface
from gaze_detector_interface import GazeDetectorInterface

# TTS support
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("pyttsx3 not available. Audio narration disabled.")

class ComprehensiveGazeTester:
    def __init__(self, master, gaze_detector: GazeDetectorInterface):
        self.root = master
        self.root.title("Comprehensive Gaze Testing System")
        self.root.geometry("1000x700")
        
        # Store the injected gaze detector
        self.gaze_detector = gaze_detector
        
        # Center the window on screen
        self.center_window()
        
        # Initialize video recording
        self.cap = None
        self.raw_writer = None
        self.analysis_writer = None
        self.recording = True  # Enable recording by default
        self.session_dir = None
        
        # Test state
        self.test_running = False
        self.current_step = 0
        self.step_data = None
        self.step_start_time = 0
        self.test_results = []
        
        # TTS
        self.tts_engine = None
        self.tts_queue = []
        self.tts_speaking = False
        self.tts_callbacks = []  # Store callbacks to execute after TTS completes
        self.max_tts_length = 200  # Maximum characters for TTS
        self.tts_timeout_timer = None  # Timeout for TTS operations
        
        # Recording ready flag
        self.recording_ready = False
        
        # Gaze detection blocking flag
        self.allow_gaze_detection = False
        
        # Step delays removed - now using actual TTS timing
                # Test steps definition - full comprehensive test
        self.test_steps = [
            {
                'name': 'Initial Calibration',
                'type': 'calibration',
                'instruction': 'Look at the red dot and keep your head still. Wait for the beep to begin.'
            },
            {
                'name': 'UP-DOWN-UP-DOWN Sequence',
                'type': 'sequence_up_down_up_down',
                'instruction': 'Look UP, then DOWN, then UP, then DOWN as fast as you can. Repeat 3 times. Wait for the beep to begin.',
                'pattern': ['UP', 'DOWN', 'UP', 'DOWN'],
                'repetitions': 3,
                'duration': 60.0
            },
            {
                'name': 'Quick UP Gazes',
                'type': 'quick_up',
                'instruction': 'Look UP 5 times as fast as you can. Wait for the beep to begin.',
                'repetitions': 5,
                'duration': 30.0
            },
            {
                'name': 'Calibration',
                'type': 'calibration',
                'instruction': 'Look at the red dot and keep your head still. Wait for the beep to begin.'
            },
            {
                'name': 'Quick DOWN Gazes',
                'type': 'quick_down',
                'instruction': 'Look DOWN 5 times as fast as you can. Wait for the beep to begin.',
                'repetitions': 5,
                'duration': 30.0
            },
            {
                'name': 'Calibration',
                'type': 'calibration',
                'instruction': 'Look at the red dot and keep your head still. Wait for the beep to begin.'
            },
            {
                'name': 'DOWN-DOWN-UP-UP Sequence',
                'type': 'sequence_down_down_up_up',
                'instruction': 'Look DOWN twice, then UP twice as fast as you can. Repeat 3 times. Wait for the beep to begin.',
                'pattern': ['DOWN', 'DOWN', 'UP', 'UP'],
                'repetitions': 3,
                'duration': 60.0
            },
            {
                'name': 'Calibration',
                'type': 'calibration',
                'instruction': 'Look at the red dot. Wait for the beep to begin.'
            },
            {
                'name': 'DOWN-UP-DOWN-UP Sequence',
                'type': 'sequence_down_up_down_up',
                'instruction': 'Look DOWN, then UP, then DOWN, then UP as fast as you can. Repeat 3 times. Wait for the beep to begin.',
                'pattern': ['DOWN', 'UP', 'DOWN', 'UP'],
                'repetitions': 3,
                'duration': 60.0
            },
            {
                'name': 'Calibration',
                'type': 'calibration',
                'instruction': 'Look at the red dot and keep your head still. Wait for the beep to begin.'
            },
            {
                'name': 'Long DOWN Holds',
                'type': 'long_down',
                'instruction': 'Look DOWN until you hear a beep, then return to neutral. Repeat 3 times. Wait for the beep to begin.',
                'repetitions': 3,
                'hold_duration': 5,
                'duration': 160.0
            },
            {
                'name': 'Calibration',
                'type': 'calibration',
                'instruction': 'Look at the red dot and keep your head still. Wait for the beep to begin.'
            },
            {
                'name': 'Long UP Holds',
                'type': 'long_up',
                'instruction': 'Look UP until you hear a beep, then return to neutral. Repeat 3 times. Wait for the beep to begin.',
                'repetitions': 3,
                'hold_duration': 5,
                'duration': 160.0
            },
        ]
        
        # Initialize TTS
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 150)
                self.tts_engine.setProperty('volume', 1.0)
                print("[OK] TTS engine initialized")
                
                # Warm up TTS engine to prevent first-call issues
                try:
                    print("[INFO] Warming up TTS engine...")
                    self.tts_engine.say("TTS ready")
                    self.tts_engine.runAndWait()
                    print("[OK] TTS engine warmed up successfully")
                except Exception as e:
                    print(f"[WARN] TTS warm-up failed: {e}")
                
                # Test TTS after a short delay
                self.root.after(1000, self.test_tts)
            except Exception as e:
                print(f"[ERROR] Failed to initialize TTS: {e}")
                self.tts_engine = None
        
        # Setup UI
        self.setup_ui()
        
        # Initialize gaze detector with more aggressive settings for testing
        if not self.gaze_detector.initialize():
            print("[ERROR] Failed to initialize gaze detector")
            return
        
        # Make gaze detection more aggressive for testing
        if hasattr(self.gaze_detector, 'gaze_detector') and self.gaze_detector.gaze_detector:
            # Reduce thresholds for more sensitive detection
            self.gaze_detector.gaze_detector.threshold_up = 0.01    # More sensitive (was 0.012)
            self.gaze_detector.gaze_detector.threshold_down = 0.007  # More sensitive (was 0.005)
            self.gaze_detector.gaze_detector.cooldown_ms = 100       # Faster detection (was 200)
            
            # Make continuous gaze detection more aggressive
            if hasattr(self.gaze_detector.gaze_detector, 'hold_threshold_ms'):
                self.gaze_detector.gaze_detector.hold_threshold_ms = 500  # Faster long gaze detection (was 1000)
            if hasattr(self.gaze_detector.gaze_detector, 'repeat_rate_ms'):
                self.gaze_detector.gaze_detector.repeat_rate_ms = 200     # Faster continuous firing (was 250)
            
            print("[INFO] Test mode: More aggressive gaze detection enabled")
        
        # Set up signal handlers for graceful shutdown
        self.setup_signal_handlers()
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
        # Start camera update loop
        self.start_camera()
    
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"\n🛑 Received signal {signum}, attempting graceful shutdown...")
            self.attempt_upload_on_exit()
            sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
        
        # Register cleanup function for normal exit
        atexit.register(self.attempt_upload_on_exit)
    
    def on_closing(self):
        """Handle window close event"""
        print("\n🛑 Window closing, attempting upload...")
        self.attempt_upload_on_exit()
        self.root.destroy()
    
    def safe_after(self, delay_ms, callback, *args):
        """Safely schedule a callback with error handling"""
        try:
            if self.root.winfo_exists():
                return self.root.after(delay_ms, callback, *args)
        except tk.TclError:
            # Window was destroyed, ignore
            pass
        return None
    
    # get_step_delay method removed - now using actual TTS timing
        
    def center_window(self):
        """Center the window on screen and force to front"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Force window to front with multiple methods
        self.root.lift()
        self.root.focus_force()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
        
        # Additional methods to ensure it comes to front
        self.root.after(200, self._force_to_front)
    
    def _force_to_front(self):
        """Additional method to force window to front"""
        self.root.lift()
        self.root.focus_force()
        self.root.attributes('-topmost', True)
        self.root.after(50, lambda: self.root.attributes('-topmost', False))
        
        # Try macOS-specific method to bring to front
        try:
            import subprocess
            subprocess.run(['osascript', '-e', 'tell application "Python" to activate'], 
                         capture_output=True, timeout=1)
        except:
            pass  # Ignore if osascript fails
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Comprehensive Gaze Testing System", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Instruction display
        self.instruction_display = tk.Label(main_frame, 
                                          text="STARTING...\n\nInitializing comprehensive gaze testing system\n\nPlease wait...",
                                          font=("Arial", 14),
                                          fg="white", bg="darkblue",
                                          width=60, height=8,
                                          wraplength=500)
        self.instruction_display.grid(row=1, column=0, columnspan=2, pady=(0, 20), sticky=(tk.W, tk.E))
        
        # Auto-start after 3 seconds
        self.root.after(3000, self.auto_start_test)
        
        # Hidden start button for automated testing
        self.start_button = ttk.Button(main_frame, text="Start Test", command=self.start_test)
        # Don't grid it - it's hidden but can be invoked programmatically
        
        # Status labels (minimal)
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.grid(row=0, column=0, padx=(0, 20))
        
        self.recording_label = ttk.Label(status_frame, text="Not Recording")
        self.recording_label.grid(row=0, column=1)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Results text area (minimal for now)
        results_frame = ttk.LabelFrame(main_frame, text="Test Log", padding="5")
        results_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        self.results_text = tk.Text(results_frame, height=6, width=80)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
    def start_camera(self):
        """Start the camera update loop"""
        self.update_camera()
        
    def update_camera(self):
        """Update camera and process gaze detection"""
        if self.gaze_detector.is_ready():
            # Get gaze result from the injected detector
            gaze_result = self.gaze_detector.update()
            
            if gaze_result:
                # Process gaze for current step if test is running
                if self.test_running and hasattr(self, 'step_data') and self.step_data:
                    self.process_step_gaze(gaze_result)
                
                # Record video frames if recording
                if self.recording and hasattr(self, 'raw_video_writer') and self.raw_video_writer:
                    self.record_video_frames(gaze_result)
        
        # Schedule next update (only if window still exists)
        try:
            if self.root.winfo_exists():
                self.root.after(33, self.update_camera)  # ~30 FPS
        except tk.TclError:
            # Window was destroyed, stop updating
            pass
        
    def process_step_gaze(self, gaze_result: Dict[str, Any]):
        """Process gaze detection for current step"""
        if not hasattr(self, 'step_data') or not self.step_data or not self.test_running:
            return
        
        # Block gaze detection until after beep fires
        if not self.allow_gaze_detection:
            return
        
        # Process both new gaze detections and continuous gaze states
        direction = gaze_result.get('direction')
        is_continuous = gaze_result.get('is_continuous_gaze', False)
        gaze_detected = gaze_result.get('gaze_detected', False)
        
        # Check if this is a sequence step
        step = self.test_steps[self.current_step] if hasattr(self, 'current_step') else None
        is_sequence_step = step and step['type'].startswith('sequence_') if step else False
        
        # Debug: Print only detected gazes
        if direction and gaze_detected:
            timestamp = time.time()
            print(f"[DETECT] GAZE DETECTED: {direction} (continuous: {is_continuous})")
            self.log_result(f"[GAZE] GAZE DETECTED: {direction} (continuous: {is_continuous}) at {timestamp:.3f}")
        
        # For sequence steps, only add initial gaze detections (not continuous follow-ups)
        if is_sequence_step and direction and gaze_detected:
            # Initialize gaze sequence if not exists
            if 'gaze_sequence' not in self.step_data:
                self.step_data['gaze_sequence'] = []
                self.step_data['completed_patterns'] = 0
                self.step_data['sequence_start_time'] = time.time()
                self.step_data['current_pattern_start_time'] = time.time()
                self.step_data['pattern_timings'] = []
            
            # Log the gaze
            self.log_result(f"[GAZE] GAZE DETECTED: {direction}")
            
            # Update sequence progress (this will add to sequence)
            self.update_sequence_progress(direction)
            return  # Skip the rest of the processing for sequence steps
        
        # Log every gaze detection to test log for other steps
        if direction and gaze_detected:
            self.log_result(f"[GAZE] GAZE DETECTED: {direction}")
        
        # Handle neutral gaze (no direction) - reset hold tracking
        if not direction and hasattr(self, 'step_data') and self.step_data:
            step = self.test_steps[self.current_step]
            if step['type'] in ['long_up', 'long_down']:
                if 'current_gaze_state' in self.step_data and self.step_data['current_gaze_state']:
                    self.step_data['current_gaze_state'] = None
                    self.step_data['hold_start_time'] = None
                    self.log_result("🔄 Gaze neutral - reset hold tracking")
                
                # Reset waiting for neutral flag to allow next hold
                if self.step_data.get('waiting_for_neutral', False):
                    self.step_data['waiting_for_neutral'] = False
                    self.log_result("🔄 Ready for next hold")
        
        # Process gaze results for new detections and long hold tracking
        step = self.test_steps[self.current_step]
        
        # For long hold steps, process every frame with direction
        if step['type'] in ['long_up', 'long_down'] and direction:
            # Only create detection for new gaze detections, not for continuous tracking
            if gaze_detected:
                current_time = time.time()
                detection = {
                    'timestamp': current_time - self.step_data['start_time'],
                    'absolute_timestamp': current_time,
                    'direction': direction,
                    'offset': gaze_result.get('offset', 0),
                    'is_continuous': is_continuous,
                    'datetime': datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                }
                print(f"[DETECT] CREATED DETECTION: {detection}")
            else:
                detection = None
            
            # Process long hold tracking (always for long hold steps)
            required_duration = step.get('hold_duration', 5)  # Default 5 seconds
            target_direction = 'UP' if step['type'] == 'long_up' else 'DOWN'
            
            # Initialize tracking variables (only once)
            if 'current_gaze_state' not in self.step_data:
                self.step_data['current_gaze_state'] = None
            if 'hold_start_time' not in self.step_data:
                self.step_data['hold_start_time'] = None
            
            # Track gaze state changes (like the main script does)
            if direction == target_direction:
                # Check if we're waiting for neutral before starting new hold
                if self.step_data.get('waiting_for_neutral', False):
                    return  # Skip processing until we get a neutral gaze
                
                # We're looking in the target direction
                if self.step_data['current_gaze_state'] != target_direction:
                    # New gaze detected - record start time
                    self.step_data['current_gaze_state'] = target_direction
                    self.step_data['hold_start_time'] = time.time()
                    self.log_result(f"[HOLD] Started {target_direction} gaze - hold for {required_duration}s")
                elif self.step_data['current_gaze_state'] == target_direction:
                    # Continuing the same gaze - check duration
                    if self.step_data['hold_start_time']:
                        hold_duration = time.time() - self.step_data['hold_start_time']
                        
                        # Only log every 0.5 seconds to avoid spam
                        if 'last_log_time' not in self.step_data or time.time() - self.step_data['last_log_time'] > 0.5:
                            self.log_result(f"[HOLD] HOLDING {target_direction}: {hold_duration:.1f}s / {required_duration}s")
                            self.step_data['last_log_time'] = time.time()
                        
                        # Check if hold duration is met
                        if hold_duration >= required_duration:
                            # Register this hold completion
                            if detection:
                                detection['hold_duration'] = hold_duration
                                self.step_data['detections'].append(detection)
                            else:
                                # Create a detection for the hold completion
                                current_time = time.time()
                                hold_detection = {
                                    'timestamp': current_time - self.step_data['start_time'],
                                    'absolute_timestamp': current_time,
                                    'direction': direction,
                                    'offset': gaze_result.get('offset', 0),
                                    'is_continuous': is_continuous,
                                    'hold_duration': hold_duration,
                                    'datetime': datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                                }
                                self.step_data['detections'].append(hold_detection)
                            
                            # Reset tracking to prevent multiple registrations
                            self.step_data['current_gaze_state'] = None
                            self.step_data['hold_start_time'] = None
                            
                            # Set a flag to wait for neutral before next hold
                            self.step_data['waiting_for_neutral'] = True
                            
                            self.log_result(f"[SUCCESS] LONG {target_direction} hold completed ({hold_duration:.1f}s)")
                            
                            # Update UI and beep
                            def _on_hold_complete():
                                self.update_step_progress()
                                self.root.update()
                                self.play_beep_async()
                            
                            self.root.after(0, _on_hold_complete)
            else:
                # Looking in wrong direction - reset tracking
                if self.step_data['current_gaze_state'] == target_direction:
                    self.step_data['current_gaze_state'] = None
                    self.step_data['hold_start_time'] = None
                    self.log_result(f"🔄 Gaze changed to {direction} - reset hold tracking")
        
        # For other step types, only process new gaze detections
        elif direction and gaze_detected:
            current_time = time.time()
            detection = {
                'timestamp': current_time - self.step_data['start_time'],
                'absolute_timestamp': current_time,
                'direction': direction,
                'offset': gaze_result.get('offset', 0),
                'is_continuous': is_continuous,
                'datetime': datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            }
            print(f"[DETECT] CREATED DETECTION: {detection}")
            
            # Add the detection
            self.step_data['detections'].append(detection)
            print(f"[DETECT] ADDED DETECTION: {detection}")
            self.log_result(f"[GAZE] {direction} gaze registered at {detection['datetime']}")
            
            # Check if this is a sequence step
            is_sequence_step = step['type'].startswith('sequence_')
            
            # Update sequence progress for sequence steps
            if is_sequence_step:
                self.update_sequence_progress(direction)
        
        # Update progress and check for completion (for all step types)
        if direction:  # Only update if we have a direction
            self.update_step_progress()
            
            # Check if step is complete and auto-advance
            if self.check_step_completion():
                self.log_result("[ADVANCE] Step target reached! Auto-advancing...")
                # Cancel the timer and complete step immediately
                self.complete_current_step()
    
    def update_sequence_progress(self, direction):
        """Update sequence progress display for sequence steps"""
        if not hasattr(self, 'step_data') or not self.step_data:
            return
            
        step = self.test_steps[self.current_step]
        if not step['type'].startswith('sequence_'):
            return
            
        # Initialize sequence tracking if not exists
        if 'gaze_sequence' not in self.step_data:
            self.step_data['gaze_sequence'] = []
            self.step_data['completed_patterns'] = 0
            self.step_data['sequence_start_time'] = time.time()  # Track when sequence started
            self.step_data['current_pattern_start_time'] = time.time()  # Track when current pattern started
            self.step_data['pattern_timings'] = []  # Initialize pattern timings list
            
        pattern = step.get('pattern', [])
        repetitions = step.get('repetitions', 3)
        
        # Add current direction to sequence with timing
        current_time = time.time()
        gaze_entry = {
            'direction': direction,
            'timestamp': current_time - self.step_data['start_time'],
            'absolute_timestamp': current_time,
            'datetime': datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        }
        self.step_data['gaze_sequence'].append(gaze_entry)
        current_seq = [g['direction'] for g in self.step_data['gaze_sequence']]  # Extract just directions for pattern matching
        
        # Check for immediate mismatch - if current direction doesn't match expected pattern position
        if len(current_seq) <= len(pattern):
            expected_direction = pattern[len(current_seq) - 1]
            if direction != expected_direction:
                # Immediate mismatch - reset sequence with current direction
                self.step_data['gaze_sequence'] = [gaze_entry]  # Keep the timing info
                current_seq = [g['direction'] for g in self.step_data['gaze_sequence']]
                self.log_result(f"🔄 Mismatch! Expected {expected_direction}, got {direction}. Resetting sequence.")
                # Update UI immediately after reset
                self._update_sequence_ui(step, pattern, repetitions, current_seq)
        
        # Update UI with current sequence
        print(f"🔧 DEBUG: Updating UI with sequence: {current_seq}")
        self._update_sequence_ui(step, pattern, repetitions, current_seq)
        
        # Log the sequence update
        sequence_display = " → ".join(current_seq)
        self.log_result(f"[SEQUENCE] GAZE SEQUENCE: {sequence_display}")
        
        # Debug: Print current sequence and pattern
        print(f"[DEBUG] Current sequence: {current_seq}")
        print(f"[DEBUG] Pattern: {pattern}")
        print(f"[DEBUG] Sequence length: {len(current_seq)}, Pattern length: {len(pattern)}")
        
        # Check if current sequence matches the pattern
        if len(current_seq) >= len(pattern):
            print(f"[DEBUG] Checking pattern match - current_seq: {current_seq}, pattern: {pattern}")
            # Check if the last part matches the pattern
            if current_seq[-len(pattern):] == pattern:
                print(f"[DEBUG] Pattern match found!")
                # Pattern completed!
                self.step_data['completed_patterns'] += 1
                print(f"[DEBUG] completed_patterns = {self.step_data['completed_patterns']}")
                
                # Calculate pattern timing
                current_time = time.time()
                pattern_start_time = self.step_data.get('current_pattern_start_time', current_time)
                pattern_duration = current_time - pattern_start_time
                
                # Initialize pattern_timings if not exists
                if 'pattern_timings' not in self.step_data:
                    self.step_data['pattern_timings'] = []
                
                # Store detailed timing for this pattern completion
                pattern_timing = {
                    'pattern_number': self.step_data['completed_patterns'],
                    'start_time': pattern_start_time,
                    'end_time': current_time,
                    'duration_seconds': pattern_duration,
                    'start_datetime': datetime.fromtimestamp(pattern_start_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    'end_datetime': datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    'pattern_sequence': pattern.copy(),
                    'actual_gazes': [g['direction'] for g in self.step_data['gaze_sequence']]
                }
                self.step_data['pattern_timings'].append(pattern_timing)
                
                self.log_result(f"[PATTERN] Pattern {self.step_data['completed_patterns']}/{repetitions} completed! (Duration: {pattern_duration:.2f}s)")
                
                # Reset for next pattern
                self.step_data['gaze_sequence'] = []
                self.step_data['current_pattern_start_time'] = time.time()  # Reset pattern start time for next pattern
                
                # Update UI with reset sequence and pattern completion
                self._update_sequence_ui(step, pattern, repetitions, [], pattern_completed=True)
                
                # Schedule UI to return to normal display after 1 second
                self.root.after(1000, lambda: self._update_sequence_ui(step, pattern, repetitions, []))
                
                # Check if all patterns are done
                print(f"[DEBUG] Checking if {self.step_data['completed_patterns']} >= {repetitions}")
                if self.step_data['completed_patterns'] >= repetitions:
                    print(f"[DEBUG] All patterns completed! Letting normal flow handle completion")
                    # Log total sequence time
                    if 'sequence_start_time' in self.step_data:
                        total_sequence_time = time.time() - self.step_data['sequence_start_time']
                        self.log_result(f"[SUCCESS] All patterns completed! Total sequence time: {total_sequence_time:.2f}s")
                    else:
                        self.log_result("[SUCCESS] All patterns completed!")
                    # Don't call complete_current_step here - let the normal flow in process_step_gaze handle it
                    return  # Stop processing more patterns after completion
            else:
                print(f"[DEBUG] Pattern mismatch - expected: {pattern}, got: {current_seq[-len(pattern):]}")
        else:
                # Check if sequence is broken (too long and doesn't match)
                if len(current_seq) > len(pattern):
                    # Sequence is broken - reset
                    self.step_data['gaze_sequence'] = [gaze_entry]  # Start fresh with current direction and timing
                    self.log_result("🔄 Sequence broken - resetting")
                    
                    # Update UI with reset sequence
                    self._update_sequence_ui(step, pattern, repetitions, [direction])

    def _update_sequence_ui(self, step, pattern, repetitions, current_seq, pattern_completed=False):
        """Helper method to consistently update sequence UI"""
        print(f"🔧 DEBUG: _update_sequence_ui called with sequence: {current_seq}, pattern_completed: {pattern_completed}")
        sequence_display = " → ".join(current_seq) if current_seq else ""
        pattern_str = "→".join(pattern)
        
        # Get completed patterns safely
        completed_patterns = 0
        if hasattr(self, 'step_data') and self.step_data and 'completed_patterns' in self.step_data:
            completed_patterns = self.step_data['completed_patterns']
        
        if pattern_completed:
            # Pattern just completed - show success message
            progress_text = f"STEP {self.current_step + 1}/{len(self.test_steps)}\n\n{step['name'].upper()}\n\n{pattern_str} sequences: {completed_patterns}/{repetitions}\n\n✅ Pattern completed!\n\n{step['instruction']}"
            print(f"🔧 DEBUG: Setting UI to pattern completed message")
            self.instruction_display.config(text=progress_text, fg="white", bg="darkgreen")
        else:
            # Normal sequence display - make current sequence more prominent
            progress_text = f"STEP {self.current_step + 1}/{len(self.test_steps)}\n\n{step['name'].upper()}\n\n{pattern_str} sequences: {completed_patterns}/{repetitions}\n\n🎯 CURRENT: {sequence_display}\n\n{step['instruction']}"
            print(f"🔧 DEBUG: Setting UI to normal sequence display: {sequence_display}")
            self.instruction_display.config(text=progress_text, fg="white", bg="darkblue")
        
        # Force immediate UI update
        print(f"🔧 DEBUG: Forcing UI update")
        self.root.update()
        self.root.update_idletasks()
        print(f"🔧 DEBUG: UI update complete")

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
            progress = min(100, (elapsed_time / target_duration) * 100)
            self.progress_var.set(progress)
            
            status_line = f"\n⏱️ Elapsed: {elapsed_time:.1f}s / {target_duration}s"
            if false_detections > 0:
                status_line += f"\n⚠️ False detections: {false_detections}"
            
            progress_text = f"STEP {self.current_step + 1}/{len(self.test_steps)}\n\n{step['name'].upper()}\n\n{step['instruction']}{status_line}"
            self.instruction_display.config(text=progress_text, fg="white", bg="darkblue")
            
        elif step['type'].startswith('sequence_'):
            # Use completed patterns count from sequence tracking
            completed_patterns = self.step_data.get('completed_patterns', 0)
            repetitions = step.get('repetitions', 3)
            
            progress = min(100, (completed_patterns / repetitions) * 100)
            self.progress_var.set(progress)
            
            # For sequence steps, don't override the detailed UI from _update_sequence_ui
            # Just update the progress bar - the sequence UI is handled separately
    
    def check_step_completion(self):
        """Check if current step is complete and should auto-advance"""
        if not hasattr(self, 'step_data') or not self.step_data:
            return False
        
        step = self.test_steps[self.current_step]
        detections = self.step_data['detections']
        
        # Add grace period for automated testing - don't check completion too early
        if hasattr(self, 'step_start_time'):
            elapsed = time.time() - self.step_start_time
            if elapsed < 2.0:  # 2 second grace period (reduced from 5)
                return False
        
        if step['type'] in ['quick_up', 'quick_down']:
            # Check if we have enough quick gazes
            target_direction = 'UP' if step['type'] == 'quick_up' else 'DOWN'
            count = len([d for d in detections if d['direction'] == target_direction and not d['is_continuous']])
            target = step.get('repetitions', 5)
            print(f"🔍 DEBUG: check_step_completion quick - count: {count}, target: {target}")
            return count >= target
            
        elif step['type'] in ['long_up', 'long_down']:
            # Check if we have enough long holds (completed ones with hold_duration)
            target_direction = 'UP' if step['type'] == 'long_up' else 'DOWN'
            count = len([d for d in detections if d['direction'] == target_direction and d.get('hold_duration', 0) > 0])
            target = step.get('repetitions', 3)
            print(f"🔍 DEBUG: check_step_completion long - count: {count}, target: {target}")
            return count >= target
            
            
        elif step['type'].startswith('sequence_'):
            # Check if we have enough completed sequences using the counter from update_sequence_progress
            repetitions = step.get('repetitions', 3)
            completed_patterns = self.step_data.get('completed_patterns', 0)
            print(f"🔍 DEBUG: check_step_completion - completed_patterns: {completed_patterns}, needed: {repetitions}")
            return completed_patterns >= repetitions
            
        return False
    
    def complete_current_step(self):
        """Complete the current test step"""
        print(f"🔧 complete_current_step called for step {self.current_step}")
        
        # Cancel the timeout timer since step is completing
        if hasattr(self, 'step_timeout_timer'):
            self.root.after_cancel(self.step_timeout_timer)
            print(f"🔧 Cancelled step timeout timer")
        
        if not hasattr(self, 'step_data') or self.step_data is None:
            # Initialize step_data if missing
            self.step_data = {'detections': [], 'start_time': time.time()}
            self.step_start_time = time.time()
            print("🔧 Initialized missing step_data")
        
        # Add 2-second delay before stopping recording to capture extra padding
        print("⏱️ Adding 2-second padding before stopping recording...")
        self.root.after(2000, self._complete_step_after_delay)
    
    def _complete_step_after_delay(self):
        """Complete step after recording padding delay"""
        print("🔧 Recording padding complete, stopping recording now")
        
        # Stop recording
        self.stop_step_recording()
        
        step = self.test_steps[self.current_step]
        duration = time.time() - self.step_start_time
        
        # Analyze results
        success = self.analyze_step_results(step, self.step_data)
        print(f"🔧 Step analysis result: {success}")
        
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
        print(f"🔧 Step result logged: {status}")
        
        # For calibration steps, log the actual baseline after completion
        if step['type'] == 'calibration':
            self.log_calibration_baseline()
        
        # Save step completion summary
        self.save_step_summary(step, success, duration)
        
        # Always advance to next step (no retries)
        if success:
            self.speak("Step completed")
        else:
            self.speak("Step completed with issues. Moving to next step.")
        
        # Update UI to show "NEXT STEP"
        self.instruction_display.config(text="NEXT STEP", fg="white", bg="green")
        
        # Process video cuts for hold tests
        if step['type'] in ['long_up', 'long_down']:
            self.create_hold_video_cuts()
        
        delattr(self, 'step_data')
        print("🔧 Scheduling next_step in 2 seconds...")
        # Ensure this runs in the main thread
        self.root.after(2000, lambda: self.root.after(0, self.next_step))
    
    def analyze_step_results(self, step, step_data):
        """Analyze step results to determine success"""
        step_type = step['type']
        print(f"🔍 ANALYZING STEP: {step_type}")
        print(f"🔍 step_data keys: {list(step_data.keys()) if step_data else 'None'}")
        
        # Calibration steps always succeed if they complete
        if step_type == 'calibration':
            print(f"🔍 Calibration step - returning True")
            return True
        
        if not step_data:
            print(f"🔍 No step_data - returning False")
            return False
        
        # For sequence steps, we don't need detections - we use completed_patterns
        if step['type'].startswith('sequence_'):
            completed_patterns = step_data.get('completed_patterns', 0)
            repetitions = step.get('repetitions', 3)
            
            print(f"🔍 Sequence analysis: {completed_patterns} completed patterns, need {repetitions}")
            result = completed_patterns >= repetitions
            print(f"🔍 Sequence step result: {result}")
            return result
        
        # For other steps, check detections
        if 'detections' not in step_data:
            print(f"🔍 No detections key in step_data - returning False")
            return False
        
        detections = step_data['detections']
        if not detections:
            print(f"🔍 No detections - returning False")
            return False
        
        print(f"🔍 Found {len(detections)} detections")
        
        if step_type == 'long_up':
            up_holds = [d for d in detections if d['direction'] == 'UP' and d.get('hold_duration', 0) > 0]
            result = len(up_holds) >= step.get('repetitions', 3)
            print(f"🔍 Long UP: {len(up_holds)} holds, need {step.get('repetitions', 3)} - returning {result}")
            return result
        
        elif step_type == 'long_down':
            down_holds = [d for d in detections if d['direction'] == 'DOWN' and d.get('hold_duration', 0) > 0]
            result = len(down_holds) >= step.get('repetitions', 3)
            print(f"🔍 Long DOWN: {len(down_holds)} holds, need {step.get('repetitions', 3)} - returning {result}")
            return result
        
        elif step_type == 'quick_up':
            up_gazes = [d for d in detections if d['direction'] == 'UP' and not d.get('is_continuous', False)]
            result = len(up_gazes) >= step.get('repetitions', 5)
            print(f"🔍 Quick UP: {len(up_gazes)} gazes, need {step.get('repetitions', 5)} - returning {result}")
            return result
        
        elif step_type == 'quick_down':
            down_gazes = [d for d in detections if d['direction'] == 'DOWN' and not d.get('is_continuous', False)]
            result = len(down_gazes) >= step.get('repetitions', 5)
            print(f"🔍 Quick DOWN: {len(down_gazes)} gazes, need {step.get('repetitions', 5)} - returning {result}")
            return result
        
        elif step_type.startswith('sequence_'):
            # Use completed patterns count from sequence tracking
            completed_patterns = step_data.get('completed_patterns', 0)
            repetitions = step.get('repetitions', 3)
            
            print(f"🔍 Sequence analysis: {completed_patterns} completed patterns, need {repetitions}")
            result = completed_patterns >= repetitions
            print(f"🔍 Sequence step result: {result}")
            return result
        
        print(f"🔍 Unknown step type - returning False")
        return False
    
    def next_step(self):
        """Move to the next step"""
        print(f"🔧 next_step called - advancing from step {self.current_step}")
        self.current_step += 1
        print(f"🔧 Advanced to step {self.current_step}")
        
        # Force UI update to ensure main thread processes it
        self.root.update()
        self.root.update_idletasks()
        
        if self.current_step < len(self.test_steps):
            print(f"🔧 Executing step {self.current_step}: {self.test_steps[self.current_step]['name']}")
            # Execute immediately in main thread
            self.execute_current_step()
        else:
            print("🔧 All steps completed - calling complete_test")
            self.complete_test()
    
    def execute_current_step(self):
        """Execute the current test step"""
        step = self.test_steps[self.current_step]
        
        # Set step start time for grace period
        self.step_start_time = time.time()
        
        # Cancel any existing timeout timer
        if hasattr(self, 'step_timeout_timer'):
            self.root.after_cancel(self.step_timeout_timer)
            print(f"🔧 Cancelled previous step timeout timer")
        
        # Create step-specific directory
        step_dir = os.path.join(self.session_dir, f"step_{self.current_step:02d}_{step['name'].lower().replace(' ', '_')}")
        os.makedirs(step_dir, exist_ok=True)
        self.current_step_dir = step_dir
        
        # Log baseline data for this step
        self.log_step_baseline(step)
        
        # Clear any existing calibration canvas first
        if hasattr(self, 'calibration_canvas'):
            self.calibration_canvas.destroy()
            delattr(self, 'calibration_canvas')
        
        # Update UI based on step type
        if step['type'] == 'calibration':
            # For calibration, show calibration display immediately
            self.show_calibration_display()
        else:
            # For other steps, show step instruction
            instruction_text = f"STEP {self.current_step + 1}/{len(self.test_steps)}\n\n{step['name'].upper()}\n\n{step['instruction']}"
            self.instruction_display.config(text=instruction_text, fg="white", bg="darkblue")
            print(f"🔧 UI Updated: {instruction_text}")
            # Force UI update to ensure it's visible
            self.root.update()
            self.root.update_idletasks()
        
        # No more step delays - using actual TTS timing
        
        # CORRECT FLOW:
        # 1. Initialize step data
        # 2. Start TTS (callback when done)
        # 3. Start recording in parallel (sets recording_ready=True when done)
        # 4. In TTS callback: wait for recording_ready, wait 1s, play beep
        # 5. After beep: execute step
        
        # Reset recording ready flag
        self.recording_ready = False
        
        # Block gaze detection until after beep
        self.allow_gaze_detection = False
        print("🚫 Gaze detection BLOCKED until beep")
        
        # Initialize step data for all steps
        self.step_data = {
            'detections': [],
            'start_time': time.time(),
            'current_gaze_state': None,
            'hold_start_time': None
        }
        
        # Define what happens after TTS completes
        def after_tts_complete():
            """Called when TTS finishes - check recording, wait, then beep"""
            print("✅ TTS complete - checking if recording is ready")
            
            # Check if recording is ready, if not wait
            def check_and_proceed():
                if self.recording_ready:
                    print("✅ Recording ready - waiting 1 second before beep")
                    self.root.after(1000, play_beep_and_execute)
                else:
                    print("⏳ Waiting for recording to be ready...")
                    self.root.after(100, check_and_proceed)  # Check again in 100ms
            
            check_and_proceed()
        
        def play_beep_and_execute():
            """Play beep and execute step"""
            print("🔊 Playing beep...")
            self.play_beep_async()
            
            # Enable gaze detection AFTER beep
            self.allow_gaze_detection = True
            print("✅ Gaze detection ENABLED after beep")
            
            # Execute step after beep
            self.root.after(500, execute_step_action)
        
        def execute_step_action():
            """Execute the actual step"""
            print(f"🎬 Executing step: {step['name']}")
            
            if step['type'] != 'calibration':
                # For gaze steps, start simulation and set timeout
                def start_simulation():
                    if hasattr(self.gaze_detector, 'start_step_simulation'):
                        auto_simulate_enabled = not hasattr(self.gaze_detector, 'auto_simulate') or self.gaze_detector.auto_simulate
                        if auto_simulate_enabled:
                            self.gaze_detector.start_step_simulation(step['type'], step)
                
                self.root.after(1000, start_simulation)
                
                # Set timeout
                max_duration = step.get('duration', 60)
                self.step_timeout_timer = self.safe_after(int(max_duration * 1000), self.complete_current_step)
                print(f"🔧 Set step timeout timer for {max_duration} seconds")
            else:
                # For calibration, execute calibration step immediately
                self.execute_calibration_step()
        
        # Start TTS FIRST (important - this takes longer)
        if not self.tts_engine:
            print("⚠️ TTS not available - proceeding after recording ready")
            # Still wait for recording, then beep
            def check_recording_only():
                if self.recording_ready:
                    self.root.after(1000, play_beep_and_execute)
                else:
                    self.root.after(100, check_recording_only)
            check_recording_only()
        else:
            print(f"🔊 Starting TTS for: {step['name']}")
            print(f"📢 Instruction: {step['instruction']}")
            self.speak(step['instruction'], after_tts_complete)
        
        # Start recording AFTER TTS (in parallel) - use short delay to ensure TTS thread starts
        self.root.after(50, self.start_step_recording)
    
    def execute_calibration_step(self):
        """Execute calibration step"""
        step = self.test_steps[self.current_step]
        
        # Recording already started in execute_current_step
        # Show calibration display
        self.show_calibration_display()
        
        # Collect calibration data
        self.calibrating = True
        calibration_data = []
        start_time = time.time()
        
        def calibration_thread():
            # Use 5 seconds for real use, 1 second for automation
            calibration_duration = getattr(self, 'calibration_duration', 5.0)
            while time.time() - start_time < calibration_duration:
                if self.gaze_detector.is_ready():
                    gaze_result = self.gaze_detector.update()
                    if gaze_result and gaze_result.get('pupil_relative'):
                        calibration_data.append(gaze_result['pupil_relative'])
                time.sleep(0.1)
            
            # Calculate baseline
            if calibration_data:
                # Handle both scalar and tuple pupil_relative values
                if isinstance(calibration_data[0], (tuple, list)):
                    # If it's a tuple/list, extract the y coordinate
                    baseline_y = sum(point[1] if len(point) > 1 else point[0] for point in calibration_data) / len(calibration_data)
                else:
                    # If it's a scalar, use it directly
                    baseline_y = sum(calibration_data) / len(calibration_data)
                print(f"Gaze baseline established: {baseline_y:.3f}")
                
                # Update gaze detector baseline if it has one
                if hasattr(self.gaze_detector, 'gaze_detector') and hasattr(self.gaze_detector.gaze_detector, 'baseline_y'):
                    self.gaze_detector.gaze_detector.baseline_y = baseline_y
                
                self.log_result(f"✅ Calibration completed - Baseline: {baseline_y:.3f}")
            else:
                self.log_result("❌ Calibration failed - No data collected")
            
            # Reset UI
            self.calibrating = False
            
            # Check if window still exists before updating UI
            try:
                # Schedule UI update in main thread
                self.root.after(0, lambda: self.instruction_display.config(text="NEXT STEP", 
                                              fg="white", bg="green"))
                
                # Schedule step completion in main thread
                print("🔧 Scheduling complete_current_step in 2 seconds...")
                self.root.after(2000, self.complete_current_step)
            except:
                # Window was closed, just return
                return
        
        threading.Thread(target=calibration_thread, daemon=True).start()
    
    
    def show_calibration_display(self):
        """Show calibration display with actual red dot"""
        # Clear the instruction display
        self.instruction_display.config(text="", fg="white", bg="black")
        
        # Create a canvas for the red dot
        if hasattr(self, 'calibration_canvas'):
            self.calibration_canvas.destroy()
            
        # Get the actual size of the instruction display
        self.instruction_display.update_idletasks()
        width = self.instruction_display.winfo_width()
        height = self.instruction_display.winfo_height()
        
        # Use the actual size or default if too small
        canvas_width = max(width, 400)
        canvas_height = max(height, 300)
        
        self.calibration_canvas = tk.Canvas(self.instruction_display, 
                                          width=canvas_width, height=canvas_height, 
                                          bg="black", highlightthickness=0)
        self.calibration_canvas.pack(expand=True, fill="both")
        
        # Draw red dot in center (larger)
        center_x = canvas_width // 2
        center_y = canvas_height // 2
        dot_radius = 20  # Larger dot
        
        # Add text above the dot
        self.calibration_canvas.create_text(center_x, center_y - 100, 
                                          text="CALIBRATION", 
                                          fill="white", font=("Arial", 24, "bold"))
        self.calibration_canvas.create_text(center_x, center_y - 60, 
                                          text="Look at the red dot", 
                                          fill="white", font=("Arial", 18))
        
        # Draw the red dot
        self.calibration_canvas.create_oval(center_x - dot_radius, center_y - dot_radius,
                                          center_x + dot_radius, center_y + dot_radius,
                                          fill="red", outline="red")
        
        # Add status text below the dot
        self.calibration_canvas.create_text(center_x, center_y + 40, 
                                          text="Calibrating...", 
                                          fill="yellow", font=("Arial", 16))
        
        # Force UI update before speaking
        self.root.update()
        
        # Note: Speech is handled by the main step execution, not here
    
    def auto_start_test(self):
        """Auto-start the test after the starting screen"""
        self.start_test()
    
    def start_test(self):
        """Start the comprehensive test"""
        # Create results directory if it doesn't exist
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        
        # Create session directory with microseconds for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        self.session_dir = os.path.join(results_dir, f"gaze_test_session_{timestamp}")
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Reset test state
        self.test_running = True
        self.current_step = 0
        self.test_results = []
        
        # Start recording
        self.start_recording()
        
        # Start first step
        self.execute_current_step()
        
        # Force window to front when test starts and keep it on top
        self._force_to_front()
        self.root.attributes('-topmost', True)  # Keep on top during test
        
        # Update UI
        self.start_button.config(state="disabled")
        self.status_label.config(text="Test Running")
    
    
    def reset_test(self):
        """Reset the test"""
        self.test_running = False
        self.current_step = 0
        self.test_results = []
        
        if hasattr(self, 'step_data'):
            delattr(self, 'step_data')
        
        # Stop recording
        self.stop_recording()
        
        # Reset UI
        self.instruction_display.config(text="Click 'Start Test' to begin comprehensive gaze testing",
                                      fg="white", bg="darkblue")
        self.progress_var.set(0)
        self.start_button.config(state="normal")
        self.status_label.config(text="Ready")
        self.results_text.delete(1.0, tk.END)
    
    def complete_test(self):
        """Complete the entire test"""
        self.test_running = False
        
        # Stop recording
        self.stop_recording()
        
        # Generate report
        self.generate_report()
        
        # Update UI
        self.instruction_display.config(text="TEST COMPLETE\n\nAll steps completed successfully!\n\nUploading to Google Drive...",
                                      fg="white", bg="green")
        self.start_button.config(state="normal")
        self.status_label.config(text="Test Complete - Uploading...")
        
        self.speak("Test completed successfully! Uploading results to Google Drive.")
        
        # Upload to Google Drive in a separate thread
        upload_thread = threading.Thread(target=self.upload_to_google_drive, daemon=True)
        upload_thread.start()
    
    def upload_to_google_drive(self):
        """Upload test results to Google Drive"""
        try:
            if not self.session_dir:
                print("❌ No session directory to upload")
                return
            
            print("🚀 Starting Google Drive upload...")
            
            # Use direct uploader instead of subprocess
            from google_drive_uploader import GoogleDriveUploader
            uploader = GoogleDriveUploader()
            
            if uploader.upload_session(self.session_dir):
                print("✅ Upload successful!")
                # Update UI to show success
                self.root.after(0, lambda: self.instruction_display.config(
                    text="TEST COMPLETE\n\nAll steps completed successfully!\n\n✅ Uploaded to Google Drive!",
                    fg="white", bg="green"
                ))
                self.root.after(0, lambda: self.status_label.config(text="Test Complete - Uploaded!"))
                self.root.after(0, lambda: self.speak("Results uploaded to Google Drive successfully!"))
                # Auto-exit after successful upload
                self.root.after(3000, lambda: self.root.quit())
            else:
                print("❌ Upload failed")
                # Update UI to show failure
                self.root.after(0, lambda: self.instruction_display.config(
                    text="TEST COMPLETE\n\nAll steps completed successfully!\n\n❌ Upload failed - check console",
                    fg="white", bg="orange"
                ))
                self.root.after(0, lambda: self.status_label.config(text="Test Complete - Upload Failed"))
                self.root.after(0, lambda: self.speak("Test completed but upload failed."))
                # Auto-exit after failed upload too
                self.root.after(5000, lambda: self.root.quit())
                
        except subprocess.TimeoutExpired:
            print("❌ Upload timed out after 5 minutes")
            self.root.after(0, lambda: self.instruction_display.config(
                text="TEST COMPLETE\n\nAll steps completed successfully!\n\n⏰ Upload timed out",
                fg="white", bg="orange"
            ))
            self.root.after(0, lambda: self.status_label.config(text="Test Complete - Upload Timeout"))
            # Auto-exit after timeout
            self.root.after(5000, lambda: self.root.quit())
        except Exception as e:
            print(f"❌ Upload error: {e}")
            self.root.after(0, lambda: self.instruction_display.config(
                text="TEST COMPLETE\n\nAll steps completed successfully!\n\n❌ Upload error",
                fg="white", bg="orange"
            ))
            self.root.after(0, lambda: self.status_label.config(text="Test Complete - Upload Error"))
            # Auto-exit after error
            self.root.after(5000, lambda: self.root.quit())
    
    def generate_report(self):
        """Generate test report"""
        report = {
            'session_info': {
                'timestamp': datetime.now().isoformat(),
                'total_steps': len(self.test_steps),
                'completed_steps': len(self.test_results)
            },
            'results': self.test_results,
            'summary': {
                'passed': len([r for r in self.test_results if r['success']]),
                'failed': len([r for r in self.test_results if not r['success']]),
                'total_duration': sum(r['duration'] for r in self.test_results)
            }
        }
        
        # Save report
        report_path = os.path.join(self.session_dir, 'test_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Display summary
        self.log_result("📊 TEST REPORT GENERATED")
        self.log_result(f"✅ Passed: {report['summary']['passed']}")
        self.log_result(f"❌ Failed: {report['summary']['failed']}")
        self.log_result(f"⏱️ Total Duration: {report['summary']['total_duration']:.1f}s")
        self.log_result(f"📁 Report saved: {report_path}")
    
    def log_step_baseline(self, step):
        """Log baseline data for the current step"""
        # Get actual gaze baseline from the gaze detector
        gaze_baseline = None
        if hasattr(self, 'gaze_detector') and self.gaze_detector:
            if hasattr(self.gaze_detector, 'gaze_detector') and self.gaze_detector.gaze_detector:
                # For real gaze detector
                if hasattr(self.gaze_detector.gaze_detector, 'baseline_y'):
                    gaze_baseline = self.gaze_detector.gaze_detector.baseline_y
            elif hasattr(self.gaze_detector, 'baseline_y'):
                # For simulated gaze detector
                gaze_baseline = self.gaze_detector.baseline_y
        
        baseline_data = {
            'step_name': step['name'],
            'step_type': step['type'],
            'step_number': self.current_step + 1,
            'total_steps': len(self.test_steps),
            'start_time': time.time(),
            'start_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'instruction': step['instruction'],
            'expected_repetitions': step.get('repetitions', 1),
            'expected_duration': step.get('duration', 30),
            'pattern': step.get('pattern', []) if step.get('pattern') else None,
            'gaze_baseline_y': gaze_baseline,
            'gaze_detector_type': type(self.gaze_detector).__name__ if hasattr(self, 'gaze_detector') else 'Unknown'
        }
        
        self.log_result(f"📊 STEP BASELINE: {baseline_data}")
        
        # Save baseline data to JSON file
        if hasattr(self, 'current_step_dir') and self.current_step_dir:
            baseline_file = os.path.join(self.current_step_dir, "baseline_data.json")
            with open(baseline_file, "w") as f:
                json.dump(baseline_data, f, indent=2)
    
    def save_step_summary(self, step, success, duration):
        """Save detailed step completion summary"""
        if not hasattr(self, 'current_step_dir') or not self.current_step_dir:
            return
            
        # Collect all detections with timestamps
        detections = []
        if hasattr(self, 'step_data') and self.step_data and 'detections' in self.step_data:
            for detection in self.step_data['detections']:
                detections.append({
                    'timestamp': detection.get('timestamp', 0),
                    'absolute_timestamp': detection.get('absolute_timestamp', 0),
                    'datetime': detection.get('datetime', ''),
                    'direction': detection.get('direction', ''),
                    'offset': detection.get('offset', 0),
                    'is_continuous': detection.get('is_continuous', False),
                    'hold_duration': detection.get('hold_duration', 0)
                })
        
        # Collect sequence data if available
        sequence_data = None
        if hasattr(self, 'step_data') and self.step_data:
            if 'gaze_sequence' in self.step_data:
                sequence_data = {
                    'gaze_sequence': self.step_data.get('gaze_sequence', []),
                    'completed_patterns': self.step_data.get('completed_patterns', 0),
                    'sequence_start_time': self.step_data.get('sequence_start_time', 0),
                    'total_sequence_time': time.time() - self.step_data.get('sequence_start_time', time.time()) if 'sequence_start_time' in self.step_data else 0,
                    'pattern_timings': self.step_data.get('pattern_timings', [])
                }
        
        # Get current baseline data
        gaze_baseline = None
        if hasattr(self, 'gaze_detector') and self.gaze_detector:
            if hasattr(self.gaze_detector, 'gaze_detector') and self.gaze_detector.gaze_detector:
                # For real gaze detector
                if hasattr(self.gaze_detector.gaze_detector, 'baseline_y'):
                    gaze_baseline = self.gaze_detector.gaze_detector.baseline_y
            elif hasattr(self.gaze_detector, 'baseline_y'):
                # For simulated gaze detector
                gaze_baseline = self.gaze_detector.baseline_y

        # Don't include raw step_data for sequence steps (it's duplicated in sequence_data)
        include_step_data = not (sequence_data is not None)
        
        summary = {
            'step_name': step['name'],
            'step_type': step['type'],
            'success': success,
            'duration': duration,
            'completion_time': time.time(),
            'completion_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'detections': detections,
            'detection_count': len(detections),
            'sequence_data': sequence_data,
            'gaze_baseline_y': gaze_baseline,
            'gaze_detector_type': type(self.gaze_detector).__name__ if hasattr(self, 'gaze_detector') else 'Unknown'
        }
        
        # Only include step_data for non-sequence steps to avoid duplication
        if include_step_data:
            summary['step_data'] = self.step_data if hasattr(self, 'step_data') else None
        
        # Save summary to JSON file
        summary_file = os.path.join(self.current_step_dir, "step_summary.json")
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        self.log_result(f"📁 Step summary saved: {summary_file}")
    
    def log_calibration_baseline(self):
        """Log the actual baseline values after calibration completes"""
        # Get actual gaze baseline from the gaze detector
        gaze_baseline = None
        if hasattr(self, 'gaze_detector') and self.gaze_detector:
            if hasattr(self.gaze_detector, 'gaze_detector') and self.gaze_detector.gaze_detector:
                # For real gaze detector
                if hasattr(self.gaze_detector.gaze_detector, 'baseline_y'):
                    gaze_baseline = self.gaze_detector.gaze_detector.baseline_y
            elif hasattr(self.gaze_detector, 'baseline_y'):
                # For simulated gaze detector
                gaze_baseline = self.gaze_detector.baseline_y
        
        baseline_info = {
            'gaze_baseline_y': gaze_baseline,
            'gaze_detector_type': type(self.gaze_detector).__name__ if hasattr(self, 'gaze_detector') else 'Unknown',
            'calibration_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'calibration_time': time.time()
        }
        
        self.log_result(f"🎯 CALIBRATION BASELINE: {baseline_info}")
        
        # Update the baseline_data.json file with actual baseline
        if hasattr(self, 'current_step_dir') and self.current_step_dir:
            baseline_file = os.path.join(self.current_step_dir, "baseline_data.json")
            try:
                with open(baseline_file, "r") as f:
                    baseline_data = json.load(f)
                baseline_data.update(baseline_info)
                with open(baseline_file, "w") as f:
                    json.dump(baseline_data, f, indent=2)
                self.log_result(f"📁 Updated baseline_data.json with actual baseline values")
            except Exception as e:
                self.log_result(f"❌ Error updating baseline file: {e}")
    
    def log_result(self, message):
        """Log a result message"""
        try:
            timestamp = time.strftime("%H:%M:%S")
            self.results_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.results_text.see(tk.END)
            self.root.update()
            
            # Also log to file if we have a current step directory
            if hasattr(self, 'current_step_dir') and self.current_step_dir:
                log_file = os.path.join(self.current_step_dir, "step_log.txt")
                with open(log_file, "a") as f:
                    f.write(f"[{timestamp}] {message}\n")
        except:
            # Window was closed or not in main thread, just print
            print(f"[{timestamp}] {message}")
    
    def speak(self, text, callback=None):
        """Speak text using TTS with optional completion callback"""
        try:
            if self.tts_engine and text:
                # Truncate very long text to prevent TTS issues
                if len(text) > self.max_tts_length:
                    text = text[:self.max_tts_length] + "..."
                    print(f"⚠️ TTS text truncated to {self.max_tts_length} characters")
                
                # Add callback if provided
                if callback:
                    self.tts_callbacks.append(callback)
                    print(f"🔊 TTS queued with callback: '{text[:50]}...'")
                else:
                    print(f"🔊 TTS queued: '{text[:50]}...'")
                
                self.tts_queue.append(text)
                self._process_tts_queue()
        except Exception as e:
            print(f"❌ Error adding text to TTS queue: {e}")
            # Execute callback immediately if TTS fails
            if callback:
                self.root.after(0, callback)
            self._process_tts_queue()
    
    def _process_tts_queue(self):
        """Process TTS queue"""
        if not self.tts_speaking and self.tts_queue:
            self.tts_speaking = True
            text = self.tts_queue.pop(0)
            
            # Set a timeout for TTS operations (10 seconds)
            self.tts_timeout_timer = self.root.after(30000, self._tts_timeout)  # Increased to 30 seconds
            
            # Run TTS in a separate thread to avoid blocking
            def speak_text():
                try:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                    
                    # IMPORTANT: Add delay to ensure audio actually finishes playing
                    # runAndWait() sometimes returns before audio completes
                    # Estimate: ~0.1s per word, minimum 1 second
                    word_count = len(text.split())
                    estimated_duration = max(1.0, word_count * 0.6)
                    time.sleep(estimated_duration)
                    
                    # TTS finished - execute callback in main thread
                    self.root.after(0, self._on_tts_finished)
                except Exception as e:
                    print(f"❌ TTS error: {e}")
                    # Execute callback immediately if TTS fails
                    self.root.after(0, self._on_tts_finished)
            
            threading.Thread(target=speak_text, daemon=True).start()
    
    def _tts_timeout(self):
        """Handle TTS timeout"""
        print("⚠️ TTS timeout - forcing completion")
        self._on_tts_finished()
    
    def _on_tts_finished(self):
        """Called when TTS finishes speaking"""
        print("🔊 TTS finished speaking")
        self.tts_speaking = False
        
        # Cancel timeout timer
        if self.tts_timeout_timer:
            self.root.after_cancel(self.tts_timeout_timer)
            self.tts_timeout_timer = None
        
        # Execute any pending callbacks
        if self.tts_callbacks:
            callback = self.tts_callbacks.pop(0)
            print("🔊 Executing TTS callback")
            self.root.after(0, callback)
        
        # Process next item in queue
        if self.tts_queue:
            self.root.after(100, self._process_tts_queue)
    
    
    def speak_long_text(self, text, callback=None):
        """Handle very long text by breaking into chunks"""
        if len(text) <= self.max_tts_length:
            self.speak(text, callback)
            return
        
        # Break into sentences or chunks
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= self.max_tts_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Speak each chunk sequentially
        def speak_chunk(index):
            if index < len(chunks):
                is_last = (index == len(chunks) - 1)
                chunk_callback = callback if is_last else lambda: speak_chunk(index + 1)
                self.speak(chunks[index], chunk_callback)
        
        speak_chunk(0)
    
    def test_tts(self):
        """Test TTS functionality"""
        print("🔊 Testing TTS...")
        if self.tts_engine:
            try:
                self.tts_engine.say("TTS test")
                self.tts_engine.runAndWait()
                print("✅ TTS working")
            except Exception as e:
                print(f"❌ TTS test failed: {e}")
        else:
            print("❌ TTS engine not available")
    
    def play_beep_async(self):
        """Play beep sound asynchronously"""
        print("🔊 Playing beep...")
        def play_beep():
            try:
                import winsound
                winsound.Beep(1000, 200)  # 1000 Hz for 200ms
                print("🔊 Beep played (Windows)")
            except ImportError:
                # On macOS/Linux, use system beep
                try:
                    import os
                    os.system('afplay /System/Library/Sounds/Ping.aiff')  # macOS
                    print("🔊 Beep played (macOS)")
                except:
                    try:
                        os.system('paplay /usr/share/sounds/alsa/Front_Left.wav')  # Linux
                        print("🔊 Beep played (Linux)")
                    except:
                        print("\a")  # Fallback to ASCII bell
                        print("🔊 Beep played (ASCII bell)")
        
        threading.Thread(target=play_beep, daemon=True).start()
    
    def start_recording(self):
        """Start video recording"""
        if not self.recording:
            self.recording = True
            self.recording_label.config(text="Recording", foreground="red")
            self.log_result("🔴 Recording started")
    
    def stop_recording(self):
        """Stop video recording"""
        if self.recording:
            self.recording = False
            self.recording_label.config(text="Not Recording", foreground="black")
            self.log_result("⏹️ Recording stopped")
    
    def start_step_recording(self):
        """Start recording for current step"""
        if self.recording:
            step = self.test_steps[self.current_step]
            step_dir = os.path.join(self.session_dir, f"step_{self.current_step:02d}_{step['name'].lower().replace(' ', '_')}")
            os.makedirs(step_dir, exist_ok=True)
            
            # Initialize video writers
            try:
                import cv2
                
                # Create video writers for this step
                raw_video_path = os.path.join(step_dir, f"{step['name'].lower().replace(' ', '_')}_raw.mp4")
                analysis_video_path = os.path.join(step_dir, f"{step['name'].lower().replace(' ', '_')}_analysis.mp4")
                
                # Video settings - match actual camera frame rate
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                fps = 15  # Reduced from 30 to prevent speed issues
                frame_width = 640
                frame_height = 480
                
                # Initialize video writers
                self.raw_video_writer = cv2.VideoWriter(raw_video_path, fourcc, fps, (frame_width, frame_height))
                self.analysis_video_writer = cv2.VideoWriter(analysis_video_path, fourcc, fps, (frame_width, frame_height))
                
                self.log_result(f"📹 Started recording step: {step['name']}")
                self.log_result(f"📁 Raw video: {raw_video_path}")
                self.log_result(f"📁 Analysis video: {analysis_video_path}")
                
                # Recording is now ready - set flag
                print("🔧 Recording setup complete - ready for beep")
                self.recording_ready = True
                
            except ImportError:
                self.log_result("❌ OpenCV not available - video recording disabled")
                self.recording = False
            except Exception as e:
                self.log_result(f"❌ Failed to initialize video recording: {e}")
                self.recording = False
    
    def stop_step_recording(self):
        """Stop recording for current step"""
        if self.recording:
            try:
                # Release video writers
                if hasattr(self, 'raw_video_writer') and self.raw_video_writer:
                    self.raw_video_writer.release()
                    self.raw_video_writer = None
                
                if hasattr(self, 'analysis_video_writer') and self.analysis_video_writer:
                    self.analysis_video_writer.release()
                    self.analysis_video_writer = None
                
                self.log_result("📹 Stopped recording step")
            except Exception as e:
                self.log_result(f"❌ Error stopping video recording: {e}")
    
    def record_video_frames(self, gaze_result: Dict[str, Any]):
        """Record video frames for current step"""
        try:
            import cv2
            import numpy as np
            
            # Get the actual camera frame from the gaze detector
            frame = None
            if hasattr(self.gaze_detector, 'get_current_frame'):
                frame = self.gaze_detector.get_current_frame()
            elif hasattr(self.gaze_detector, 'gaze_detector') and hasattr(self.gaze_detector.gaze_detector, 'get_current_frame'):
                frame = self.gaze_detector.gaze_detector.get_current_frame()
            
            # If no frame available, create a placeholder
            if frame is None:
                frame_width = 640
                frame_height = 480
                frame = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
                cv2.putText(frame, "No Camera Feed Available", (10, frame_height//2), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Ensure frame is in correct format
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                # Frame is already BGR, use as is
                pass
            else:
                # Convert if needed
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) if len(frame.shape) == 3 else cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            
            # Resize frame to standard size if needed
            frame_height, frame_width = frame.shape[:2]
            if frame_width != 640 or frame_height != 480:
                frame = cv2.resize(frame, (640, 480))
                frame_height, frame_width = frame.shape[:2]
            
            # Write clean raw video (no overlays)
            if hasattr(self, 'raw_video_writer') and self.raw_video_writer:
                self.raw_video_writer.write(frame)
            
            # Create analysis frame with overlays
            analysis_frame = frame.copy()
            
            # Add gaze information overlays
            direction = gaze_result.get('direction', 'NONE')
            is_continuous = gaze_result.get('is_continuous_gaze', False)
            gaze_detected = gaze_result.get('gaze_detected', False)
            
            # Add step name
            cv2.putText(analysis_frame, f"Step: {self.test_steps[self.current_step]['name']}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add gaze information
            cv2.putText(analysis_frame, f"Gaze: {direction}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(analysis_frame, f"Continuous: {is_continuous}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(analysis_frame, f"Detected: {gaze_detected}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Add timestamp
            timestamp = time.strftime("%H:%M:%S")
            cv2.putText(analysis_frame, timestamp, (10, frame_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Add gaze direction indicator
            if direction == 'UP':
                cv2.arrowedLine(analysis_frame, (frame_width//2, frame_height//2), 
                               (frame_width//2, 50), (0, 0, 255), 5)
            elif direction == 'DOWN':
                cv2.arrowedLine(analysis_frame, (frame_width//2, frame_height//2), 
                               (frame_width//2, frame_height - 50), (0, 0, 255), 5)
            elif direction == 'LEFT':
                cv2.arrowedLine(analysis_frame, (frame_width//2, frame_height//2), 
                               (50, frame_height//2), (0, 0, 255), 5)
            elif direction == 'RIGHT':
                cv2.arrowedLine(analysis_frame, (frame_width//2, frame_height//2), 
                               (frame_width - 50, frame_height//2), (0, 0, 255), 5)
            
            # Add center crosshair
            cv2.line(analysis_frame, (frame_width//2 - 20, frame_height//2), 
                    (frame_width//2 + 20, frame_height//2), (255, 255, 255), 2)
            cv2.line(analysis_frame, (frame_width//2, frame_height//2 - 20), 
                    (frame_width//2, frame_height//2 + 20), (255, 255, 255), 2)
            
            # Write to analysis video
            if hasattr(self, 'analysis_video_writer') and self.analysis_video_writer:
                self.analysis_video_writer.write(analysis_frame)
                
        except Exception as e:
            # Don't log every frame error to avoid spam
            if not hasattr(self, '_video_error_logged'):
                self.log_result(f"❌ Video recording error: {e}")
                self._video_error_logged = True
    
    def create_hold_video_cuts(self):
        """Create video cuts for hold tests"""
        # This would create 1s, 2s, 3s, 5s cuts of hold videos
        self.log_result("✂️ Creating hold video cuts...")
    
    def toggle_recording(self):
        """Toggle recording on/off"""
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def attempt_upload_on_exit(self):
        """Attempt to upload session data when exiting"""
        try:
            if self.session_dir and os.path.exists(self.session_dir):
                print("\n🔄 Attempting to upload session data on exit...")
                from google_drive_uploader import GoogleDriveUploader
                uploader = GoogleDriveUploader()
                if uploader.upload_session(self.session_dir):
                    print("✅ Session data uploaded successfully!")
                else:
                    print("❌ Upload failed - data saved locally")
        except Exception as e:
            print(f"⚠️ Upload on exit failed: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'gaze_detector'):
            self.gaze_detector.cleanup()
        
        # Try to upload session data if available
        self.attempt_upload_on_exit()
