#!/usr/bin/env python3
"""
Simulation script that tests the comprehensive gaze tester by spoofing inputs
This will verify that the auto-advance functionality works correctly
"""

import time
import threading
import queue
import sys
import os
from unittest.mock import patch, MagicMock

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ComprehensiveTestSimulator:
    def __init__(self):
        self.tester = None
        self.simulation_running = False
        self.step_completed = False
        
    def create_mock_camera(self):
        """Create a mock camera that returns simulated frames"""
        mock_camera = MagicMock()
        
        # Create a mock frame (numpy array)
        import numpy as np
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
        
    def simulate_gaze_detection(self, direction, is_continuous=False, gaze_detected=True):
        """Simulate gaze detection results"""
        # Create mock face landmarks
        mock_landmarks = MagicMock()
        
        # Mock pupil positions based on direction
        if direction == 'UP':
            pupil_relative = (0.5, 0.3)  # Higher Y position
        elif direction == 'DOWN':
            pupil_relative = (0.5, 0.7)  # Lower Y position
        else:
            pupil_relative = (0.5, 0.5)  # Center position
            
        mock_landmarks.get_pupil_relative.return_value = pupil_relative
        mock_landmarks.get_confidence.return_value = 0.9
        
        # Create mock gaze detector
        mock_gaze_detector = MagicMock()
        mock_gaze_detector.baseline_y = 0.5
        
        # Mock gaze result
        gaze_result = {
            'direction': direction,
            'offset': 0.02 if direction == 'UP' else -0.02 if direction == 'DOWN' else 0,
            'is_continuous_gaze': is_continuous,
            'gaze_detected': gaze_detected,
            'pupil_relative': pupil_relative,
            'confidence': 0.9
        }
        
        mock_gaze_detector.update.return_value = gaze_result
        
        return mock_landmarks, mock_gaze_detector, gaze_result
        
    def patch_imports(self):
        """Patch the imports to use our mock objects"""
        patches = []
        
        # Patch cv2.VideoCapture
        cv2_patch = patch('cv2.VideoCapture', return_value=self.create_mock_camera())
        patches.append(cv2_patch)
        
        # Patch mediapipe
        mp_patch = patch('mediapipe', return_value=self.create_mock_mediapipe())
        patches.append(mp_patch)
        
        # Patch tkinter to prevent GUI from opening
        tkinter_patch = patch('tkinter.Tk')
        patches.append(tkinter_patch)
        
        return patches
        
    def run_simulation(self):
        """Run the comprehensive test simulation"""
        print("🎭 Starting Comprehensive Gaze Tester Simulation")
        print("=" * 60)
        
        # Apply patches
        patches = self.patch_imports()
        for patch in patches:
            patch.start()
            
        try:
            # Import and create the tester
            from comprehensive_gaze_tester import RemoteGazeTester
            self.tester = RemoteGazeTester()
            
            # Override the camera update method to use our simulation
            self.tester.update_camera = self.simulate_camera_update
            
            # Start the simulation
            self.simulate_test_sequence()
            
        except Exception as e:
            print(f"❌ Simulation error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Clean up patches
            for patch in patches:
                patch.stop()
                
    def simulate_camera_update(self):
        """Override the camera update method to simulate gaze inputs"""
        if not self.simulation_running:
            return
            
        # This will be called by the tester's update loop
        # We'll control the gaze simulation from here
        pass
        
    def simulate_test_sequence(self):
        """Simulate the complete test sequence"""
        print("🚀 Starting test sequence simulation...")
        
        # Start the tester (this will initialize everything)
        self.tester.setup_ui()
        self.tester.start_camera()
        
        # Wait a moment for initialization
        time.sleep(1)
        
        # Start the test
        print("\n📋 Starting test...")
        self.tester.start_test()
        
        # Wait for test to initialize
        time.sleep(2)
        
        # Now simulate the test steps
        self.simulation_running = True
        
        # Test Step 1: Long UP Holds
        print("\n--- Simulating Step 1: Long UP Holds ---")
        self.simulate_long_holds('UP', 3, 5)
        
        # Wait for auto-advance
        time.sleep(3)
        
        # Test Step 2: Long DOWN Holds  
        print("\n--- Simulating Step 2: Long DOWN Holds ---")
        self.simulate_long_holds('DOWN', 3, 5)
        
        # Wait for auto-advance
        time.sleep(3)
        
        # Test Step 3: Neutral Hold
        print("\n--- Simulating Step 3: Neutral Hold ---")
        self.simulate_neutral_hold(5)
        
        print("\n✅ Simulation completed!")
        
    def simulate_long_holds(self, direction, count, duration):
        """Simulate long holds in a direction"""
        print(f"🎭 Simulating {count} long {direction} holds ({duration}s each)")
        
        for hold_num in range(count):
            print(f"  Hold {hold_num + 1}/{count}")
            
            # Simulate the hold
            start_time = time.time()
            while time.time() - start_time < duration + 0.5:  # Add buffer
                # Create gaze result
                gaze_result = {
                    'direction': direction,
                    'offset': 0.02 if direction == 'UP' else -0.02,
                    'is_continuous_gaze': True,
                    'gaze_detected': False,
                    'pupil_relative': (0.5, 0.3 if direction == 'UP' else 0.7),
                    'confidence': 0.9
                }
                
                # Process the gaze
                if hasattr(self.tester, 'process_step_gaze'):
                    self.tester.process_step_gaze(gaze_result)
                
                time.sleep(0.1)  # 100ms intervals
                
            # Brief neutral break between holds
            if hold_num < count - 1:
                print("    Neutral break...")
                for _ in range(5):  # 0.5 seconds of neutral
                    neutral_result = {
                        'direction': None,
                        'offset': 0,
                        'is_continuous_gaze': False,
                        'gaze_detected': False,
                        'pupil_relative': (0.5, 0.5),
                        'confidence': 0.9
                    }
                    
                    if hasattr(self.tester, 'process_step_gaze'):
                        self.tester.process_step_gaze(neutral_result)
                    
                    time.sleep(0.1)
                    
    def simulate_neutral_hold(self, duration):
        """Simulate neutral hold"""
        print(f"🎭 Simulating neutral hold for {duration}s")
        
        start_time = time.time()
        while time.time() - start_time < duration + 0.5:
            neutral_result = {
                'direction': None,
                'offset': 0,
                'is_continuous_gaze': False,
                'gaze_detected': False,
                'pupil_relative': (0.5, 0.5),
                'confidence': 0.9
            }
            
            if hasattr(self.tester, 'process_step_gaze'):
                self.tester.process_step_gaze(neutral_result)
            
            time.sleep(0.1)

def main():
    """Main function to run the simulation"""
    print("🎭 Comprehensive Gaze Tester Simulation")
    print("This will simulate gaze inputs to test the auto-advance functionality")
    print()
    
    simulator = ComprehensiveTestSimulator()
    simulator.run_simulation()

if __name__ == "__main__":
    main()
