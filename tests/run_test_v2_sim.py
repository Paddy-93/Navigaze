#!/usr/bin/env python3
"""
Run the comprehensive gaze test V2 with simulated gaze detector
"""

import tkinter as tk
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'gaze_reporting'))
from comprehensive_gaze_tester_v2 import ComprehensiveGazeTesterV2
from simulated_gaze_detector import SimulatedGazeDetector

def main():
    # Create main window
    root = tk.Tk()
    
    # Initialize simulated gaze detector
    gaze_detector = SimulatedGazeDetector()
    gaze_detector.initialize()
    
    # Create tester
    tester = ComprehensiveGazeTesterV2(root, gaze_detector)
    
    # Run
    try:
        root.mainloop()
    finally:
        gaze_detector.release()

if __name__ == "__main__":
    main()

