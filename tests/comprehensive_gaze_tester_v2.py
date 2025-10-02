#!/usr/bin/env python3
"""
Comprehensive Gaze Testing System - Version 2 (Clean Implementation)
Uses dependency injection for gaze detection

CLEAN FLOW FOR ALL STEPS:
1. Step starts → Update UI
2. Start recording (parallel) + Start TTS (parallel)
3. Wait for both: recording_ready=True AND tts_complete=True
4. Wait 1 second
5. Play beep
6. Execute step (calibration or gaze detection)
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

class ComprehensiveGazeTesterV2:
    def __init__(self, master, gaze_detector: GazeDetectorInterface):
        self.root = master
        self.root.title("Comprehensive Gaze Testing System V2")
        self.root.geometry("1000x700")
        
        # Store the injected gaze detector
        self.gaze_detector = gaze_detector
        
        # Center the window on screen
        self.center_window()
        
        # Test state
        self.test_running = False
        self.current_step = 0
        self.step_data = None
        self.step_start_time = 0
        self.test_results = []
        
        # Recording state
        self.session_dir = None
        self.current_step_dir = None
        self.raw_video_writer = None
        self.analysis_video_writer = None
        self.recording_active = True  # Always record
        
        # Step coordination flags
        self.recording_ready = False
        self.tts_complete = False
        
        # TTS
        self.tts_engine = None
        self.tts_queue = []
        self.tts_speaking = False
        self.tts_callbacks = []
        self.max_tts_length = 200
        self.tts_timeout_timer = None
        
        # Timeout management
        self.step_timeout_timer = None
        
        # Test steps definition
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
                'name': 'Calibration',
                'type': 'calibration',
                'instruction': 'Look at the red dot and keep your head still. Wait for the beep to begin.'
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
                'instruction': 'Look at the red dot. Wait for the beep to begin.'
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
                print("✅ TTS engine initialized")
            except Exception as e:
                print(f"❌ Failed to initialize TTS: {e}")
                self.tts_engine = None
        
        # Setup UI
        self.setup_ui()
        
        # Start camera updates
        self.root.after(33, self.update_camera)
        
        # Show starting screen
        self.show_starting_screen()
        
        # Register cleanup
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
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
        # Main instruction display (large, centered)
        self.instruction_display = tk.Label(
            self.root,
            text="STARTING...",
            font=("Arial", 24, "bold"),
            fg="white",
            bg="darkblue",
            wraplength=900,
            justify="center"
        )
        self.instruction_display.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Status bar at bottom
        status_frame = tk.Frame(self.root, bg="lightgray")
        status_frame.pack(fill="x", side="bottom")
        
        self.status_label = tk.Label(
            status_frame,
            text="Initializing...",
            font=("Arial", 12),
            bg="lightgray"
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Hidden start button (for programmatic use)
        self.start_button = tk.Button(
            status_frame,
            text="Start Test",
            command=self.start_test,
            font=("Arial", 12)
        )
        # Don't pack it - keep it hidden
    
    def show_starting_screen(self):
        """Show starting screen for 3 seconds then auto-start"""
        self.instruction_display.config(
            text="STARTING...",
            fg="white",
            bg="darkblue"
        )
        # Force window to front immediately
        self._force_to_front()
        self.root.after(3000, self.auto_start_test)
    
    def auto_start_test(self):
        """Automatically start the test"""
        self.start_test()
    
    def start_test(self):
        """Start the comprehensive test"""
        if self.test_running:
            return
        
        print("🚀 Starting comprehensive gaze test")
        self.test_running = True
        self.current_step = 0
        
        # Create session directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        self.session_dir = os.path.join("test_sessions", f"session_{timestamp}")
        os.makedirs(self.session_dir, exist_ok=True)
        print(f"📁 Session directory: {self.session_dir}")
        
        # Start first step
        self.execute_current_step()
        
        # Force window to front
        self._force_to_front()
        self.root.attributes('-topmost', True)
        
        # Update UI
        self.status_label.config(text="Test Running")
    
    def _force_to_front(self):
        """Force window to front (macOS specific)"""
        try:
            if sys.platform == 'darwin':
                # Try multiple methods for macOS
                subprocess.run([
                    'osascript', '-e',
                    'tell application "System Events" to set frontmost of the first process whose unix id is ' + str(os.getpid()) + ' to true'
                ], check=False, capture_output=True, timeout=1)
        except:
            pass
        
        # Universal methods
        self.root.lift()
        self.root.focus_force()
        self.root.attributes('-topmost', True)
        self.root.update()
        self.root.after(100, lambda: self.root.attributes('-topmost', False))  # Remove topmost after display
    
    def execute_current_step(self):
        """
        Execute the current test step with clean flow:
        1. Update UI
        2. Start recording + Start TTS (parallel)
        3. Wait for both complete
        4. Wait 1 second
        5. Play beep
        6. Execute step
        """
        if self.current_step >= len(self.test_steps):
            print("✅ All steps completed")
            self.complete_test()
            return
        
        step = self.test_steps[self.current_step]
        print(f"\n{'='*60}")
        print(f"🎬 STEP {self.current_step + 1}/{len(self.test_steps)}: {step['name']}")
        print(f"{'='*60}")
        
        # Set step start time
        self.step_start_time = time.time()
        
        # Cancel any existing timeout
        if self.step_timeout_timer:
            self.root.after_cancel(self.step_timeout_timer)
        
        # Create step directory
        step_dir = os.path.join(
            self.session_dir,
            f"step_{self.current_step:02d}_{step['name'].lower().replace(' ', '_')}"
        )
        os.makedirs(step_dir, exist_ok=True)
        self.current_step_dir = step_dir
        
        # Log baseline
        self.log_step_baseline(step)
        
        # Update UI
        if step['type'] == 'calibration':
            self.show_calibration_display()
        else:
            instruction_text = f"STEP {self.current_step + 1}/{len(self.test_steps)}\n\n{step['name'].upper()}\n\n{step['instruction']}"
            self.instruction_display.config(text=instruction_text, fg="white", bg="darkblue")
            self.root.update()
        
        # Force window to front for each step
        self._force_to_front()
        
        # Reset coordination flags
        self.recording_ready = False
        self.tts_complete = False
        
        # Initialize step data
        self.step_data = {
            'detections': [],
            'start_time': time.time(),
            'current_gaze_state': None,
            'hold_start_time': None
        }
        
        # START PARALLEL EXECUTION
        # 1. Start recording
        self.start_step_recording()
        
        # 2. Start TTS
        self.start_step_tts(step)
    
    def start_step_tts(self, step):
        """Start TTS for current step"""
        def on_tts_done():
            print("✅ TTS complete")
            self.tts_complete = True
            self.check_step_ready()
        
        if not self.tts_engine:
            print("⚠️ TTS not available - marking complete")
            self.tts_complete = True
            self.check_step_ready()
        else:
            print(f"🔊 Starting TTS: '{step['instruction'][:50]}...'")
            self.speak(step['instruction'], on_tts_done)
    
    def start_step_recording(self):
        """Start recording for current step"""
        step = self.test_steps[self.current_step]
        step_dir = self.current_step_dir
        
        try:
            # Create video writers
            raw_video_path = os.path.join(step_dir, f"{step['name'].lower().replace(' ', '_')}_raw.mp4")
            analysis_video_path = os.path.join(step_dir, f"{step['name'].lower().replace(' ', '_')}_analysis.mp4")
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = 15
            frame_width = 640
            frame_height = 480
            
            self.raw_video_writer = cv2.VideoWriter(raw_video_path, fourcc, fps, (frame_width, frame_height))
            self.analysis_video_writer = cv2.VideoWriter(analysis_video_path, fourcc, fps, (frame_width, frame_height))
            
            print(f"📹 Recording initialized: {step['name']}")
            print(f"   Raw: {raw_video_path}")
            print(f"   Analysis: {analysis_video_path}")
            
            # Mark recording as ready
            self.recording_ready = True
            self.check_step_ready()
            
        except Exception as e:
            print(f"❌ Failed to initialize recording: {e}")
            self.recording_ready = True  # Continue anyway
            self.check_step_ready()
    
    def check_step_ready(self):
        """Check if both recording and TTS are complete, then proceed"""
        print(f"🔍 Checking readiness: Recording={self.recording_ready}, TTS={self.tts_complete}")
        
        if self.recording_ready and self.tts_complete:
            print("✅ Both ready - waiting 1 second before beep")
            self.root.after(1000, self.play_beep_and_start)
    
    def play_beep_and_start(self):
        """Play beep and start step execution"""
        print("🔊 Playing beep...")
        self.play_beep_async()
        
        # Start step execution after beep
        self.root.after(500, self.execute_step_action)
    
    def execute_step_action(self):
        """Execute the actual step action (calibration or gaze detection)"""
        step = self.test_steps[self.current_step]
        print(f"🎬 Executing step action: {step['name']}")
        
        if step['type'] == 'calibration':
            self.execute_calibration()
        else:
            self.execute_gaze_detection(step)
    
    def execute_calibration(self):
        """Execute calibration step"""
        # Calibration will be implemented
        print("🎯 Calibration started")
        # For now, just complete after 5 seconds
        self.root.after(5000, self.complete_current_step)
    
    def execute_gaze_detection(self, step):
        """Execute gaze detection step"""
        print(f"👁️ Gaze detection started for: {step['type']}")
        
        # Set timeout
        max_duration = step.get('duration', 60)
        self.step_timeout_timer = self.root.after(int(max_duration * 1000), self.complete_current_step)
        print(f"⏱️ Timeout set for {max_duration}s")
        
        # Start simulation if available
        if hasattr(self.gaze_detector, 'start_step_simulation'):
            auto_simulate = not hasattr(self.gaze_detector, 'auto_simulate') or self.gaze_detector.auto_simulate
            if auto_simulate:
                self.gaze_detector.start_step_simulation(step['type'], step)
    
    def complete_current_step(self):
        """Complete current step and move to next"""
        print(f"✅ Step {self.current_step + 1} complete")
        
        # Stop recording
        self.stop_step_recording()
        
        # Move to next step
        self.current_step += 1
        self.root.after(500, self.execute_current_step)
    
    def stop_step_recording(self):
        """Stop recording for current step"""
        if self.raw_video_writer:
            self.raw_video_writer.release()
            self.raw_video_writer = None
        if self.analysis_video_writer:
            self.analysis_video_writer.release()
            self.analysis_video_writer = None
        print("⏹️ Recording stopped")
    
    def show_calibration_display(self):
        """Show calibration display with red dot"""
        self.instruction_display.config(text="", fg="white", bg="black")
        
        # Create canvas if doesn't exist
        if hasattr(self, 'calibration_canvas'):
            self.calibration_canvas.destroy()
        
        self.calibration_canvas = tk.Canvas(
            self.root,
            width=1000,
            height=600,
            bg="black",
            highlightthickness=0
        )
        self.calibration_canvas.place(x=0, y=50)
        
        # Draw centered red dot
        center_x = 500
        center_y = 300
        dot_radius = 30
        
        self.calibration_canvas.create_oval(
            center_x - dot_radius,
            center_y - dot_radius,
            center_x + dot_radius,
            center_y + dot_radius,
            fill="red",
            outline=""
        )
        
        # Add text above dot
        self.calibration_canvas.create_text(
            center_x,
            center_y - 80,
            text="Look at the red dot",
            font=("Arial", 24, "bold"),
            fill="white"
        )
    
    def log_step_baseline(self, step):
        """Log baseline data for step"""
        baseline_data = {
            'step_name': step['name'],
            'step_type': step['type'],
            'step_index': self.current_step,
            'timestamp': datetime.now().isoformat()
        }
        
        baseline_file = os.path.join(self.current_step_dir, 'baseline_data.json')
        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2)
        print(f"📊 Baseline logged: {baseline_file}")
    
    # ===== TTS METHODS =====
    
    def speak(self, text, callback=None):
        """Speak text with optional callback"""
        if self.tts_engine and text:
            if len(text) > self.max_tts_length:
                text = text[:self.max_tts_length] + "..."
            
            if callback:
                self.tts_callbacks.append(callback)
            
            self.tts_queue.append(text)
            self._process_tts_queue()
    
    def _process_tts_queue(self):
        """Process TTS queue"""
        if not self.tts_speaking and self.tts_queue:
            self.tts_speaking = True
            text = self.tts_queue.pop(0)
            
            # Set timeout
            self.tts_timeout_timer = self.root.after(10000, self._tts_timeout)
            
            def speak_text():
                try:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                    self.root.after(0, self._on_tts_finished)
                except Exception as e:
                    print(f"❌ TTS error: {e}")
                    self.root.after(0, self._on_tts_finished)
            
            threading.Thread(target=speak_text, daemon=True).start()
    
    def _tts_timeout(self):
        """Handle TTS timeout"""
        print("⚠️ TTS timeout")
        self._on_tts_finished()
    
    def _on_tts_finished(self):
        """Called when TTS finishes"""
        self.tts_speaking = False
        
        if self.tts_timeout_timer:
            self.root.after_cancel(self.tts_timeout_timer)
            self.tts_timeout_timer = None
        
        if self.tts_callbacks:
            callback = self.tts_callbacks.pop(0)
            self.root.after(0, callback)
        
        if self.tts_queue:
            self.root.after(100, self._process_tts_queue)
    
    def play_beep_async(self):
        """Play beep sound"""
        def play_beep():
            try:
                import winsound
                winsound.Beep(1000, 200)
            except ImportError:
                try:
                    os.system('afplay /System/Library/Sounds/Ping.aiff')
                except:
                    try:
                        os.system('paplay /usr/share/sounds/alsa/Front_Left.wav')
                    except:
                        print("\a")
        
        threading.Thread(target=play_beep, daemon=True).start()
    
    # ===== CAMERA AND CLEANUP =====
    
    def update_camera(self):
        """Update camera and gaze detection"""
        if self.test_running and self.gaze_detector:
            gaze_result = self.gaze_detector.update()
            # Process gaze results here
        
        try:
            self.root.after(33, self.update_camera)
        except:
            pass
    
    def complete_test(self):
        """Complete the entire test"""
        print("🎉 Test completed!")
        self.test_running = False
        self.instruction_display.config(
            text="TEST COMPLETE\n\nResults saved!",
            fg="white",
            bg="darkgreen"
        )
        self.root.after(2000, self.root.quit)
    
    def cleanup(self):
        """Cleanup resources"""
        print("🧹 Cleaning up...")
        if self.gaze_detector:
            self.gaze_detector.release()
    
    def signal_handler(self, sig, frame):
        """Handle interrupt signal"""
        print("\n⚠️ Interrupt received")
        self.cleanup()
        sys.exit(0)
    
    def on_closing(self):
        """Handle window close"""
        self.cleanup()
        self.root.destroy()


if __name__ == "__main__":
    print("❌ This file should be imported and used with a gaze detector")
    print("   Use gaze_reporting/gaze_reporter.py or tests/comprehensive_gaze_tester_sim.py")

