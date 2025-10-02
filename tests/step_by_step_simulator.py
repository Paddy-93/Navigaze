#!/usr/bin/env python3
"""
Step-by-Step Simulator
Tests each component of the comprehensive gaze tester individually
"""

import tkinter as tk
import time
import threading
from comprehensive_gaze_tester_refactored import ComprehensiveGazeTester
from simulated_gaze_detector import SimulatedGazeDetector

class StepByStepSimulator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Step-by-Step Gaze Tester Simulator")
        self.root.geometry("400x300")
        
        # Create control panel
        self.create_control_panel()
        
        # Initialize gaze detector and tester
        self.gaze_detector = SimulatedGazeDetector()
        self.tester = None
        
        # Test state
        self.current_test = None
        self.test_results = []
        
    def create_control_panel(self):
        """Create the control panel for running tests"""
        # Title
        title_label = tk.Label(self.root, text="Step-by-Step Simulator", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Test buttons
        self.test1_btn = tk.Button(self.root, text="Test 1: Open GUI & Click Start", 
                                  command=self.test_gui_start, width=30)
        self.test1_btn.pack(pady=5)
        
        self.test2_btn = tk.Button(self.root, text="Test 2: Calibration Step", 
                                  command=self.test_calibration, width=30)
        self.test2_btn.pack(pady=5)
        
        self.test3_btn = tk.Button(self.root, text="Test 3: Long UP Hold", 
                                  command=self.test_long_up, width=30)
        self.test3_btn.pack(pady=5)
        
        self.test4_btn = tk.Button(self.root, text="Test 4: Long DOWN Hold", 
                                  command=self.test_long_down, width=30)
        self.test4_btn.pack(pady=5)
        
        self.test5_btn = tk.Button(self.root, text="Test 5: Sequence Pattern", 
                                  command=self.test_sequence, width=30)
        self.test5_btn.pack(pady=5)
        
        # Results display
        self.results_text = tk.Text(self.root, height=10, width=50)
        self.results_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Clear button
        clear_btn = tk.Button(self.root, text="Clear Results", 
                             command=self.clear_results)
        clear_btn.pack(pady=5)
        
    def log_result(self, message):
        """Log a result message"""
        timestamp = time.strftime("%H:%M:%S")
        self.results_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.results_text.see(tk.END)
        self.root.update()
        print(f"[{timestamp}] {message}")
        
    def clear_results(self):
        """Clear the results display"""
        self.results_text.delete(1.0, tk.END)
        
    def test_gui_start(self):
        """Test 1: Open GUI and click start button"""
        self.log_result("🧪 Starting Test 1: GUI Start Button")
        
        try:
            # Create the comprehensive gaze tester
            self.tester = ComprehensiveGazeTester(self.root, self.gaze_detector)
            self.log_result("✅ GUI created successfully")
            
            # Wait a moment for GUI to be ready
            self.root.after(1000, self._click_start_button)
            
        except Exception as e:
            self.log_result(f"❌ Test 1 failed: {e}")
            
    def _click_start_button(self):
        """Click the start button after a delay"""
        try:
            if self.tester and hasattr(self.tester, 'start_test'):
                self.log_result("🖱️ Clicking Start Test button...")
                self.tester.start_test()
                self.log_result("✅ Start button clicked successfully")
                self.log_result("✅ Test 1 PASSED: GUI opens and start button works")
            else:
                self.log_result("❌ Test 1 FAILED: No start button found")
        except Exception as e:
            self.log_result(f"❌ Test 1 FAILED: {e}")
            
    def test_calibration(self):
        """Test 2: Calibration step"""
        self.log_result("🧪 Starting Test 2: Calibration Step")
        
        try:
            if not self.tester:
                self.log_result("❌ Test 2 FAILED: No tester instance. Run Test 1 first.")
                return
                
            # Test calibration
            self.log_result("🔧 Testing calibration...")
            calibration_success = self.gaze_detector.calibrate({})
            
            if calibration_success:
                self.log_result("✅ Calibration completed successfully")
                self.log_result("✅ Test 2 PASSED: Calibration works")
            else:
                self.log_result("❌ Test 2 FAILED: Calibration failed")
                
        except Exception as e:
            self.log_result(f"❌ Test 2 FAILED: {e}")
            
    def test_long_up(self):
        """Test 3: Long UP hold simulation"""
        self.log_result("🧪 Starting Test 3: Long UP Hold")
        
        try:
            if not self.tester:
                self.log_result("❌ Test 3 FAILED: No tester instance. Run Test 1 first.")
                return
                
            # Simulate long UP hold
            self.log_result("👁️ Simulating long UP hold...")
            self.gaze_detector.start_step_simulation('long_up', {
                'repetitions': 1,
                'hold_duration': 5
            })
            
            # Monitor the simulation
            self._monitor_simulation("UP", 5)
            
        except Exception as e:
            self.log_result(f"❌ Test 3 FAILED: {e}")
            
    def test_long_down(self):
        """Test 4: Long DOWN hold simulation"""
        self.log_result("🧪 Starting Test 4: Long DOWN Hold")
        
        try:
            if not self.tester:
                self.log_result("❌ Test 4 FAILED: No tester instance. Run Test 1 first.")
                return
                
            # Simulate long DOWN hold
            self.log_result("👁️ Simulating long DOWN hold...")
            self.gaze_detector.start_step_simulation('long_down', {
                'repetitions': 1,
                'hold_duration': 5
            })
            
            # Monitor the simulation
            self._monitor_simulation("DOWN", 5)
            
        except Exception as e:
            self.log_result(f"❌ Test 4 FAILED: {e}")
            
    def test_sequence(self):
        """Test 5: Sequence pattern simulation"""
        self.log_result("🧪 Starting Test 5: Sequence Pattern")
        
        try:
            if not self.tester:
                self.log_result("❌ Test 5 FAILED: No tester instance. Run Test 1 first.")
                return
                
            # Simulate sequence pattern
            self.log_result("👁️ Simulating UP-DOWN-UP-DOWN sequence...")
            self.gaze_detector.start_step_simulation('sequence_up_down', {
                'pattern': ['UP', 'DOWN', 'UP', 'DOWN'],
                'repetitions': 1
            })
            
            # Monitor the simulation
            self._monitor_simulation("SEQUENCE", 3)
            
        except Exception as e:
            self.log_result(f"❌ Test 5 FAILED: {e}")
            
    def _monitor_simulation(self, test_type, duration):
        """Monitor a simulation for the given duration"""
        start_time = time.time()
        
        def check_simulation():
            elapsed = time.time() - start_time
            if elapsed < duration:
                # Check if gaze detector is providing input
                gaze_result = self.gaze_detector.update()
                if gaze_result and gaze_result.get('direction'):
                    self.log_result(f"👁️ Detected {gaze_result['direction']} gaze")
                self.root.after(100, check_simulation)
            else:
                self.log_result(f"✅ Test completed: {test_type} simulation finished")
                
        check_simulation()
        
    def run(self):
        """Run the simulator"""
        self.log_result("🚀 Step-by-Step Simulator started")
        self.log_result("📋 Available tests:")
        self.log_result("   1. Test GUI & Start Button")
        self.log_result("   2. Test Calibration")
        self.log_result("   3. Test Long UP Hold")
        self.log_result("   4. Test Long DOWN Hold")
        self.log_result("   5. Test Sequence Pattern")
        self.log_result("")
        self.log_result("Click a test button to run that specific test")
        
        self.root.mainloop()

def main():
    simulator = StepByStepSimulator()
    simulator.run()

if __name__ == "__main__":
    main()
