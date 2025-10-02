#!/usr/bin/env python3
"""
Test the comprehensive gaze tester with simulation capabilities
This adds simulation mode to the actual tester
"""

import time
import threading
import sys
import os
import numpy as np

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the comprehensive gaze tester
from comprehensive_gaze_tester import ComprehensiveGazeTester
import tkinter as tk

class SimulatedComprehensiveGazeTester(ComprehensiveGazeTester):
    """Extended version of ComprehensiveGazeTester with simulation capabilities"""
    
    def __init__(self, master):
        super().__init__(master)
        self.simulation_mode = False
        self.simulation_thread = None
        self.simulation_running = False
        
    def enable_simulation_mode(self):
        """Enable simulation mode"""
        self.simulation_mode = True
        print("🎭 Simulation mode enabled")
        
    def start_simulation(self):
        """Start the simulation"""
        if self.simulation_mode:
            self.simulation_running = True
            self.simulation_thread = threading.Thread(target=self.run_simulation_sequence, daemon=True)
            self.simulation_thread.start()
            
    def run_simulation_sequence(self):
        """Run the simulation sequence"""
        print("🎭 Starting Simulation Sequence")
        print("=" * 40)
        
        # Wait for test to initialize
        time.sleep(3)
        
        try:
            # Test Step 1: Long UP Holds
            print("\n--- Simulating Step 1: Long UP Holds ---")
            self.simulate_long_holds('UP', 3, 5)
            
            # Wait for auto-advance
            print("\n⏳ Waiting for auto-advance...")
            time.sleep(3)
            
            # Test Step 2: Long DOWN Holds
            print("\n--- Simulating Step 2: Long DOWN Holds ---")
            self.simulate_long_holds('DOWN', 3, 5)
            
            # Wait for auto-advance
            print("\n⏳ Waiting for auto-advance...")
            time.sleep(3)
            
            # Test Step 3: Neutral Hold
            print("\n--- Simulating Step 3: Neutral Hold ---")
            self.simulate_neutral_hold(5)
            
            print("\n✅ Simulation completed!")
            
        except Exception as e:
            print(f"\n❌ Simulation error: {e}")
            import traceback
            traceback.print_exc()
            
    def simulate_long_holds(self, direction, count, duration):
        """Simulate long holds in a direction"""
        print(f"🎭 Simulating {count} long {direction} holds ({duration}s each)")
        
        for hold_num in range(count):
            print(f"\nHold {hold_num + 1}/{count}")
            
            # Simulate the hold by directly calling process_step_gaze
            start_time = time.time()
            while time.time() - start_time < duration + 0.5 and self.simulation_running:
                gaze_result = self.create_simulated_gaze(direction, is_continuous=True, gaze_detected=False)
                
                if hasattr(self, 'process_step_gaze'):
                    self.process_step_gaze(gaze_result)
                
                time.sleep(0.1)  # 100ms intervals
                
            # Brief neutral break between holds
            if hold_num < count - 1:
                print("  Neutral break...")
                for _ in range(5):  # 0.5 seconds of neutral
                    neutral_result = self.create_simulated_gaze(None, is_continuous=False, gaze_detected=False)
                    if hasattr(self, 'process_step_gaze'):
                        self.process_step_gaze(neutral_result)
                    time.sleep(0.1)
                    
    def simulate_neutral_hold(self, duration):
        """Simulate neutral hold"""
        print(f"🎭 Simulating neutral hold for {duration}s")
        
        start_time = time.time()
        while time.time() - start_time < duration + 0.5 and self.simulation_running:
            neutral_result = self.create_simulated_gaze(None, is_continuous=False, gaze_detected=False)
            if hasattr(self, 'process_step_gaze'):
                self.process_step_gaze(neutral_result)
            time.sleep(0.1)
            
    def create_simulated_gaze(self, direction, is_continuous=False, gaze_detected=True):
        """Create a simulated gaze result"""
        return {
            'direction': direction,
            'offset': 0.02 if direction == 'UP' else -0.02 if direction == 'DOWN' else 0,
            'is_continuous_gaze': is_continuous,
            'gaze_detected': gaze_detected,
            'pupil_relative': (0.5, 0.3 if direction == 'UP' else 0.7 if direction == 'DOWN' else 0.5),
            'confidence': 0.9
        }
        
    def start_test(self):
        """Override start_test to enable simulation"""
        super().start_test()
        
        # If in simulation mode, start simulation after a delay
        if self.simulation_mode:
            self.master.after(2000, self.start_simulation)  # Start simulation after 2 seconds

def main():
    """Main function to run the test with simulation"""
    print("🎭 Comprehensive Gaze Tester with Simulation")
    print("This will show the actual UI and simulate gaze inputs")
    print("The simulation will start automatically after the test begins")
    print()
    
    # Create the main window
    root = tk.Tk()
    
    # Create the simulated tester
    tester = SimulatedComprehensiveGazeTester(root)
    
    # Enable simulation mode
    tester.enable_simulation_mode()
    
    try:
        # Run the GUI
        root.mainloop()
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
    finally:
        tester.simulation_running = False

if __name__ == "__main__":
    main()
