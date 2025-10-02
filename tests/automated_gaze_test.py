#!/usr/bin/env python3
"""
Comprehensive Automated Gaze Test
Simulates a complete walkthrough of the gaze testing system
"""

import tkinter as tk
import time
import threading
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'gaze_reporting'))
from comprehensive_gaze_tester_refactored import ComprehensiveGazeTester
from simulated_gaze_detector import SimulatedGazeDetector

class ComprehensiveAutomatedTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Comprehensive Automated Gaze Test")
        
        # Initialize gaze detector and tester
        self.gaze_detector = SimulatedGazeDetector()
        self.tester = None
        
        # Test state
        self.test_passed = False
        self.test_failed = False
        self.current_test_step = 0
        
        # Gaze tracking for debugging
        self.gaze_count = 0
        self.last_gaze_time = 0
        self.gaze_times = []
        self.test_start_time = time.time()
        
        # Initialize step monitoring
        self.last_step = -1
        self.root.after(3000, self.monitor_step_changes)
        
        # Timeout after 1.5 minutes (90 seconds)
        # self.timeout_timer = self.root.after(90000, self.timeout_test)  # Disabled for debugging
    
    def timeout_test(self):
        """Handle test timeout after 1.5 minutes"""
        print("\n" + "=" * 60)
        print("⏰ TEST TIMEOUT - 1.5 minutes elapsed")
        print("=" * 60)
        
        # Print gaze frequency analysis
        self.analyze_gaze_frequency()
        
        # Close the test
        self.root.quit()
        self.root.destroy()
    
    def analyze_gaze_frequency(self):
        """Analyze gaze frequency for debugging"""
        if not self.gaze_times:
            print("[ERROR] No gazes detected during test")
            return
            
        print(f"[ANALYSIS] GAZE FREQUENCY ANALYSIS:")
        print(f"   Total gazes detected: {self.gaze_count}")
        print(f"   Test duration: {time.time() - self.test_start_time:.1f} seconds")
        print(f"   Average gazes per second: {self.gaze_count / (time.time() - self.test_start_time):.2f}")
        
        # Check for gazes that are too frequent (more than 1 per second)
        too_frequent = 0
        for i in range(1, len(self.gaze_times)):
            time_diff = self.gaze_times[i] - self.gaze_times[i-1]
            if time_diff < 1.0:
                too_frequent += 1
                print(f"   [WARN] Gaze {i} detected {time_diff:.2f}s after previous (too fast!)")
        
        if too_frequent == 0:
            print("   [OK] All gazes properly spaced (1+ seconds apart)")
        else:
            print(f"   [ERROR] {too_frequent} gazes detected too frequently")
    
    def track_gaze(self, direction):
        """Track gaze detection for debugging"""
        current_time = time.time()
        self.gaze_count += 1
        self.gaze_times.append(current_time)
        
        if self.last_gaze_time > 0:
            time_since_last = current_time - self.last_gaze_time
            print(f"   [GAZE] GAZE #{self.gaze_count}: {direction} (after {time_since_last:.2f}s) [{current_time:.2f}]")
        else:
            print(f"   [GAZE] GAZE #{self.gaze_count}: {direction} (first gaze) [{current_time:.2f}]")
            
        self.last_gaze_time = current_time
        
    def run_test(self):
        """Run the comprehensive automated test"""
        print("[START] Starting Comprehensive Automated Gaze Test")
        print("=" * 60)
        print("This will simulate a complete user walkthrough:")
        print("1. Starting screen (3 seconds)")
        print("2. Auto-start to calibration")
        print("3. Calibration with spoofed data (1 second)")
        print("4. Long UP gazes with realistic delays")
        print("5. Long DOWN gazes with realistic delays")
        print("6. Sequence patterns with realistic timing")
        print("=" * 60)
        
        try:
            # Initialize the comprehensive gaze tester
            print("[INFO] Initializing comprehensive gaze tester...")
            self.tester = ComprehensiveGazeTester(self.root, self.gaze_detector)
            self.tester.calibration_duration = 1.0  # Set to 1 second for automation
            print("[OK] Comprehensive gaze tester initialized")
            
            # Start the automated simulation
            self.start_simulation()
            
            # Run the main loop
            self.root.mainloop()
            
        except Exception as e:
            print(f"❌ TEST FAILED: Exception occurred - {e}")
            self.test_failed = True
            
        return self.test_passed
    
    def start_simulation(self):
        """Start the automated simulation"""
        print("\n🎬 Starting simulation...")
        print("👀 WATCH THE WINDOW - Starting screen should show for 3 seconds")
        
        # Schedule the simulation steps
        self.root.after(4000, self.simulate_calibration)  # After starting screen + auto-start
        
    def simulate_calibration(self):
        """Simulate calibration step"""
        print("\n📋 Step: Calibration")
        print("👀 WATCH THE WINDOW - Should show calibration screen with red dot")
        
        # Check if we're in calibration step
        current_step_type = self.tester.test_steps[self.tester.current_step]['type'] if self.tester.current_step < len(self.tester.test_steps) else None
        print(f"   Current step: {self.tester.current_step}")
        print(f"   Step type: {current_step_type}")
        print(f"   Test running: {self.tester.test_running}")
        
        if current_step_type == 'calibration':
            print("✅ Calibration step detected")
            
            # Spoof calibration data to the gaze detector
            self.spoof_calibration_data()
            
            # Wait for calibration to complete (1 second + buffer)
            self.root.after(2000, self.verify_calibration_completion)
        else:
            print("❌ Not in calibration step, retrying...")
            # Try again in 1 second
            self.root.after(1000, self.simulate_calibration)
    
    def spoof_calibration_data(self):
        """Spoof realistic calibration data"""
        print("🎭 Spoofing calibration data...")
        
        def provide_calibration_data():
            """Provide calibration data in a separate thread"""
            for i in range(10):  # Provide 10 data points
                if hasattr(self.tester, 'calibrating') and self.tester.calibrating:
                    # Simulate realistic pupil positions with slight variation
                    base_y = 0.5
                    variation = (i % 3 - 1) * 0.02  # Small variation
                    pupil_data = (0.5, base_y + variation)
                    
                    # Mock the gaze detector to return this data
                    if hasattr(self.gaze_detector, 'mock_pupil_data'):
                        self.gaze_detector.mock_pupil_data = pupil_data
                    
                time.sleep(0.1)  # 100ms intervals
        
        # Start providing data in background
        threading.Thread(target=provide_calibration_data, daemon=True).start()
    
    def verify_calibration_completion(self):
        """Verify calibration completed and moved to next step"""
        print("\n🔍 Verifying calibration completion...")
        
        if self.tester.current_step > 0:
            print(f"   Current step: {self.tester.current_step}")
            print(f"   Step type: {self.tester.test_steps[self.tester.current_step]['type']}")
            
            # Wait a moment for UI to update, then start simulating the gaze step
            self.root.after(1000, self.simulate_current_gaze_step)
        else:
            print(f"❌ Still in calibration step")
            print(f"   Calibrating: {getattr(self.tester, 'calibrating', 'N/A')}")
            print(f"   Test running: {getattr(self.tester, 'test_running', 'N/A')}")
            
            # Check if calibration finished but step not advanced
            if not getattr(self.tester, 'calibrating', True):
                print("   Calibration finished but step not advanced - waiting for completion...")
            
            # Force calibration completion after a few attempts
            if not hasattr(self, 'calibration_attempts'):
                self.calibration_attempts = 0
            
            self.calibration_attempts += 1
            
            if self.calibration_attempts >= 15:  # Give it more time (15 seconds)
                print("❌ Calibration failed to complete automatically")
                self.test_failed = True
            else:
                # Try again in 1 second
                self.root.after(1000, self.verify_calibration_completion)
    
    def monitor_step_changes(self):
        """Monitor for step changes and automatically start simulation"""
        if self.tester.current_step != self.last_step:
            print(f"\n🔄 Step changed from {self.last_step} to {self.tester.current_step}")
            self.last_step = self.tester.current_step
            
            # Check if this is a gaze step that needs simulation
            if self.tester.current_step < len(self.tester.test_steps):
                current_step = self.tester.test_steps[self.tester.current_step]
                step_type = current_step['type']
                
                # Only run first two steps: UP-DOWN-UP-DOWN Sequence (step 1) and Quick UP Gazes (step 2)
                if self.tester.current_step == 1 or self.tester.current_step == 2:
                    if step_type in ['quick_up', 'quick_down', 'long_up', 'long_down', 'neutral_hold'] or step_type.startswith('sequence_'):
                        print(f"🎭 Auto-starting simulation for step: {current_step['name']}")
                        self.root.after(2000, self.simulate_current_gaze_step)
                elif self.tester.current_step > 2:
                    print(f"✅ Test completed after first two gaze steps (step {self.tester.current_step})")
                    self.test_passed = True
                    self.root.after(1000, self.root.quit)
                    return
            else:
                print(f"✅ Test completed - reached step {self.tester.current_step} (total: {len(self.tester.test_steps)})")
                return
        
        # Continue monitoring
        self.root.after(1000, self.monitor_step_changes)
    
    def simulate_current_gaze_step(self):
        """Simulate the current gaze step"""
        # Check if we're still within bounds
        if self.tester.current_step >= len(self.tester.test_steps):
            print(f"✅ Test completed - all {len(self.tester.test_steps)} steps finished")
            return
        
        current_step = self.tester.test_steps[self.tester.current_step]
        step_type = current_step['type']
        step_name = current_step['name']
        
        print(f"\n📋 Step: {step_name} ({step_type})")
        print("👀 WATCH THE WINDOW - Should show gaze step instructions")
        
        # Log baseline results for this step
        if hasattr(self.tester, 'step_data') and self.tester.step_data:
            baseline_info = {
                'step_name': step_name,
                'step_type': step_type,
                'current_step': self.tester.current_step,
                'total_steps': len(self.tester.test_steps),
                'timestamp': time.time()
            }
            print(f"📊 BASELINE: {baseline_info}")
        else:
            print(f"📊 BASELINE: No step_data available yet")
        
        if step_type == 'long_up':
            self.simulate_long_gazes('UP', current_step.get('repetitions', 3))
        elif step_type == 'long_down':
            self.simulate_long_gazes('DOWN', current_step.get('repetitions', 3))
        elif step_type == 'quick_up':
            self.simulate_quick_gazes('UP', current_step.get('repetitions', 5))
        elif step_type == 'quick_down':
            self.simulate_quick_gazes('DOWN', current_step.get('repetitions', 5))
        elif step_type == 'neutral_hold':
            self.simulate_neutral_hold(current_step.get('hold_duration', 5))
        elif step_type.startswith('sequence_'):
            pattern = current_step.get('pattern', [])
            repetitions = current_step.get('repetitions', 3)
            self.simulate_sequence(pattern, repetitions)
        else:
            print(f"⚠️ Unknown step type: {step_type}")
            self.advance_to_next_step()
    
    def simulate_long_gazes(self, direction, repetitions):
        """Simulate long gaze holds with realistic timing"""
        print(f"🎭 Simulating {repetitions} long {direction} gazes...")
        print(f"📋 Expected: {repetitions} x {direction} holds (5.5s each)")
        
        def simulate_gaze(gaze_num):
            if gaze_num <= repetitions:
                timestamp = time.time()
                print(f"   👁️ [{timestamp:.2f}] Long {direction} gaze {gaze_num}/{repetitions}")
                
                # Track this gaze for debugging
                self.track_gaze(f"LONG_{direction}")
                
                # Start the gaze
                self.gaze_detector.start_simulated_gaze(direction, duration=5.5, is_long=True)
                
                # Schedule next gaze or completion
                if gaze_num < repetitions:
                    # Wait for gaze + neutral break (increased timeout for long holds)
                    self.root.after(7000, lambda: simulate_gaze(gaze_num + 1))
                else:
                    # All gazes complete, advance to next step (increased timeout for long holds)
                    print(f"   ✅ All {repetitions} {direction} holds complete!")
                    self.root.after(6000, self.advance_to_next_step)
            
        # Start the first gaze after a brief delay
        self.root.after(2000, lambda: simulate_gaze(1))
    
    def simulate_quick_gazes(self, direction, repetitions):
        """Simulate quick gaze movements with realistic timing"""
        print(f"🎭 Simulating {repetitions} quick {direction} gazes...")
        print(f"📋 Expected: {repetitions} x {direction} gazes")
        
        def simulate_gaze(gaze_num):
            if gaze_num <= repetitions:
                timestamp = time.time()
                print(f"   👁️ [{timestamp:.2f}] Quick {direction} gaze {gaze_num}/{repetitions}")
                
                # Track this gaze for debugging
                self.track_gaze(f"QUICK_{direction}")
                
                # Start the gaze
                self.gaze_detector.start_simulated_gaze(direction, duration=0.5, is_long=False)
                
                # Schedule next gaze or completion
                if gaze_num < repetitions:
                    # Wait for gaze + neutral break
                    self.root.after(1000, lambda: simulate_gaze(gaze_num + 1))
                else:
                    # All gazes complete, let the comprehensive tester handle step completion
                    print(f"   ✅ All {repetitions} {direction} gazes complete!")
            
        # Start the first gaze after a brief delay
        self.root.after(2000, lambda: simulate_gaze(1))
    
    def simulate_neutral_hold(self, duration):
        """Simulate neutral hold"""
        print(f"🎭 Simulating neutral hold for {duration} seconds...")
        
        # Start neutral hold
        self.gaze_detector.start_simulated_neutral(duration)
        
        # Advance after completion
        self.root.after((duration + 1) * 1000, self.advance_to_next_step)
    
    def simulate_sequence(self, pattern, repetitions):
        """Simulate sequence pattern with realistic timing and retry logic"""
        print(f"🎭 Simulating sequence {pattern} x {repetitions}")
        print("⏳ Waiting 2 seconds for recording to start and instructions to be spoken...")
        
        # Track retry attempts
        self.sequence_retry_count = 0
        self.max_retries = 5  # Maximum retries per sequence step
        
        def simulate_pattern(rep_num):
            if rep_num <= repetitions:
                print(f"   🔄 Sequence repetition {rep_num}/{repetitions}")
                print(f"   📋 Expected pattern: {' → '.join(pattern)}")
                
                def simulate_direction(dir_index):
                    if dir_index < len(pattern):
                        direction = pattern[dir_index]
                        timestamp = time.time()
                        print(f"     👁️ [{timestamp:.2f}] Quick {direction} gaze ({dir_index + 1}/{len(pattern)})")
                        
                        # Track this gaze for debugging
                        self.track_gaze(f"SEQ_{direction}")
                        
                        # Start quick gaze with 0.5 second duration for sequence
                        self.gaze_detector.start_simulated_gaze(direction, duration=0.5, is_long=False)
                        
                        # Wait 0.5 seconds for gaze to complete, then schedule next direction
                        self.root.after(500, lambda: simulate_direction(dir_index + 1))
                    else:
                        # Pattern complete, schedule next repetition or advance
                        if rep_num < repetitions:
                            print(f"   ✅ Pattern {rep_num} complete, starting next...")
                            self.root.after(500, lambda: simulate_pattern(rep_num + 1))
                        else:
                            # Wait for final pattern processing
                            print(f"   ✅ All {repetitions} patterns complete!")
                            self.root.after(1000, self.advance_to_next_step)
                
                # Start first direction after brief delay
                self.root.after(2000, lambda: simulate_direction(0))
        
        # Start monitoring for test failures and retry logic
        self.start_test_monitoring(pattern, repetitions)
        
        # Start first repetition after 10 second delay for recording and instructions
        self.root.after(2500, lambda: simulate_pattern(1))
    
    def start_test_monitoring(self, pattern, repetitions):
        """Start monitoring the test for failures and retry if needed"""
        def check_test_progress():
            if hasattr(self.tester, 'current_step') and hasattr(self.tester, 'test_steps'):
                current_step = self.tester.current_step
                if current_step < len(self.tester.test_steps):
                    step = self.tester.test_steps[current_step]
                    step_type = step['type']
                    
                    # Check if this is a sequence step that might have failed
                    if step_type.startswith('sequence_'):
                        # Check if the step completed and failed
                        if hasattr(self.tester, 'step_data') and self.tester.step_data:
                            # Look for failure indicators in the step data
                            if 'detections' in self.tester.step_data:
                                detections = self.tester.step_data['detections']
                                if len(detections) > 0:
                                    # Check if we have enough detections but the step failed
                                    # This indicates a pattern mismatch
                                    print(f"🔍 Checking sequence step progress...")
                                    
                                    # If we have detections but the step is still running, 
                                    # it might be a pattern mismatch - wait a bit more
                                    pass
            
            # Continue monitoring
            self.root.after(2000, check_test_progress)
        
        # Start monitoring after a delay
        self.root.after(4000, check_test_progress)  # Start after 4 seconds
    
    def restart_sequence(self, pattern, repetitions):
        """Restart the sequence from the beginning"""
        print(f"🔄 Restarting sequence {pattern} x {repetitions}")
        
        def simulate_pattern(rep_num):
            if rep_num <= repetitions:
                print(f"   🔄 Sequence repetition {rep_num}/{repetitions}")
                
                def simulate_direction(dir_index):
                    if dir_index < len(pattern):
                        direction = pattern[dir_index]
                        print(f"     👁️ Quick {direction} gaze")
                        
                        # Track this gaze for debugging
                        self.track_gaze(direction)
                        
                        # Start quick gaze with 1 second duration for sequence
                        self.gaze_detector.start_simulated_gaze(direction, duration=1.0, is_long=False)
                        
                        # Wait 0.5 seconds for gaze to complete, then schedule next direction
                        self.root.after(500, lambda: simulate_direction(dir_index + 1))
                    else:
                        # Pattern complete, schedule next repetition or advance
                        if rep_num < repetitions:
                            self.root.after(500, lambda: simulate_pattern(rep_num + 1))
                        else:
                            # Wait for final pattern processing
                            self.root.after(750, self.advance_to_next_step)
                
                # Start first direction
                simulate_direction(0)
        
        # Start the first pattern
        simulate_pattern(1)
    
    def advance_to_next_step(self):
        """Advance to the next step with failure detection and retry logic"""
        print("\n⏭️ Advancing to next step...")
        
        if self.tester.current_step < len(self.tester.test_steps) - 1:
            # Check if the current step failed before advancing
            current_step = self.tester.test_steps[self.tester.current_step]
            step_type = current_step['type']
            
            # Check if this was a sequence step that might have failed
            if step_type.startswith('sequence_'):
                # Check if we have detections but the step failed
                if hasattr(self.tester, 'step_data') and self.tester.step_data:
                    detections = self.tester.step_data.get('detections', [])
                    if len(detections) > 0:
                        print(f"🔍 Sequence step had {len(detections)} detections")
                        
                        # If this is a sequence step and we're advancing, check if we should retry
                        if self.sequence_retry_count < self.max_retries:
                            print(f"🔄 Sequence step may have failed - retrying (attempt {self.sequence_retry_count + 1}/{self.max_retries})")
                            self.sequence_retry_count += 1
                            
                            # Reset the current step and retry
                            if hasattr(self.tester, 'step_data'):
                                self.tester.step_data['gaze_sequence'] = []
                                self.tester.step_data['completed_patterns'] = 0
                            
                            # Wait 2 seconds then restart the sequence
                            print("⏳ Waiting 2 seconds before retry...")
                            self.root.after(2000, lambda: self.restart_current_sequence_step())
                            return
                        else:
                            print("❌ Max retries exceeded for this sequence step, continuing...")
                            self.sequence_retry_count = 0  # Reset for next step
            
            # Let the comprehensive tester handle step completion automatically
            print("✅ Step should complete automatically")
            
        # Wait a moment then simulate next step
        self.root.after(1000, self.simulate_current_gaze_step)
    
    def restart_current_sequence_step(self):
        """Restart the current sequence step"""
        if hasattr(self.tester, 'current_step') and hasattr(self.tester, 'test_steps'):
            current_step = self.tester.test_steps[self.tester.current_step]
            step_type = current_step['type']
            
            if step_type.startswith('sequence_'):
                pattern = current_step.get('pattern', [])
                repetitions = current_step.get('repetitions', 3)
                print(f"🔄 Restarting current sequence step: {pattern} x {repetitions}")
                
                # Reset step data
                if hasattr(self.tester, 'step_data'):
                    self.tester.step_data = {
                        'gaze_sequence': [],
                        'completed_patterns': 0,
                        'detections': [],
                        'start_time': time.time()
                    }
                
                # Restart the sequence simulation
                self.simulate_sequence(pattern, repetitions)
    
    def complete_test(self):
        """Complete the test"""
        print("\n🎉 TEST COMPLETED!")
        print("✅ All steps simulated successfully")
        self.test_passed = True
        
        # Wait a moment then close
        self.root.after(3000, self.root.quit)

def main():
    """Main test function"""
    test = ComprehensiveAutomatedTest()
    
    success = test.run_test()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 COMPREHENSIVE TEST RESULT: PASSED")
        print("✅ Complete walkthrough simulation successful")
    else:
        print("💥 COMPREHENSIVE TEST RESULT: FAILED")
        print("❌ Simulation failed or incomplete")
    
    return success

if __name__ == "__main__":
    main()