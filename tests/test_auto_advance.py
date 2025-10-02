#!/usr/bin/env python3
"""
Test script to verify auto-advance functionality
This simulates the test steps to ensure auto-advance works correctly
"""

import time
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class AutoAdvanceTester:
    def __init__(self):
        # Simulate the test steps
        self.test_steps = [
            {
                'name': 'Long UP Holds',
                'type': 'long_up',
                'repetitions': 3,
                'hold_duration': 5
            },
            {
                'name': 'Long DOWN Holds',
                'type': 'long_down', 
                'repetitions': 3,
                'hold_duration': 5
            },
            {
                'name': 'Neutral Hold',
                'type': 'neutral_hold',
                'hold_duration': 5
            }
        ]
        
        self.current_step = 0
        self.step_data = None
        self.test_results = []
        
    def simulate_gaze_result(self, direction, is_continuous=False, gaze_detected=True):
        """Simulate a gaze result"""
        return {
            'direction': direction,
            'offset': 0.02 if direction == 'UP' else -0.02,
            'is_continuous_gaze': is_continuous,
            'gaze_detected': gaze_detected,
            'pupil_relative': (0.5, 0.3 if direction == 'UP' else 0.7),
            'confidence': 0.9
        }
        
    def check_step_completion(self):
        """Check if current step is complete and should auto-advance"""
        if not self.step_data:
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
            
        return False
        
    def process_step_gaze(self, gaze_result):
        """Process gaze detection for current step (simplified version)"""
        if not self.step_data:
            return
            
        # Process both new gaze detections and continuous gaze states
        direction = gaze_result.get('direction')
        is_continuous = gaze_result.get('is_continuous_gaze', False)
        gaze_detected = gaze_result.get('gaze_detected', False)
        
        # Handle neutral gaze (no direction) - reset hold tracking
        if not direction and self.step_data:
            step = self.test_steps[self.current_step]
            if step['type'] in ['long_up', 'long_down']:
                if 'current_gaze_state' in self.step_data and self.step_data['current_gaze_state']:
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
                        elif self.step_data['current_gaze_state'] == target_direction:
                            # Continuing the same gaze - check duration
                            if self.step_data['hold_start_time']:
                                hold_duration = time.time() - self.step_data['hold_start_time']
                                
                                # Check if hold duration is met
                                if hold_duration >= required_duration:
                                    # Register this hold completion
                                    detection['hold_duration'] = hold_duration
                                    self.step_data['detections'].append(detection)
                                    
                                    # Reset tracking to prevent multiple registrations
                                    self.step_data['current_gaze_state'] = None
                                    self.step_data['hold_start_time'] = None
                                    
                                    print(f"✅ LONG {target_direction} hold completed ({hold_duration:.1f}s)")
                    else:
                        # Looking in wrong direction - reset tracking
                        if self.step_data['current_gaze_state'] == target_direction:
                            self.step_data['current_gaze_state'] = None
                            self.step_data['hold_start_time'] = None
            else:
                # No direction in this frame, but we might be tracking a hold
                if ('current_gaze_state' in self.step_data and 
                    self.step_data['current_gaze_state'] and
                    'hold_start_time' in self.step_data and 
                    self.step_data['hold_start_time']):
                    
                    # Continue tracking the hold even without direction
                    hold_duration = time.time() - self.step_data['hold_start_time']
                    
                    # Check if hold duration is met
                    step = self.test_steps[self.current_step]
                    required_duration = step.get('hold_duration', 5)
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
                        
                        print(f"✅ LONG {self.step_data['current_gaze_state']} hold completed ({hold_duration:.1f}s)")
        
        # Check if step is complete and auto-advance
        if self.check_step_completion():
            print(f"🎯 Step {self.current_step + 1} target reached! Auto-advancing...")
            self.complete_current_step()
            return True
        return False
        
    def complete_current_step(self):
        """Complete the current test step"""
        if not self.step_data:
            return
        
        step = self.test_steps[self.current_step]
        duration = time.time() - self.step_data['start_time']
        
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
        print(f"{status} {step['name']} - Duration: {duration:.1f}s")
        
        # Move to next step
        self.next_step()
        
    def analyze_step_results(self, step, step_data):
        """Analyze step results to determine success"""
        detections = step_data['detections']
        if not detections:
            return False
        
        step_type = step['type']
        
        if step_type == 'long_up':
            up_holds = [d for d in detections if d['direction'] == 'UP' and d.get('hold_duration', 0) > 0]
            return len(up_holds) >= step.get('repetitions', 3)
        
        elif step_type == 'long_down':
            down_holds = [d for d in detections if d['direction'] == 'DOWN' and d.get('hold_duration', 0) > 0]
            return len(down_holds) >= step.get('repetitions', 3)
        
        elif step_type == 'neutral_hold':
            false_detections = [d for d in detections if d['direction'] in ['UP', 'DOWN']]
            return len(false_detections) < 3
        
        return False
        
    def next_step(self):
        """Move to the next step"""
        self.current_step += 1
        if self.current_step < len(self.test_steps):
            print(f"\n🔄 Moving to Step {self.current_step + 1}: {self.test_steps[self.current_step]['name']}")
            self.start_step()
        else:
            print("\n🎉 All steps completed!")
            self.complete_test()
            
    def start_step(self):
        """Start the current step"""
        step = self.test_steps[self.current_step]
        print(f"\n📋 Starting: {step['name']}")
        
        # Initialize step data
        self.step_data = {
            'detections': [],
            'start_time': time.time(),
            'current_gaze_state': None,
            'hold_start_time': None
        }
        
    def complete_test(self):
        """Complete the entire test"""
        print("\n📊 Test Results Summary:")
        print("=" * 50)
        for i, result in enumerate(self.test_results):
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            print(f"Step {i+1}: {result['name']} - {status} ({result['duration']:.1f}s)")
            
    def test_auto_advance(self):
        """Test the auto-advance functionality"""
        print("🧪 Testing Auto-Advance Functionality")
        print("=" * 50)
        
        # Start first step
        self.start_step()
        
        # Test Step 1: Long UP Holds
        print("\n--- Testing Step 1: Long UP Holds ---")
        for hold_num in range(3):
            print(f"\nHold {hold_num + 1}/3:")
            
            # Simulate 5 seconds of UP gaze
            start_time = time.time()
            while time.time() - start_time < 5.5:  # 5.5 seconds to ensure completion
                self.process_step_gaze(self.simulate_gaze_result('UP', is_continuous=True, gaze_detected=False))
                time.sleep(0.1)
                
            # Brief neutral break between holds
            if hold_num < 2:  # Don't add neutral after last hold
                for _ in range(5):  # 0.5 seconds of neutral
                    self.process_step_gaze(self.simulate_gaze_result(None, is_continuous=False, gaze_detected=False))
                    time.sleep(0.1)
                    
        # Test Step 2: Long DOWN Holds
        print("\n--- Testing Step 2: Long DOWN Holds ---")
        for hold_num in range(3):
            print(f"\nHold {hold_num + 1}/3:")
            
            # Simulate 5 seconds of DOWN gaze
            start_time = time.time()
            while time.time() - start_time < 5.5:  # 5.5 seconds to ensure completion
                self.process_step_gaze(self.simulate_gaze_result('DOWN', is_continuous=True, gaze_detected=False))
                time.sleep(0.1)
                
            # Brief neutral break between holds
            if hold_num < 2:  # Don't add neutral after last hold
                for _ in range(5):  # 0.5 seconds of neutral
                    self.process_step_gaze(self.simulate_gaze_result(None, is_continuous=False, gaze_detected=False))
                    time.sleep(0.1)
                    
        # Test Step 3: Neutral Hold
        print("\n--- Testing Step 3: Neutral Hold ---")
        start_time = time.time()
        while time.time() - start_time < 5.5:  # 5.5 seconds to ensure completion
            self.process_step_gaze(self.simulate_gaze_result(None, is_continuous=False, gaze_detected=False))
            time.sleep(0.1)

def main():
    """Run the auto-advance test"""
    print("🎭 Auto-Advance Test Simulator")
    print("This will test the auto-advance functionality")
    print()
    
    tester = AutoAdvanceTester()
    tester.test_auto_advance()

if __name__ == "__main__":
    main()
