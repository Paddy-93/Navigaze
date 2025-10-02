#!/usr/bin/env python3
"""
Gaze Reporter - Real Version
Uses actual camera and gaze detection for comprehensive gaze testing
"""

import tkinter as tk
from comprehensive_gaze_tester_refactored import ComprehensiveGazeTester
from real_gaze_detector import RealGazeDetector

def main():
    """Main function for real gaze testing"""
    print("🎯 Gaze Reporter - Real Version")
    print("This version uses actual camera and gaze detection")
    print()
    
    # Create the main window
    root = tk.Tk()
    
    # Create real gaze detector
    gaze_detector = RealGazeDetector()
    
    # Initialize the gaze detector
    if not gaze_detector.initialize():
        print("❌ Failed to initialize gaze detector")
        return
    
    # Create the comprehensive gaze tester with real detector
    tester = ComprehensiveGazeTester(root, gaze_detector)
    
    # Set calibration duration to 5 seconds for real use
    tester.calibration_duration = 5.0
    
    try:
        # Run the GUI
        root.mainloop()
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
    finally:
        # Cleanup
        if hasattr(tester, 'gaze_detector'):
            tester.gaze_detector.release()

if __name__ == "__main__":
    main()
