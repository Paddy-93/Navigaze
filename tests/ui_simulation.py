#!/usr/bin/env python3
"""
UI Simulation for Comprehensive Gaze Tester
This brings up the actual UI and simulates camera inputs to show the test in action
"""

import time
import threading
import sys
import os
import numpy as np
from unittest.mock import patch, MagicMock

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class UISimulation:
    def __init__(self):
        self.tester = None
        self.simulation_running = False
        self.simulation_thread = None
        
    def create_mock_camera(self):
        """Create a mock camera that returns simulated frames"""
        mock_camera = MagicMock()
        
        # Create a mock frame (numpy array)
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock the read method to return True and the frame
        mock_camera.read.return_value = (True, mock_frame)
        mock_camera.isOpened.return_value = True
        
        return mock_camera
        
    def create_mock_mediapipe(self):
        """Create mock MediaPipe face detection"""
        mock_mp = MagicMock()
        mock_face_detection = MagicMock()
        mock_face_mesh = MagicMock()
        
        # Mock face detection results
        mock_face_detection.process.return_value = MagicMock()
        mock_face_mesh.process.return_value = MagicMock()
        
        mock_mp.solutions.face_detection = MagicMock(return_value=mock_face_detection)
        mock_mp.solutions.face_mesh = MagicMock(return_value=mock_face_mesh)
        
        return mock_mp
        
    def simulate_gaze_sequence(self, direction, duration, interval=0.1):
        """Simulate a gaze sequence"""
        print(f"🎭 SIMULATING: {direction} gaze for {duration}s")
        
        start_time = time.time()
        while time.time() - start_time < duration and self.simulation_running:
            # Create a simulated gaze result
            gaze_result = {
                'direction': direction,
                'offset': 0.02 if direction == 'UP' else -0.02 if direction == 'DOWN' else 0,
                'is_continuous_gaze': True,
                'gaze_detected': False,  # Simulate continuous gaze
                'pupil_relative': (0.5, 0.3 if direction == 'UP' else 0.7 if direction == 'DOWN' else 0.5),
                'confidence': 0.9
            }
            
            # Send to tester
            if hasattr(self.tester, 'process_step_gaze'):
                self.tester.process_step_gaze(gaze_result)
            
            time.sleep(interval)
            
    def simulate_neutral_gaze(self, duration, interval=0.1):
        """Simulate neutral gaze (no direction)"""
        print(f"🎭 SIMULATING: Neutral gaze for {duration}s")
        
        start_time = time.time()
        while time.time() - start_time < duration and self.simulation_running:
            # Create a neutral gaze result
            gaze_result = {
                'direction': None,
                'offset': 0,
                'is_continuous_gaze': False,
                'gaze_detected': False,
                'pupil_relative': (0.5, 0.5),
                'confidence': 0.9
            }
            
            # Send to tester
            if hasattr(self.tester, 'process_step_gaze'):
                self.tester.process_step_gaze(gaze_result)
            
            time.sleep(interval)
            
    def run_test_simulation(self):
        """Run the complete test simulation"""
        print("🎭 Starting UI Test Simulation")
        print("=" * 50)
        
        # Wait for tester to be ready
        time.sleep(3)
        
        try:
            # Test the first few steps
            print("\n📋 Testing Step 1: Long UP Holds")
            print("-" * 30)
            
            # Simulate 3 long UP holds
            for hold_num in range(3):
                print(f"\nHold {hold_num + 1}/3:")
                self.simulate_gaze_sequence('UP', 5.5)  # 5.5 seconds to ensure completion
                
                # Brief neutral break between holds
                if hold_num < 2:  # Don't add neutral after last hold
                    print("  Neutral break...")
                    self.simulate_neutral_gaze(1.0)
                    
            print("\n⏳ Waiting for auto-advance...")
            time.sleep(3)
            
            print("\n📋 Testing Step 2: Long DOWN Holds")
            print("-" * 30)
            
            # Simulate 3 long DOWN holds
            for hold_num in range(3):
                print(f"\nHold {hold_num + 1}/3:")
                self.simulate_gaze_sequence('DOWN', 5.5)  # 5.5 seconds to ensure completion
                
                # Brief neutral break between holds
                if hold_num < 2:  # Don't add neutral after last hold
                    print("  Neutral break...")
                    self.simulate_neutral_gaze(1.0)
                    
            print("\n⏳ Waiting for auto-advance...")
            time.sleep(3)
            
            print("\n📋 Testing Step 3: Neutral Hold")
            print("-" * 30)
            self.simulate_neutral_gaze(5.5)
            
            print("\n✅ Simulation completed!")
            
        except Exception as e:
            print(f"\n❌ Simulation error: {e}")
            import traceback
            traceback.print_exc()
            
    def start_simulation(self):
        """Start the simulation in a separate thread"""
        self.simulation_running = True
        self.simulation_thread = threading.Thread(target=self.run_test_simulation)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        
    def stop_simulation(self):
        """Stop the simulation"""
        self.simulation_running = False
        if self.simulation_thread:
            self.simulation_thread.join()

def main():
    """Main function to run the UI simulation"""
    print("🎭 Comprehensive Gaze Tester UI Simulation")
    print("This will show the actual UI and simulate gaze inputs")
    print("Press Ctrl+C to stop the simulation")
    print()
    
    # Apply patches to mock camera and mediapipe
    with patch('cv2.VideoCapture') as mock_camera, \
         patch('mediapipe') as mock_mp:
        
        # Set up mocks
        mock_camera.return_value.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_camera.return_value.isOpened.return_value = True
        
        # Mock mediapipe
        mock_face_detection = MagicMock()
        mock_face_mesh = MagicMock()
        mock_face_detection.process.return_value = MagicMock()
        mock_face_mesh.process.return_value = MagicMock()
        mock_mp.solutions.face_detection = MagicMock(return_value=mock_face_detection)
        mock_mp.solutions.face_mesh = MagicMock(return_value=mock_face_mesh)
        
        # Import and run the comprehensive gaze tester
        from comprehensive_gaze_tester import ComprehensiveGazeTester
        import tkinter as tk
        
        # Create the main window
        root = tk.Tk()
        
        # Create the tester
        tester = ComprehensiveGazeTester(root)
        
        # Create simulation
        simulation = UISimulation()
        simulation.tester = tester
        
        # Start simulation after a delay
        root.after(2000, simulation.start_simulation)  # Start simulation after 2 seconds
        
        try:
            # Run the GUI
            root.mainloop()
        except KeyboardInterrupt:
            print("\n🛑 Simulation stopped by user")
        finally:
            simulation.stop_simulation()

if __name__ == "__main__":
    main()
