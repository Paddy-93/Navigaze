#!/usr/bin/env python3
"""
Simulation script for testing the comprehensive gaze tester
This script simulates gaze inputs to test the auto-advance functionality
"""

import time
import threading
import queue
from comprehensive_gaze_tester import RemoteGazeTester

class GazeSimulator:
    def __init__(self):
        self.tester = None
        self.simulation_queue = queue.Queue()
        self.running = False
        
    def create_tester(self):
        """Create the gaze tester instance"""
        self.tester = RemoteGazeTester()
        return self.tester
        
    def simulate_gaze_sequence(self, direction, duration, interval=0.1):
        """Simulate a gaze in a specific direction for a given duration"""
        print(f"🎭 SIMULATING: {direction} gaze for {duration}s")
        
        start_time = time.time()
        while time.time() - start_time < duration and self.running:
            # Create a simulated gaze result
            gaze_result = {
                'direction': direction,
                'offset': 0.02 if direction == 'UP' else -0.02,
                'is_continuous_gaze': True,
                'gaze_detected': False,  # Simulate continuous gaze
                'pupil_relative': (0.5, 0.3 if direction == 'UP' else 0.7),
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
        while time.time() - start_time < duration and self.running:
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
            
    def simulate_quick_gazes(self, direction, count, interval=0.5):
        """Simulate quick gazes in a direction"""
        print(f"🎭 SIMULATING: {count} quick {direction} gazes")
        
        for i in range(count):
            if not self.running:
                break
                
            # Quick gaze detection
            gaze_result = {
                'direction': direction,
                'offset': 0.02 if direction == 'UP' else -0.02,
                'is_continuous_gaze': False,
                'gaze_detected': True,
                'pupil_relative': (0.5, 0.3 if direction == 'UP' else 0.7),
                'confidence': 0.9
            }
            
            if hasattr(self.tester, 'process_step_gaze'):
                self.tester.process_step_gaze(gaze_result)
            
            # Brief neutral between gazes
            time.sleep(0.2)
            self.simulate_neutral_gaze(0.3)
            time.sleep(interval)
            
    def simulate_long_holds(self, direction, count, hold_duration=5):
        """Simulate long holds in a direction"""
        print(f"🎭 SIMULATING: {count} long {direction} holds ({hold_duration}s each)")
        
        for i in range(count):
            if not self.running:
                break
                
            print(f"  Hold {i+1}/{count}")
            
            # Start hold
            self.simulate_gaze_sequence(direction, hold_duration + 0.5)
            
            # Brief neutral between holds
            if i < count - 1:  # Don't add neutral after last hold
                self.simulate_neutral_gaze(1.0)
                
    def simulate_sequence_pattern(self, pattern, repetitions):
        """Simulate a sequence pattern (e.g., UP-DOWN-UP-DOWN)"""
        print(f"🎭 SIMULATING: {repetitions} repetitions of {'→'.join(pattern)}")
        
        for rep in range(repetitions):
            if not self.running:
                break
                
            print(f"  Sequence {rep+1}/{repetitions}")
            
            for direction in pattern:
                if not self.running:
                    break
                    
                # Quick gaze for each direction in sequence
                gaze_result = {
                    'direction': direction,
                    'offset': 0.02 if direction == 'UP' else -0.02,
                    'is_continuous_gaze': False,
                    'gaze_detected': True,
                    'pupil_relative': (0.5, 0.3 if direction == 'UP' else 0.7),
                    'confidence': 0.9
                }
                
                if hasattr(self.tester, 'process_step_gaze'):
                    self.tester.process_step_gaze(gaze_result)
                
                # Brief pause between directions
                time.sleep(0.3)
                
            # Pause between sequences
            if rep < repetitions - 1:
                time.sleep(0.5)
                
    def run_test_simulation(self):
        """Run a complete test simulation"""
        print("🚀 Starting Gaze Test Simulation")
        print("=" * 50)
        
        self.running = True
        
        try:
            # Wait for tester to be ready
            time.sleep(2)
            
            # Test the first few steps
            test_steps = [
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
                },
                {
                    'name': 'Neutral Hold',
                    'type': 'neutral_hold',
                    'hold_duration': 5
                },
                {
                    'name': 'UP-DOWN-UP-DOWN Sequence',
                    'type': 'sequence_up_down_up_down',
                    'pattern': ['UP', 'DOWN', 'UP', 'DOWN'],
                    'repetitions': 3
                }
            ]
            
            for step in test_steps:
                if not self.running:
                    break
                    
                print(f"\n📋 Testing: {step['name']}")
                print("-" * 30)
                
                if step['type'] == 'long_up':
                    self.simulate_long_holds('UP', step['repetitions'], step['hold_duration'])
                elif step['type'] == 'long_down':
                    self.simulate_long_holds('DOWN', step['repetitions'], step['hold_duration'])
                elif step['type'] == 'neutral_hold':
                    self.simulate_neutral_gaze(step['hold_duration'])
                elif step['type'].startswith('sequence_'):
                    self.simulate_sequence_pattern(step['pattern'], step['repetitions'])
                
                # Wait for step completion
                print(f"⏳ Waiting for step completion...")
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n🛑 Simulation interrupted by user")
        except Exception as e:
            print(f"\n❌ Simulation error: {e}")
        finally:
            self.running = False
            print("\n✅ Simulation completed")

def main():
    """Main function to run the simulation"""
    print("🎭 Gaze Test Simulator")
    print("This will simulate gaze inputs to test auto-advance functionality")
    print()
    
    simulator = GazeSimulator()
    
    # Create tester in a separate thread
    def create_tester_thread():
        try:
            tester = simulator.create_tester()
            print("✅ Tester created successfully")
        except Exception as e:
            print(f"❌ Failed to create tester: {e}")
            return
    
    # Start tester creation
    tester_thread = threading.Thread(target=create_tester_thread)
    tester_thread.start()
    
    # Wait a bit for tester to initialize
    time.sleep(3)
    
    # Start simulation
    simulator.run_test_simulation()

if __name__ == "__main__":
    main()
