#!/usr/bin/env python3
"""
Unit test for hold detection logic
This tests the hold detection without requiring the full GUI
"""

import time
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from eye_tracking.gaze_detector import GazeDetector
from eye_tracking.face_landmarks import FaceLandmarks

class HoldDetectionTester:
    def __init__(self):
        self.gaze_detector = GazeDetector()
        self.face_landmarks = FaceLandmarks()
        
        # Test state
        self.step_data = {
            'detections': [],
            'start_time': time.time(),
            'current_gaze_state': None,
            'hold_start_time': None
        }
        
        self.test_steps = [
            {
                'name': 'Long UP Holds',
                'type': 'long_up',
                'repetitions': 3,
                'hold_duration': 5
            }
        ]
        
    def process_simulated_gaze(self, direction, is_continuous=False, gaze_detected=True):
        """Process a simulated gaze input"""
        gaze_result = {
            'direction': direction,
            'offset': 0.02 if direction == 'UP' else -0.02,
            'is_continuous_gaze': is_continuous,
            'gaze_detected': gaze_detected,
            'pupil_relative': (0.5, 0.3 if direction == 'UP' else 0.7),
            'confidence': 0.9
        }
        
        return self.process_step_gaze(gaze_result)
        
    def process_step_gaze(self, gaze_result):
        """Process gaze detection for current step (simplified version)"""
        if not self.step_data:
            return
            
        # Process both new gaze detections and continuous gaze states
        direction = gaze_result.get('direction')
        is_continuous = gaze_result.get('is_continuous_gaze', False)
        gaze_detected = gaze_result.get('gaze_detected', False)
        
        print(f"[TEST] GAZE: {direction} | continuous: {is_continuous} | detected: {gaze_detected}")
        
        # Handle neutral gaze (no direction) - reset hold tracking
        if not direction and self.step_data:
            step = self.test_steps[0]  # Test with first step
            if step['type'] in ['long_up', 'long_down']:
                if 'current_gaze_state' in self.step_data and self.step_data['current_gaze_state']:
                    print(f"[TEST] NEUTRAL GAZE - resetting hold tracking (was {self.step_data['current_gaze_state']})")
                    self.step_data['current_gaze_state'] = None
                    self.step_data['hold_start_time'] = None
        
        # Process gaze results if we have a direction OR if we're already tracking a hold
        if direction or (self.step_data and 
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
                step = self.test_steps[0]  # Test with first step
                if step['type'] in ['long_up', 'long_down']:
                    required_duration = step.get('hold_duration', 5)  # Default 5 seconds
                    target_direction = 'UP' if step['type'] == 'long_up' else 'DOWN'
                    
                    # Initialize tracking variables (only once)
                    if 'current_gaze_state' not in self.step_data:
                        self.step_data['current_gaze_state'] = None
                        print(f"[TEST] INITIALIZED current_gaze_state to None")
                    if 'hold_start_time' not in self.step_data:
                        self.step_data['hold_start_time'] = None
                        print(f"[TEST] INITIALIZED hold_start_time to None")
                    
                    # Track gaze state changes (like the main script does)
                    if direction == target_direction:
                        # We're looking in the target direction
                        print(f"[TEST] Looking {target_direction}, current_state={self.step_data.get('current_gaze_state', None)}")
                        if self.step_data['current_gaze_state'] != target_direction:
                            # New gaze detected - record start time
                            self.step_data['current_gaze_state'] = target_direction
                            self.step_data['hold_start_time'] = time.time()
                            print(f"[TEST] NEW GAZE DETECTED - starting hold tracking")
                        elif self.step_data['current_gaze_state'] == target_direction:
                            # Continuing the same gaze - check duration
                            if self.step_data['hold_start_time']:
                                hold_duration = time.time() - self.step_data['hold_start_time']
                                print(f"[TEST] CONTINUING GAZE - hold_duration={hold_duration:.1f}s")
                                
                                # Check if hold duration is met
                                if hold_duration >= required_duration:
                                    print(f"[TEST] HOLD COMPLETED - registering hold")
                                    # Register this hold completion
                                    detection['hold_duration'] = hold_duration
                                    self.step_data['detections'].append(detection)
                                    
                                    # Reset tracking to prevent multiple registrations
                                    self.step_data['current_gaze_state'] = None
                                    self.step_data['hold_start_time'] = None
                                    
                                    print(f"[TEST] ✅ LONG {target_direction} hold completed ({hold_duration:.1f}s)")
                                    return True  # Hold completed
                    else:
                        # Looking in wrong direction - reset tracking
                        if self.step_data['current_gaze_state'] == target_direction:
                            self.step_data['current_gaze_state'] = None
                            self.step_data['hold_start_time'] = None
                            print(f"[TEST] Gaze changed to {direction} - reset hold tracking")
            else:
                # No direction in this frame, but we might be tracking a hold
                if ('current_gaze_state' in self.step_data and 
                    self.step_data['current_gaze_state'] and
                    'hold_start_time' in self.step_data and 
                    self.step_data['hold_start_time']):
                    
                    # Continue tracking the hold even without direction
                    hold_duration = time.time() - self.step_data['hold_start_time']
                    print(f"[TEST] CONTINUING HOLD WITHOUT DIRECTION - hold_duration={hold_duration:.1f}s")
                    
                    # Check if hold duration is met
                    step = self.test_steps[0]
                    required_duration = step.get('hold_duration', 5)
                    if hold_duration >= required_duration:
                        print(f"[TEST] HOLD COMPLETED WITHOUT DIRECTION - registering hold")
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
                        
                        print(f"[TEST] ✅ LONG {self.step_data['current_gaze_state']} hold completed ({hold_duration:.1f}s)")
                        return True  # Hold completed
        
        return False  # No hold completed
        
    def test_single_hold(self):
        """Test a single 5-second hold"""
        print("🧪 Testing single 5-second UP hold")
        print("=" * 40)
        
        # Simulate 5 seconds of UP gaze
        start_time = time.time()
        hold_completed = False
        
        while time.time() - start_time < 6 and not hold_completed:  # Run for 6 seconds max
            # Simulate continuous UP gaze
            hold_completed = self.process_simulated_gaze('UP', is_continuous=True, gaze_detected=False)
            time.sleep(0.1)  # 100ms intervals
            
        if hold_completed:
            print("✅ Test PASSED: Hold was completed successfully")
        else:
            print("❌ Test FAILED: Hold was not completed")
            
        print(f"Total detections: {len(self.step_data['detections'])}")
        for i, detection in enumerate(self.step_data['detections']):
            print(f"  Detection {i+1}: {detection}")
            
    def test_multiple_holds(self):
        """Test multiple holds with neutral breaks"""
        print("\n🧪 Testing multiple 5-second UP holds with neutral breaks")
        print("=" * 60)
        
        # Reset state
        self.step_data = {
            'detections': [],
            'start_time': time.time(),
            'current_gaze_state': None,
            'hold_start_time': None
        }
        
        # Test 3 holds
        for hold_num in range(3):
            print(f"\n--- Hold {hold_num + 1}/3 ---")
            
            # Simulate 5 seconds of UP gaze
            start_time = time.time()
            hold_completed = False
            
            while time.time() - start_time < 6 and not hold_completed:
                hold_completed = self.process_simulated_gaze('UP', is_continuous=True, gaze_detected=False)
                time.sleep(0.1)
                
            if hold_completed:
                print(f"✅ Hold {hold_num + 1} completed")
            else:
                print(f"❌ Hold {hold_num + 1} failed")
                
            # Brief neutral break between holds
            if hold_num < 2:  # Don't add neutral after last hold
                print("  Neutral break...")
                for _ in range(10):  # 1 second of neutral
                    self.process_simulated_gaze(None, is_continuous=False, gaze_detected=False)
                    time.sleep(0.1)
                    
        print(f"\nTotal holds completed: {len(self.step_data['detections'])}")
        for i, detection in enumerate(self.step_data['detections']):
            print(f"  Hold {i+1}: {detection['direction']} for {detection.get('hold_duration', 0):.1f}s")

def main():
    """Run the hold detection tests"""
    print("🧪 Hold Detection Unit Tests")
    print("=" * 50)
    
    tester = HoldDetectionTester()
    
    # Test single hold
    tester.test_single_hold()
    
    # Test multiple holds
    tester.test_multiple_holds()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()
