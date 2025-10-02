#!/usr/bin/env python3
"""
Direct Patch Test for Comprehensive Gaze Tester
This patches the actual tester to use simulated inputs and shows the test in action
"""

import time
import threading
import sys
import os
import numpy as np
from unittest.mock import patch, MagicMock

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_mock_objects():
    """Create mock objects for camera and mediapipe"""
    # Mock cv2
    mock_cv2 = MagicMock()
    mock_camera = MagicMock()
    mock_camera.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    mock_camera.isOpened.return_value = True
    mock_cv2.VideoCapture.return_value = mock_camera
    mock_cv2.VideoWriter.return_value = MagicMock()
    
    # Mock mediapipe
    mock_mp = MagicMock()
    mock_face_detection = MagicMock()
    mock_face_mesh = MagicMock()
    mock_face_detection.process.return_value = MagicMock()
    mock_face_mesh.process.return_value = MagicMock()
    mock_mp.solutions.face_detection = MagicMock(return_value=mock_face_detection)
    mock_mp.solutions.face_mesh = MagicMock(return_value=mock_face_mesh)
    
    return mock_cv2, mock_mp

def simulate_gaze_input(direction, is_continuous=False, gaze_detected=True):
    """Create a simulated gaze input"""
    return {
        'direction': direction,
        'offset': 0.02 if direction == 'UP' else -0.02 if direction == 'DOWN' else 0,
        'is_continuous_gaze': is_continuous,
        'gaze_detected': gaze_detected,
        'pupil_relative': (0.5, 0.3 if direction == 'UP' else 0.7 if direction == 'DOWN' else 0.5),
        'confidence': 0.9
    }

def run_simulation():
    """Run the simulation with the actual comprehensive gaze tester"""
    print("🎭 Comprehensive Gaze Tester Direct Patch Test")
    print("=" * 60)
    
    # Create mock objects
    mock_cv2, mock_mp = create_mock_objects()
    
    # Apply patches
    with patch('cv2', mock_cv2), \
         patch('mediapipe', mock_mp):
        
        # Import the comprehensive gaze tester
        from comprehensive_gaze_tester import ComprehensiveGazeTester
        import tkinter as tk
        
        # Create the main window
        root = tk.Tk()
        
        # Create the tester
        tester = ComprehensiveGazeTester(root)
        
        # Override the camera update method to use simulated inputs
        def simulated_camera_update():
            """Simulated camera update that generates fake gaze data"""
            # Create a fake frame
            fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Simulate face landmarks
            if hasattr(tester, 'face_landmarks'):
                # Mock the face landmarks processing
                mock_landmarks = type('MockLandmarks', (), {
                    'get_pupil_relative': lambda: (0.5, 0.3),  # UP gaze
                    'get_confidence': lambda: 0.9
                })()
                
                # Update gaze detector
                if hasattr(tester, 'gaze_detector'):
                    gaze_result = tester.gaze_detector.update(mock_landmarks)
                    
                    # Process the gaze result
                    if hasattr(tester, 'process_step_gaze'):
                        tester.process_step_gaze(gaze_result)
            
            # Schedule next update
            root.after(33, simulated_camera_update)  # ~30 FPS
            
        # Replace the update method
        tester.update_camera = simulated_camera_update
        
        # Start the test
        print("📋 Starting test...")
        tester.start_test()
        
        # Wait for test to initialize
        time.sleep(3)
        
        # Start the simulation
        print("🎭 Starting simulation...")
        threading.Thread(target=run_test_sequence, args=(tester,), daemon=True).start()
        
        try:
            # Run the GUI
            root.mainloop()
        except KeyboardInterrupt:
            print("\n🛑 Test stopped by user")

def run_test_sequence(tester):
    """Run the test sequence with simulated inputs"""
    print("🎭 Starting Test Sequence")
    print("=" * 30)
    
    # Wait for test to initialize
    time.sleep(2)
    
    try:
        # Test Step 1: Long UP Holds
        print("\n--- Simulating Step 1: Long UP Holds ---")
        simulate_long_holds(tester, 'UP', 3, 5)
        
        # Wait for auto-advance
        print("\n⏳ Waiting for auto-advance...")
        time.sleep(3)
        
        # Test Step 2: Long DOWN Holds
        print("\n--- Simulating Step 2: Long DOWN Holds ---")
        simulate_long_holds(tester, 'DOWN', 3, 5)
        
        # Wait for auto-advance
        print("\n⏳ Waiting for auto-advance...")
        time.sleep(3)
        
        # Test Step 3: Neutral Hold
        print("\n--- Simulating Step 3: Neutral Hold ---")
        simulate_neutral_hold(tester, 5)
        
        print("\n✅ Simulation completed!")
        
    except Exception as e:
        print(f"\n❌ Simulation error: {e}")
        import traceback
        traceback.print_exc()

def simulate_long_holds(tester, direction, count, duration):
    """Simulate long holds in a direction"""
    print(f"🎭 Simulating {count} long {direction} holds ({duration}s each)")
    
    for hold_num in range(count):
        print(f"\nHold {hold_num + 1}/{count}")
        
        # Simulate the hold by directly calling process_step_gaze
        start_time = time.time()
        while time.time() - start_time < duration + 0.5:
            gaze_result = simulate_gaze_input(direction, is_continuous=True, gaze_detected=False)
            
            if hasattr(tester, 'process_step_gaze'):
                tester.process_step_gaze(gaze_result)
            
            time.sleep(0.1)  # 100ms intervals
            
        # Brief neutral break between holds
        if hold_num < count - 1:
            print("  Neutral break...")
            for _ in range(5):  # 0.5 seconds of neutral
                neutral_result = simulate_gaze_input(None, is_continuous=False, gaze_detected=False)
                if hasattr(tester, 'process_step_gaze'):
                    tester.process_step_gaze(neutral_result)
                time.sleep(0.1)

def simulate_neutral_hold(tester, duration):
    """Simulate neutral hold"""
    print(f"🎭 Simulating neutral hold for {duration}s")
    
    start_time = time.time()
    while time.time() - start_time < duration + 0.5:
        neutral_result = simulate_gaze_input(None, is_continuous=False, gaze_detected=False)
        if hasattr(tester, 'process_step_gaze'):
            tester.process_step_gaze(neutral_result)
        time.sleep(0.1)

def main():
    """Main function"""
    run_simulation()

if __name__ == "__main__":
    main()
