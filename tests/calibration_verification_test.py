#!/usr/bin/env python3
"""
Calibration Verification Test
Specifically tests that the calibration display appears correctly
"""

import tkinter as tk
import time
import threading
from comprehensive_gaze_tester_refactored import ComprehensiveGazeTester
from simulated_gaze_detector import SimulatedGazeDetector

class CalibrationVerificationTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Calibration Verification Test")
        
        # Initialize gaze detector and tester
        self.gaze_detector = SimulatedGazeDetector()
        self.tester = None
        
        # Test state
        self.test_passed = False
        self.test_failed = False
        
    def run_test(self):
        """Run the calibration verification test"""
        print("🧪 Starting Calibration Verification Test")
        print("=" * 60)
        
        try:
            # Step 1: Initialize the comprehensive gaze tester
            print("📋 Step 1: Initializing comprehensive gaze tester...")
            self.tester = ComprehensiveGazeTester(self.root, self.gaze_detector)
            print("✅ Comprehensive gaze tester initialized")
            
            # Step 2: Check initial state
            print("📋 Step 2: Checking initial state...")
            initial_text = self.tester.instruction_display.cget("text")
            initial_bg = self.tester.instruction_display.cget("bg")
            print(f"   Initial text: {initial_text[:50]}...")
            print(f"   Initial background: {initial_bg}")
            
            # Step 3: Start the test
            print("📋 Step 3: Starting test...")
            self.tester.start_test()
            print("✅ Test started")
            
            # Step 4: Wait for calibration display to appear
            print("📋 Step 4: Waiting for calibration display...")
            self.wait_for_calibration_display()
            
        except Exception as e:
            print(f"❌ TEST FAILED: Exception occurred - {e}")
            self.test_failed = True
            
        finally:
            # Wait to see final state
            print("\n⏳ Waiting 3 seconds to see final state...")
            time.sleep(3)
            
            # Cleanup
            if self.tester and hasattr(self.tester, 'cleanup'):
                self.tester.cleanup()
            self.root.destroy()
            
        return self.test_passed
    
    def wait_for_calibration_display(self):
        """Wait for calibration display to appear and verify it"""
        max_wait_time = 10  # Maximum 10 seconds to wait
        check_interval = 0.5  # Check every 0.5 seconds
        elapsed_time = 0
        
        print("   Checking for calibration display every 0.5 seconds...")
        
        while elapsed_time < max_wait_time:
            time.sleep(check_interval)
            elapsed_time += check_interval
            
            # Get current display state
            current_text = self.tester.instruction_display.cget("text")
            current_bg = self.tester.instruction_display.cget("bg")
            current_fg = self.tester.instruction_display.cget("fg")
            
            print(f"   [{elapsed_time:.1f}s] Text: {current_text[:30]}... | BG: {current_bg} | FG: {current_fg}")
            
            # Check if calibration display is showing
            if self.is_calibration_display_correct(current_text, current_bg, current_fg):
                print("✅ CALIBRATION DISPLAY FOUND!")
                self.verify_calibration_display(current_text, current_bg, current_fg)
                return
            
        print("❌ TIMEOUT: Calibration display did not appear within 10 seconds")
        self.test_failed = True
    
    def is_calibration_display_correct(self, text, bg, fg):
        """Check if the display shows calibration correctly"""
        # Check for red background
        if bg.lower() not in ['red', '#ff0000', '#f00']:
            return False
            
        # Check for white text
        if fg.lower() not in ['white', '#ffffff', '#fff']:
            return False
            
        # Check for calibration text
        if "CALIBRATION" not in text.upper():
            return False
            
        if "red dot" not in text.lower():
            return False
            
        return True
    
    def verify_calibration_display(self, text, bg, fg):
        """Verify the calibration display details"""
        print("\n🔍 CALIBRATION DISPLAY VERIFICATION:")
        print(f"   Text: {text}")
        print(f"   Background: {bg}")
        print(f"   Foreground: {fg}")
        
        # Verification checks
        checks_passed = 0
        total_checks = 4
        
        # Check 1: Red background
        if bg.lower() in ['red', '#ff0000', '#f00']:
            print("   ✅ PASS: Background is red")
            checks_passed += 1
        else:
            print(f"   ❌ FAIL: Background is {bg}, should be red")
            
        # Check 2: White text
        if fg.lower() in ['white', '#ffffff', '#fff']:
            print("   ✅ PASS: Text is white")
            checks_passed += 1
        else:
            print(f"   ❌ FAIL: Text color is {fg}, should be white")
            
        # Check 3: Contains "CALIBRATION"
        if "CALIBRATION" in text.upper():
            print("   ✅ PASS: Contains 'CALIBRATION'")
            checks_passed += 1
        else:
            print("   ❌ FAIL: Missing 'CALIBRATION' text")
            
        # Check 4: Contains "red dot"
        if "red dot" in text.lower():
            print("   ✅ PASS: Contains 'red dot'")
            checks_passed += 1
        else:
            print("   ❌ FAIL: Missing 'red dot' text")
            
        # Overall result
        if checks_passed == total_checks:
            print(f"\n🎯 CALIBRATION VERIFICATION: PASSED ({checks_passed}/{total_checks})")
            self.test_passed = True
        else:
            print(f"\n💥 CALIBRATION VERIFICATION: FAILED ({checks_passed}/{total_checks})")
            self.test_failed = True

def main():
    """Main test function"""
    test = CalibrationVerificationTest()
    
    print("🚀 Calibration Verification Test Starting...")
    print("This test will:")
    print("1. Initialize the comprehensive gaze tester")
    print("2. Start the test")
    print("3. Wait for calibration display to appear")
    print("4. Verify the display has red background and correct text")
    print()
    
    success = test.run_test()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST RESULT: PASSED")
        print("✅ Calibration display appears correctly with red background and proper text")
    else:
        print("💥 TEST RESULT: FAILED")
        print("❌ Calibration display did not appear correctly")
    
    return success

if __name__ == "__main__":
    main()
