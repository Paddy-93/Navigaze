#!/usr/bin/env python3
"""
Simple test for continuous gaze firing system
Tests the core functionality without complex timing
"""

import time
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

from eye_tracking.gaze_detector import GazeDetector
from config import CONTINUOUS_GAZE_CONFIG

def test_gaze_detector_basic():
    """Test basic gaze detector functionality"""
    print("🧪 Testing Gaze Detector Basic Functionality")
    print("=" * 50)
    
    detector = GazeDetector()
    detector.baseline_y = 0.5  # Set baseline
    
    # Test 1: Initial gaze detection
    print("  Test 1: Initial gaze detection")
    result = detector.update(0.6, head_moving=False, is_blinking=False)  # UP gaze
    print(f"    Gaze detected: {result.get('gaze_detected', False)}")
    print(f"    Direction: {result.get('direction', 'None')}")
    print(f"    Is continuous: {result.get('is_continuous_gaze', False)}")
    
    # Test 2: Continuous gaze after hold time
    print("\n  Test 2: Continuous gaze after hold time")
    print("    Simulating 1.2 seconds of continuous UP gaze...")
    
    # Simulate time passing by calling update multiple times
    for i in range(5):  # 5 calls over 1.2 seconds
        time.sleep(0.25)  # 250ms between calls
        result = detector.update(0.6, head_moving=False, is_blinking=False)  # UP gaze
        print(f"    Call {i+1}: continuous={result.get('is_continuous_gaze', False)}")
    
    # Test 3: Neutral gaze stops continuous
    print("\n  Test 3: Neutral gaze stops continuous")
    result = detector.update(0.5, head_moving=False, is_blinking=False)  # Neutral
    print(f"    After neutral: continuous={result.get('is_continuous_gaze', False)}")
    
    # Test 4: Direction change resets timer
    print("\n  Test 4: Direction change resets timer")
    result = detector.update(0.4, head_moving=False, is_blinking=False)  # DOWN gaze
    print(f"    After DOWN: continuous={result.get('is_continuous_gaze', False)}")
    
    print("\n  ✅ Basic gaze detector tests completed!")

def test_configuration():
    """Test configuration values"""
    print("\n🧪 Testing Configuration Values")
    print("=" * 50)
    
    hold_threshold = CONTINUOUS_GAZE_CONFIG['hold_threshold_ms']
    repeat_rate = CONTINUOUS_GAZE_CONFIG['repeat_rate_ms']
    
    print(f"  Hold threshold: {hold_threshold}ms")
    print(f"  Repeat rate: {repeat_rate}ms")
    
    if hold_threshold == 1000 and repeat_rate == 500:
        print("  ✅ Configuration values are correct!")
    else:
        print("  ❌ Configuration values are incorrect!")

def test_continuous_timing():
    """Test continuous gaze timing"""
    print("\n🧪 Testing Continuous Gaze Timing")
    print("=" * 50)
    
    detector = GazeDetector()
    detector.baseline_y = 0.5
    
    # Start with UP gaze
    print("  Starting UP gaze...")
    result = detector.update(0.6, head_moving=False, is_blinking=False)
    print(f"    Initial: continuous={result.get('is_continuous_gaze', False)}")
    
    # Wait for continuous threshold
    print("  Waiting for continuous threshold (1000ms)...")
    start_time = time.time()
    
    while time.time() - start_time < 2.0:  # Wait up to 2 seconds
        time.sleep(0.1)  # Check every 100ms
        result = detector.update(0.6, head_moving=False, is_blinking=False)
        is_continuous = result.get('is_continuous_gaze', False)
        elapsed = time.time() - start_time
        
        if is_continuous:
            print(f"    ✅ Became continuous after {elapsed:.1f}s")
            break
        else:
            print(f"    Waiting... {elapsed:.1f}s")
    else:
        print("    ❌ Never became continuous!")
        return False
    
    # Test that it stays continuous
    print("  Testing that it stays continuous...")
    for i in range(3):
        time.sleep(0.2)
        result = detector.update(0.6, head_moving=False, is_blinking=False)
        is_continuous = result.get('is_continuous_gaze', False)
        print(f"    Check {i+1}: continuous={is_continuous}")
        if not is_continuous:
            print("    ❌ Stopped being continuous!")
            return False
    
    print("  ✅ Continuous timing test passed!")
    return True

def main():
    """Run all tests"""
    print("🚀 Simple Continuous Gaze Tests")
    print("=" * 60)
    
    test_gaze_detector_basic()
    test_configuration()
    test_continuous_timing()
    
    print("\n🎉 All simple tests completed!")
    print("\nTo test the full system:")
    print("1. Run 'python main.py'")
    print("2. Look UP for 1+ seconds to trigger continuous firing")
    print("3. Look DOWN for 1+ seconds to trigger continuous firing")
    print("4. Look neutral to stop firing")

if __name__ == "__main__":
    main()

