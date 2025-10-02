#!/usr/bin/env python3
"""
Run the comprehensive gaze test V2 with real gaze detector
"""

import tkinter as tk
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'gaze_reporting'))
from comprehensive_gaze_tester_v2 import ComprehensiveGazeTesterV2
from real_gaze_detector import RealGazeDetector

def main():
    # Create main window
    root = tk.Tk()
    
    # Initialize real gaze detector
    gaze_detector = RealGazeDetector()
    success = gaze_detector.initialize()
    
    if not success:
        print("❌ Failed to initialize gaze detector")
        return
    
    # Create tester
    tester = ComprehensiveGazeTesterV2(root, gaze_detector)
    
    # Run
    try:
        root.mainloop()
    finally:
        gaze_detector.release()

if __name__ == "__main__":
    main()

