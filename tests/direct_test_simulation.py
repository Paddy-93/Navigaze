#!/usr/bin/env python3
"""
Direct simulation of the comprehensive gaze tester
This patches the actual tester to simulate inputs and verify auto-advance
"""

import time
import sys
import os
import threading
from unittest.mock import patch, MagicMock
import numpy as np

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class DirectTestSimulator:
    def __init__(self):
        self.tester = None
        self.simulation_data = {
            'current_step': 0,
            'step_data': None,
            'test_results': [],
            'step_retry_count': 0,
            'max_retries': 3,
            'current_step': 0,
            'step_start_time': None
        }
        
    def create_mock_objects(self):
        """Create all the mock objects needed"""
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
        
        # Mock tkinter
        mock_tk = MagicMock()
        mock_root = MagicMock()
        mock_tk.Tk.return_value = mock_root
        
        return mock_cv2, mock_mp, mock_tk
        
    def simulate_gaze_input(self, direction, is_continuous=False, gaze_detected=True):
        """Simulate a gaze input"""
        gaze_result = {
            'direction': direction,
            'offset': 0.02 if direction == 'UP' else -0.02 if direction == 'DOWN' else 0,
            'is_continuous_gaze': is_continuous,
            'gaze_detected': gaze_detected,
            'pupil_relative': (0.5, 0.3 if direction == 'UP' else 0.7 if direction == 'DOWN' else 0.5),
            'confidence': 0.9
        }
        return gaze_result
        
    def test_hold_detection_logic(self):
        """Test the hold detection logic directly"""
        print("🧪 Testing Hold Detection Logic Directly")
        print("=" * 50)
        
        # Import the comprehensive gaze tester
        from comprehensive_gaze_tester import ComprehensiveGazeTester
        
        # Create a minimal tester instance
        tester = ComprehensiveGazeTester()
        
        # Set up test data
        tester.current_step = 0
        tester.test_steps = [
            {
                'name': 'Long UP Holds',
                'type': 'long_up',
                'repetitions': 3,
                'hold_duration': 5
            }
        ]
        
        tester.step_data = {
            'detections': [],
            'start_time': time.time(),
            'current_gaze_state': None,
            'hold_start_time': None
        }
        
        print("Testing single 5-second UP hold...")
        
        # Simulate 5 seconds of UP gaze
        start_time = time.time()
        hold_completed = False
        
        while time.time() - start_time < 6 and not hold_completed:
            gaze_result = self.simulate_gaze_input('UP', is_continuous=True, gaze_detected=False)
            
            # Call the process_step_gaze method
            try:
                tester.process_step_gaze(gaze_result)
                
                # Check if hold was completed
                if len(tester.step_data['detections']) > 0:
                    last_detection = tester.step_data['detections'][-1]
                    if last_detection.get('hold_duration', 0) > 0:
                        hold_completed = True
                        print(f"✅ Hold completed: {last_detection['hold_duration']:.1f}s")
                        
            except Exception as e:
                print(f"❌ Error processing gaze: {e}")
                break
                
            time.sleep(0.1)
            
        if hold_completed:
            print("✅ Single hold test PASSED")
        else:
            print("❌ Single hold test FAILED")
            
        return hold_completed
        
    def test_auto_advance_logic(self):
        """Test the auto-advance logic"""
        print("\n🧪 Testing Auto-Advance Logic")
        print("=" * 40)
        
        from comprehensive_gaze_tester import ComprehensiveGazeTester
        
        tester = ComprehensiveGazeTester()
        
        # Set up test data
        tester.current_step = 0
        tester.test_steps = [
            {
                'name': 'Long UP Holds',
                'type': 'long_up',
                'repetitions': 3,
                'hold_duration': 5
            },
            {
                'name': 'Long DOWN Holds',
                'type': 'long_down',
                'repetitions': 3,
                'hold_duration': 5
            }
        ]
        
        tester.step_data = {
            'detections': [],
            'start_time': time.time(),
            'current_gaze_state': None,
            'hold_start_time': None
        }
        
        print("Testing 3 long UP holds with auto-advance...")
        
        # Simulate 3 holds
        for hold_num in range(3):
            print(f"\nHold {hold_num + 1}/3:")
            
            # Simulate 5 seconds of UP gaze
            start_time = time.time()
            hold_completed = False
            
            while time.time() - start_time < 6 and not hold_completed:
                gaze_result = self.simulate_gaze_input('UP', is_continuous=True, gaze_detected=False)
                
                try:
                    tester.process_step_gaze(gaze_result)
                    
                    # Check if hold was completed
                    if len(tester.step_data['detections']) > 0:
                        last_detection = tester.step_data['detections'][-1]
                        if last_detection.get('hold_duration', 0) > 0:
                            hold_completed = True
                            print(f"  ✅ Hold {hold_num + 1} completed: {last_detection['hold_duration']:.1f}s")
                            
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    break
                    
                time.sleep(0.1)
                
            # Brief neutral break between holds
            if hold_num < 2:
                for _ in range(5):
                    neutral_result = self.simulate_gaze_input(None, is_continuous=False, gaze_detected=False)
                    try:
                        tester.process_step_gaze(neutral_result)
                    except:
                        pass
                    time.sleep(0.1)
                    
        # Check if step completion is detected
        try:
            is_complete = tester.check_step_completion()
            print(f"\nStep completion check: {is_complete}")
            
            if is_complete:
                print("✅ Auto-advance logic working correctly")
            else:
                print("❌ Auto-advance logic not working")
                
        except Exception as e:
            print(f"❌ Error checking step completion: {e}")
            
        return is_complete
        
    def run_comprehensive_test(self):
        """Run a comprehensive test of the system"""
        print("🎭 Comprehensive Gaze Tester Direct Simulation")
        print("=" * 60)
        
        # Test 1: Hold detection logic
        hold_test_passed = self.test_hold_detection_logic()
        
        # Test 2: Auto-advance logic
        auto_advance_passed = self.test_auto_advance_logic()
        
        # Summary
        print("\n📊 Test Results Summary:")
        print("=" * 30)
        print(f"Hold Detection Logic: {'✅ PASSED' if hold_test_passed else '❌ FAILED'}")
        print(f"Auto-Advance Logic: {'✅ PASSED' if auto_advance_passed else '❌ FAILED'}")
        
        if hold_test_passed and auto_advance_passed:
            print("\n🎉 All tests PASSED! The system should work correctly.")
        else:
            print("\n⚠️  Some tests FAILED. The system may not work as expected.")
            
        return hold_test_passed and auto_advance_passed

def main():
    """Main function"""
    simulator = DirectTestSimulator()
    success = simulator.run_comprehensive_test()
    
    if success:
        print("\n✅ Simulation completed successfully!")
    else:
        print("\n❌ Simulation found issues that need to be fixed.")

if __name__ == "__main__":
    main()
