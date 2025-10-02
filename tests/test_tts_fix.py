#!/usr/bin/env python3
"""
Test script to verify TTS and beep timing fixes
"""

import tkinter as tk
from comprehensive_gaze_tester_refactored import ComprehensiveGazeTester
from simulated_gaze_detector import SimulatedGazeDetector

def test_tts_and_beep():
    """Test TTS and beep functionality"""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    # Create simulated gaze detector
    gaze_detector = SimulatedGazeDetector()
    gaze_detector.initialize()
    
    # Create tester
    tester = ComprehensiveGazeTester(root, gaze_detector)
    
    # Test TTS directly
    print("🔊 Testing TTS directly...")
    tester.test_tts()
    
    # Test speak with callback
    print("🔊 Testing speak with callback...")
    def test_callback():
        print("✅ Callback executed!")
        tester.play_beep_async()
    
    tester.speak("Testing TTS with callback", test_callback)
    
    # Test dual-flag system
    print("🔊 Testing dual-flag system...")
    tester.step_ready_callback = lambda: print("✅ Step ready callback executed!")
    tester.tts_complete = True
    tester.recording_complete = True
    tester.check_step_ready()
    
    # Keep the window alive for a bit to see results
    root.after(5000, root.quit)
    root.mainloop()
    
    # Cleanup
    gaze_detector.release()

if __name__ == "__main__":
    test_tts_and_beep()
