#!/usr/bin/env python3
"""
Comprehensive Gaze Tester - Simulation Version
Uses simulated gaze detection for testing
"""

import tkinter as tk
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'gaze_reporting'))
from comprehensive_gaze_tester_refactored import ComprehensiveGazeTester
from simulated_gaze_detector import SimulatedGazeDetector

def main():
    """Main function for simulated gaze testing"""
    print("🎭 Comprehensive Gaze Tester - Simulation Version")
    print("This version uses simulated gaze detection for testing")
    print()
    
    # Create the main window
    root = tk.Tk()
    
    # Create simulated gaze detector
    gaze_detector = SimulatedGazeDetector()
    
    # Create the comprehensive gaze tester with simulated detector
    tester = ComprehensiveGazeTester(root, gaze_detector)
    
    # Start simulation after a delay
    def start_simulation():
        print("🎭 Starting simulation...")
        gaze_detector.start_test_simulation(tester.test_steps, tester)
    
    root.after(3000, start_simulation)  # Start simulation after 3 seconds
    
    try:
        # Run the GUI
        root.mainloop()
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
    finally:
        # Cleanup
        if hasattr(tester, 'gaze_detector'):
            tester.gaze_detector.cleanup()

if __name__ == "__main__":
    main()
