#!/usr/bin/env python3
"""
Simulated Gaze Detector
Implementation of GazeDetectorInterface for testing and simulation
"""

import time
import threading
from typing import Dict, Any, Optional, Tuple
from gaze_detector_interface import GazeDetectorInterface

class SimulatedGazeDetector(GazeDetectorInterface):
    """Simulated gaze detector for testing and simulation"""
    
    def __init__(self):
        self.initialized = False
        self.ready = False
        self.current_gaze = None
        self.tester_instance = None
        self.test_running = False
        self.current_step_type = None
        self.step_start_time = 0
        self.simulation_timer = None
        self.auto_simulate = False  # Disabled by default for automated testing
        self.calibration_data = {
            'left_eye': {'x': 0.3, 'y': 0.3},
            'right_eye': {'x': 0.7, 'y': 0.3},
            'nose': {'x': 0.5, 'y': 0.5}
        }
        # For realistic simulation
        self.mock_pupil_data = None
        self.simulated_gaze_active = False
        self.simulated_gaze_start_time = 0
        self.simulated_gaze_duration = 0
        self.simulated_gaze_direction = None
        self.simulated_gaze_is_long = False
        self.baseline_y = 0.5  # Default baseline for simulation
        
    def initialize(self) -> bool:
        """Initialize the simulated gaze detector"""
        try:
            self.initialized = True
            self.ready = True
            print("🎭 Simulated gaze detector initialized")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize simulated gaze detector: {e}")
            return False
    
    def update(self) -> Optional[Dict[str, Any]]:
        """Update gaze detection and return current gaze state"""
        if not self.ready:
            return None
            
        # Check for active simulated gaze
        if self.simulated_gaze_active:
            return self._get_active_simulated_gaze()
            
        # Return mock pupil data for calibration if available
        if self.mock_pupil_data:
            result = self._create_gaze_result(None, False, True)
            result['pupil_relative'] = self.mock_pupil_data
            return result
            
        # Default neutral state
        return self._create_gaze_result(None, False, False)
    
    def cleanup(self) -> None:
        """Clean up resources"""
        self.test_running = False
        if self.simulation_timer:
            self.simulation_timer.cancel()
        print("🎭 Simulated gaze detector cleaned up")
    
    def is_ready(self) -> bool:
        """Check if the gaze detector is ready for use"""
        return self.ready
    
    def start_test_simulation(self, test_steps: list, tester_instance=None) -> None:
        """Start a test simulation with the given test steps"""
        self.tester_instance = tester_instance
        self.test_running = True
        
        print(f"🎭 Simulation ready - starting test...")
        
        # Auto-start the test if we have a tester instance
        if self.tester_instance and hasattr(self.tester_instance, 'start_test'):
            print("🎭 Auto-starting test...")
            self.tester_instance.start_test()
        
        # Disable automatic simulation - let the automated test handle it
        self.auto_simulate = False
    
    def start_step_simulation(self, step_type: str, step_data: dict) -> None:
        """Start simulation for a specific test step"""
        self.current_step_type = step_type
        self.step_start_time = time.time()
        
        print(f"🎭 Starting simulation for {step_type} step")
        
        # Only schedule simulation if auto_simulate is enabled
        if not hasattr(self, 'auto_simulate') or self.auto_simulate:
            # Schedule gaze inputs based on step type
            if step_type == 'calibration':
                # For calibration, we don't provide any gaze input
                pass
            elif step_type == 'long_up':
                self._schedule_long_holds('UP', step_data.get('repetitions', 3), step_data.get('hold_duration', 5))
            elif step_type == 'long_down':
                self._schedule_long_holds('DOWN', step_data.get('repetitions', 3), step_data.get('hold_duration', 5))
            elif step_type == 'neutral_hold':
                self._schedule_neutral_hold(step_data.get('hold_duration', 5))
            elif step_type.startswith('sequence_'):
                pattern = step_data.get('pattern', [])
                repetitions = step_data.get('repetitions', 3)
                self._schedule_sequence(pattern, repetitions)
    
    def _schedule_long_holds(self, direction: str, repetitions: int, hold_duration: float):
        """Schedule long hold gazes with proper timing"""
        delay = 0
        for i in range(repetitions):
            # Start the hold
            self.simulation_timer = threading.Timer(delay, self._start_hold, args=[direction, hold_duration])
            self.simulation_timer.start()
            delay += hold_duration + 1.0  # 1 second break between holds
    
    def _schedule_neutral_hold(self, hold_duration: float):
        """Schedule neutral hold"""
        self.simulation_timer = threading.Timer(0, self._start_neutral_hold, args=[hold_duration])
        self.simulation_timer.start()
    
    def _schedule_sequence(self, pattern: list, repetitions: int):
        """Schedule sequence pattern"""
        delay = 0
        for rep in range(repetitions):
            for direction in pattern:
                # Quick gaze
                self.simulation_timer = threading.Timer(delay, self._start_quick_gaze, args=[direction])
                self.simulation_timer.start()
                delay += 0.5  # 0.5 second per gaze
            delay += 0.5  # Brief pause between sequences
    
    def _start_hold(self, direction: str, duration: float):
        """Start a long hold gaze"""
        print(f"🎭 Starting {direction} hold for {duration}s")
        self.current_gaze = {
            'direction': direction,
            'is_continuous': True,
            'gaze_detected': False,
            'start_time': time.time(),
            'duration': duration
        }
    
    def _start_neutral_hold(self, duration: float):
        """Start neutral hold"""
        print(f"🎭 Starting neutral hold for {duration}s")
        self.current_gaze = {
            'direction': None,
            'is_continuous': False,
            'gaze_detected': False,
            'start_time': time.time(),
            'duration': duration
        }
    
    def _start_quick_gaze(self, direction: str):
        """Start a quick gaze"""
        print(f"🎭 Quick {direction} gaze")
        self.current_gaze = {
            'direction': direction,
            'is_continuous': False,
            'gaze_detected': True,
            'start_time': time.time(),
            'duration': 0.1
        }
    
    def _get_simulated_gaze(self) -> Dict[str, Any]:
        """Get current simulated gaze state"""
        if not self.current_gaze:
            return self._create_gaze_result(None, False, False)
        
        elapsed = time.time() - self.current_gaze['start_time']
        
        # Check if gaze duration is complete
        if elapsed >= self.current_gaze['duration']:
            # Gaze complete, return neutral
            self.current_gaze = None
            return self._create_gaze_result(None, False, False)
        
        # Only return gaze_detected=True on the first call, then False for the rest
        if self.current_gaze.get('first_call', True):
            self.current_gaze['first_call'] = False  # Set to False after first call
            gaze_detected = True
        else:
            gaze_detected = False
        
        # Return current gaze
        return self._create_gaze_result(
            self.current_gaze['direction'],
            self.current_gaze['is_continuous'],
            gaze_detected
        )
    
    def _create_gaze_result(self, direction: Optional[str], is_continuous: bool, gaze_detected: bool) -> Dict[str, Any]:
        """Create a gaze result dictionary"""
        return {
            'direction': direction,
            'offset': 0.02 if direction == 'UP' else -0.02 if direction == 'DOWN' else 0,
            'is_continuous_gaze': is_continuous,
            'gaze_detected': gaze_detected,
            'pupil_relative': (
                0.5, 
                0.3 if direction == 'UP' else 0.7 if direction == 'DOWN' else 0.5
            ),
            'confidence': 0.9
        }
    
    def calibrate(self, frame_data: Dict[str, Any]) -> bool:
        """Mock calibration - always succeeds"""
        # Set baseline from calibration data if available
        if frame_data and 'pupil_relative' in frame_data:
            pupil_relative = frame_data['pupil_relative']
            if isinstance(pupil_relative, (tuple, list)) and len(pupil_relative) > 1:
                self.baseline_y = pupil_relative[1]  # Use y coordinate
            elif isinstance(pupil_relative, (int, float)):
                self.baseline_y = pupil_relative
        print(f"🎭 Mock calibration completed - baseline_y: {self.baseline_y}")
        return True
    
    def reset_calibration(self) -> None:
        """Reset calibration"""
        print("🎭 Mock calibration reset")
    
    def get_current_frame(self):
        """Get a mock camera frame for video recording"""
        try:
            import cv2
            import numpy as np
            
            # Create a mock frame that looks like a webcam feed
            frame_width = 640
            frame_height = 480
            frame = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
            
            # Add some visual elements to make it look like a real webcam feed
            # Add a subtle gradient background
            for y in range(frame_height):
                color_value = int(30 + (y / frame_height) * 20)
                frame[y, :] = [color_value, color_value, color_value]
            
            # Add a simple face-like circle
            center = (frame_width//2, frame_height//2)
            cv2.circle(frame, center, 80, (100, 100, 100), 2)
            
            # Add eyes
            cv2.circle(frame, (center[0] - 30, center[1] - 20), 10, (200, 200, 200), -1)
            cv2.circle(frame, (center[0] + 30, center[1] - 20), 10, (200, 200, 200), -1)
            
            # Add nose
            cv2.circle(frame, (center[0], center[1]), 5, (150, 150, 150), -1)
            
            # Add mouth
            cv2.ellipse(frame, (center[0], center[1] + 20), (20, 10), 0, 0, 180, (150, 150, 150), 2)
            
            # Add timestamp
            timestamp = time.strftime("%H:%M:%S")
            cv2.putText(frame, f"SIM: {timestamp}", (10, frame_height - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            return frame
            
        except Exception as e:
            print(f"Error creating mock frame: {e}")
            return None
    
    def release(self) -> None:
        """Release resources"""
        self.cleanup()
    
    def start_simulated_gaze(self, direction: str, duration: float, is_long: bool = False):
        """Start a simulated gaze in the specified direction"""
        print(f"🎭 Starting simulated {direction} gaze for {duration}s (long: {is_long})")
        self.simulated_gaze_active = True
        self.simulated_gaze_start_time = time.time()
        self.simulated_gaze_duration = duration
        self.simulated_gaze_direction = direction
        self.simulated_gaze_is_long = is_long
        
        # Reset first call flag for new gaze
        self.gaze_first_call = True
        
        # Schedule end of gaze
        if self.simulation_timer:
            self.simulation_timer.cancel()
        self.simulation_timer = threading.Timer(duration, self._end_simulated_gaze)
        self.simulation_timer.start()
    
    def start_simulated_neutral(self, duration: float):
        """Start a simulated neutral state"""
        print(f"🎭 Starting simulated neutral for {duration}s")
        self.simulated_gaze_active = True
        self.simulated_gaze_start_time = time.time()
        self.simulated_gaze_duration = duration
        self.simulated_gaze_direction = None
        self.simulated_gaze_is_long = False
        
        # Schedule end of neutral
        if self.simulation_timer:
            self.simulation_timer.cancel()
        self.simulation_timer = threading.Timer(duration, self._end_simulated_gaze)
        self.simulation_timer.start()
    
    def _get_active_simulated_gaze(self) -> Dict[str, Any]:
        """Get the current active simulated gaze result"""
        elapsed = time.time() - self.simulated_gaze_start_time
        
        # Check if gaze should still be active
        if elapsed >= self.simulated_gaze_duration:
            self._end_simulated_gaze()
            return self._create_gaze_result(None, False, False)
        
        # Return simulated gaze result
        is_continuous = self.simulated_gaze_is_long and elapsed >= 1.0  # Long gaze after 1 second
        
        # Only return gaze_detected=True on the first call, then False for the rest
        if not hasattr(self, 'gaze_first_call') or self.gaze_first_call:
            self.gaze_first_call = False  # Set to False after first call
            gaze_detected = True
        else:
            gaze_detected = False
        
        result = self._create_gaze_result(self.simulated_gaze_direction, is_continuous, gaze_detected)
        
        # Add duration info for long gazes
        if self.simulated_gaze_is_long:
            result['gaze_duration_ms'] = int(elapsed * 1000)
            result['hold_duration'] = elapsed if elapsed >= 5.0 else 0  # Hold registered after 5 seconds
        
        return result
    
    def _end_simulated_gaze(self):
        """End the current simulated gaze"""
        if self.simulated_gaze_active:
            direction = self.simulated_gaze_direction or "NEUTRAL"
            print(f"🎭 Ended simulated {direction} gaze")
            self.simulated_gaze_active = False
            self.simulated_gaze_direction = None
            self.simulated_gaze_is_long = False