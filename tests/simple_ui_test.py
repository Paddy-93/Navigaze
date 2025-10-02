#!/usr/bin/env python3
"""
Simple UI Test
Just opens the comprehensive gaze tester and keeps it open so you can see it
"""

import tkinter as tk
import time
from comprehensive_gaze_tester_refactored import ComprehensiveGazeTester
from simulated_gaze_detector import SimulatedGazeDetector

def main():
    print("🚀 Simple UI Test - Opening comprehensive gaze tester...")
    
    # Create root window
    root = tk.Tk()
    
    # Initialize gaze detector and tester
    gaze_detector = SimulatedGazeDetector()
    tester = ComprehensiveGazeTester(root, gaze_detector)
    
    print("✅ Comprehensive gaze tester opened")
    print("📱 You should see the window with 'Click Start Test to begin...'")
    print("⏳ Window will stay open for 10 seconds...")
    
    # Wait 10 seconds so you can see the window
    time.sleep(10)
    
    print("🖱️ Now clicking Start Test...")
    tester.start_test()
    
    print("📱 You should now see the calibration display with red background")
    print("⏳ Window will stay open for another 10 seconds...")
    
    # Wait another 10 seconds so you can see the calibration display
    time.sleep(10)
    
    print("✅ Test complete - closing window")
    root.destroy()

if __name__ == "__main__":
    main()