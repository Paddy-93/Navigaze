import time
import numpy as np
from collections import deque
import sys
import os

from config import GAZE_CONFIG

# Pure gaze detector - no external dependencies

class GazeDetector:
    """Detects up/down gaze movements using relative pupil position"""
    
    def __init__(self, threshold_up=None, threshold_down=None, baseline_frames=None, cooldown_ms=None):
        # Use config values or override with parameters
        self.threshold_up = threshold_up or GAZE_CONFIG['threshold_up']
        self.threshold_down = threshold_down or GAZE_CONFIG['threshold_down']
        self.baseline_frames = baseline_frames or GAZE_CONFIG['baseline_frames']
        self.cooldown_ms = cooldown_ms or GAZE_CONFIG['cooldown_ms']
        self.long_gaze_threshold_ms = GAZE_CONFIG['long_gaze_threshold_ms']
        self.arrow_colors = GAZE_CONFIG['arrow_colors']
        
        # State variables
        self.baseline_y = None
        self.samples = []
        self.last_gaze_time = 0
        self.last_gaze_direction = None
        self.current_color_index = 0
        self.last_blink_time = 0
        self.blink_recovery_ms = 400  # Wait 200ms after a blink before detecting gaze
        self.baseline_stable_time = 0
        self.baseline_stable_ms = 300  # Wait 300ms after baseline before detecting gaze
        
        # Gaze state tracking - only fire once per continuous gaze
        self.current_gaze_state = None  # "UP", "DOWN", or None
        self.gaze_already_fired = False  # Prevent multiple fires for same gaze
        self.gaze_start_time = None  # When current gaze started (milliseconds)
        self.gaze_duration_ms = 0    # Duration in milliseconds
        
        # Smart recalibration state
        self.recalibrating = False
        self.head_was_moving = False
        self.head_settled_time = 0
        self.settle_wait_ms = 1000  # Wait 1 second after head stops before recalibrating
        self.recalibration_frames = 0
        self.recalibration_needed_frames = 30  # Same as baseline_frames
        
        # Velocity detection for reading vs intentional movements
        self.recent_positions = deque(maxlen=10)  # Last 10 frames (~300ms at 30fps)
        self.velocity_threshold = 0.17  # Threshold for detecting fast movements (reading)
        self.enable_velocity_filter = True  # Can be toggled on/off
        
        # Pure gaze detection only
        
    def reset_baseline(self):
        """Reset the gaze baseline (called when head moves or blinks)"""
        self.baseline_y = None
        self.samples.clear()
        self.last_gaze_direction = None
        self.current_gaze_state = None
        self.gaze_already_fired = False
        self.recent_positions.clear()  # Clear velocity history too
        # Pure gaze detection - no external state
    
    def set_baseline(self, baseline_value):
        """Set the gaze baseline from external calibration"""
        self.baseline_y = baseline_value
        self.baseline_stable_time = time.time() * 1000  # Set to current time
        print(f"Gaze baseline set to: {self.baseline_y:.3f}")

    # Pure gaze detection methods only
    
    def calculate_velocity(self):
        """Calculate recent eye movement velocity"""
        if len(self.recent_positions) < 3:
            return 0.0
            
        # Calculate average velocity over recent frames
        velocities = []
        for i in range(1, len(self.recent_positions)):
            prev_pos = self.recent_positions[i-1]
            curr_pos = self.recent_positions[i]
            velocity = abs(curr_pos - prev_pos)
            velocities.append(velocity)
            
        return np.mean(velocities) if velocities else 0.0
    
    def is_reading_movement(self, velocity):
        """Detect if current movement looks like reading (fast/jerky)"""
        return self.enable_velocity_filter and velocity > self.velocity_threshold
    
    def update(self, pupil_relative, head_moving=False, is_blinking=False):
        """Update gaze detection with new pupil position"""
        now_ms = time.time() * 1000.0
        
        # No sequence tracking in gaze detector
        
        # Smart recalibration logic
        if head_moving:
            if not self.recalibrating:
                # Significant head movement detected - start recalibration process
                self.recalibrating = True
                self.baseline_y = None  # Invalidate current baseline
                self.samples.clear()
                self.current_gaze_state = None
                self.gaze_already_fired = False
                print("SIGNIFICANT HEAD MOVEMENT - Starting recalibration process")
            self.head_was_moving = True
            return {
                'gaze_detected': False,
                'direction': None,
                'color_index': self.current_color_index,
                'baseline_established': False,
                'disabled_reason': 'RECALIBRATING'
            }
        elif self.head_was_moving:
            # Head just stopped moving
            self.head_was_moving = False
            self.head_settled_time = now_ms
            print("Head stopped - waiting for settle...")
        
        # If we're in recalibration mode
        if self.recalibrating:
            # Wait for head to settle after stopping
            if self.head_settled_time > 0 and now_ms - self.head_settled_time < self.settle_wait_ms:
                return {
                    'gaze_detected': False,
                    'direction': None,
                    'color_index': self.current_color_index,
                    'baseline_established': False,
                    'disabled_reason': 'SETTLING'
                }
            
            # Head has settled, start collecting new baseline if we haven't started yet
            if self.recalibration_frames == 0:
                self.samples = []
                print("RECALIBRATING - LOOK STRAIGHT AHEAD")
            
            # Collect frames for new baseline
            self.samples.append(pupil_relative)
            self.recalibration_frames += 1
            
            if self.recalibration_frames >= self.recalibration_needed_frames:
                # Recalibration complete
                self.baseline_y = sum(self.samples) / len(self.samples)
                self.baseline_stable_time = now_ms
                self.recalibrating = False
                self.head_settled_time = 0
                self.recalibration_frames = 0
                print(f"RECALIBRATION COMPLETE - New baseline: {self.baseline_y:.3f}")
            
            return {
                'gaze_detected': False,
                'direction': None,
                'color_index': self.current_color_index,
                'baseline_established': False,
                'disabled_reason': f'RECALIBRATING ({self.recalibration_frames}/{self.recalibration_needed_frames})'
            }
        
        # If blinking, just disable gaze detection temporarily
        if is_blinking:
            self.last_blink_time = now_ms
            return {
                'gaze_detected': False,
                'direction': None,
                'color_index': self.current_color_index,
                'baseline_established': self.baseline_y is not None,
                'disabled_reason': 'BLINKING'
            }
        
        # Check if we're still in recovery period after a blink
        if now_ms - self.last_blink_time < self.blink_recovery_ms:
            return {
                'gaze_detected': False,
                'direction': None,
                'color_index': self.current_color_index,
                'baseline_established': False,
                'disabled_reason': 'BLINK_RECOVERY'
            }
        
        # Establish baseline for first few frames
        if self.baseline_y is None:
            self.samples.append(pupil_relative)
            if len(self.samples) >= self.baseline_frames:
                self.baseline_y = float(np.mean(self.samples))
                self.baseline_stable_time = now_ms
                print(f"Gaze baseline established: {self.baseline_y:.3f}")
            return {
                'gaze_detected': False,
                'direction': None,
                'color_index': self.current_color_index,
                'baseline_established': False,
                'disabled_reason': None
            }
        
        # Wait for baseline to stabilize
        if now_ms - self.baseline_stable_time < self.baseline_stable_ms:
            return {
                'gaze_detected': False,
                'direction': None,  # Don't return last direction during stabilization
                'color_index': self.current_color_index,
                'baseline_established': True,
                'offset': self.baseline_y - pupil_relative,
                'disabled_reason': 'BASELINE_STABILIZING'
            }
        
        # Add current position to velocity history
        self.recent_positions.append(pupil_relative)
        
        # Calculate movement velocity
        velocity = self.calculate_velocity()
        
        # Check for gaze movement relative to baseline
        gaze_offset = self.baseline_y - pupil_relative
        
        # Check if this looks like reading movement (fast/jerky)
        if self.is_reading_movement(velocity):
            return {
                'gaze_detected': False,
                'direction': None,
                'color_index': self.current_color_index,
                'baseline_established': True,
                'offset': gaze_offset,
                'velocity': velocity,
                'disabled_reason': 'READING_MOVEMENT'
            }
        
        # Determine current physical gaze state with hysteresis
        current_physical_state = None
        
        # Use moderate hysteresis to prevent false opposite direction detections
        if self.current_gaze_state == "UP":
            # Already looking up - need to go more neutral to exit
            if gaze_offset > self.threshold_up * 0.4:  # Stay in UP until 60% closer to neutral
                current_physical_state = "UP"
        elif self.current_gaze_state == "DOWN":
            # Already looking down - need to go more neutral to exit  
            if gaze_offset < -self.threshold_down * 0.4:  # Stay in DOWN until 60% closer to neutral
                current_physical_state = "DOWN"
        else:
            # Currently neutral - use normal thresholds to enter a gaze state
            if gaze_offset > self.threshold_up:
                current_physical_state = "UP"
            elif gaze_offset < -self.threshold_down:
                current_physical_state = "DOWN"
        
        # Check if gaze state changed
        state_changed = current_physical_state != self.current_gaze_state
        if state_changed:
            # Gaze state changed - reset the firing flag and update state
            self.current_gaze_state = current_physical_state
            self.gaze_already_fired = False
            if current_physical_state:  # Starting a new gaze
                self.gaze_start_time = now_ms
            else:  # Going to neutral
                self.gaze_start_time = None
        
        # Calculate duration of current gaze
        if self.gaze_start_time and self.current_gaze_state:
            self.gaze_duration_ms = now_ms - self.gaze_start_time
        else:
            self.gaze_duration_ms = 0
        
        # Fire detection continuously while gazing (for hybrid approach)
        if self.current_gaze_state:
            # Set fired flag on first detection
            if not self.gaze_already_fired:
                self.gaze_already_fired = True
                self.last_gaze_direction = self.current_gaze_state
                self.current_color_index = (self.current_color_index + 1) % len(self.arrow_colors)
                self.last_gaze_time = now_ms
                # print(f"GAZE DETECTED: {self.current_gaze_state} (offset: {gaze_offset:.3f})")  # Disabled for performance
                # print(f"🔍 GAZE DEBUG: Detected {self.current_gaze_state} (offset: {gaze_offset:.3f}, baseline: {self.baseline_y:.3f})")  # Disabled to prevent hanging
            
            # Return continuous gaze detection with duration
            return {
                'gaze_detected': True,
                'direction': self.current_gaze_state,
                'duration': self.gaze_duration_ms,  # Duration in milliseconds
                'is_long_gaze': self.gaze_duration_ms > self.long_gaze_threshold_ms,  # Configurable threshold
                'baseline_established': True,
                'offset': gaze_offset,
                'velocity': velocity,
                'disabled_reason': None
            }
        
        # No sequence tracking in gaze detector
        
        # No new gaze detected (but may still be in a gaze state)
        return {
            'gaze_detected': False,
            'direction': self.current_gaze_state,  # Return current physical state for morse handler
            'color_index': self.current_color_index,
            'baseline_established': True,
            'offset': gaze_offset,
            'velocity': velocity,
            'disabled_reason': None
        }
    
    def get_baseline_status(self):
        """Get current baseline status for display"""
        if self.baseline_y is None:
            return f"GAZE CALIB: {len(self.samples)}/{self.baseline_frames}"
        else:
            return "GAZE READY"