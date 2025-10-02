#!/usr/bin/env python3
"""
Click Start Button Test
Actually clicks the start button on the UI instead of calling the function
"""

import tkinter as tk
import time
from comprehensive_gaze_tester_refactored import ComprehensiveGazeTester
from simulated_gaze_detector import SimulatedGazeDetector

def main():
    print("🚀 Click Start Button Test")
    print("=" * 50)
    
    # Create root window
    root = tk.Tk()
    
    # Initialize gaze detector and tester
    gaze_detector = SimulatedGazeDetector()
    tester = ComprehensiveGazeTester(root, gaze_detector)
    
    print("✅ Comprehensive gaze tester opened")
    print("📱 You should see the window with 'Click Start Test to begin...'")
    print("⏳ Waiting 3 seconds before clicking start button...")
    
    # Wait 3 seconds so you can see the initial state
    time.sleep(3)
    
    print("🖱️ Now actually clicking the Start Test button...")
    
    # Actually click the start button
    try:
        tester.start_button.invoke()  # This simulates clicking the button
        print("✅ Start button clicked successfully")
    except Exception as e:
        print(f"❌ Failed to click start button: {e}")
        return
    
    print("📱 You should now see the calibration display with red background")
    print("⏳ Waiting 10 seconds to see the calibration display...")
    
    # Wait 10 seconds so you can see the calibration display
    for i in range(10):
        time.sleep(1)
        # Check what's displayed
        current_text = tester.instruction_display.cget("text")
        current_bg = tester.instruction_display.cget("bg")
        print(f"   [{i+1}s] Text: {current_text[:50]}... | BG: {current_bg}")
        
        # Check if calibration display is showing
        if "CALIBRATION" in current_text and current_bg.lower() == "red":
            print("✅ CALIBRATION DISPLAY FOUND!")
            break
    
    print("✅ Test complete - closing window")
    root.destroy()

if __name__ == "__main__":
    main()
