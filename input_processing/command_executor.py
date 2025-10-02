"""
Command Executor - Executes keyboard commands based on gaze directions
"""
from pynput.keyboard import Controller, Key
import time

class CommandExecutor:
    def __init__(self):
        self.keyboard = Controller()
    
    def execute_tab_command(self, direction):
        """Execute tab navigation based on gaze direction"""
        if direction == "UP":
            self.keyboard.press(Key.tab)
            self.keyboard.release(Key.tab)
            print("⌨️  TAB FORWARD")
        elif direction == "DOWN":
            self.keyboard.press(Key.shift)
            self.keyboard.press(Key.tab)
            self.keyboard.release(Key.tab)
            self.keyboard.release(Key.shift)
            print("⌨️  TAB BACKWARD (Shift+Tab)")
    
    def execute_scroll_command(self, direction):
        """Execute scroll commands based on gaze direction"""
        if direction == "UP":
            self.keyboard.press(Key.up)
            self.keyboard.release(Key.up)
            print("⌨️  SCROLL UP")
        elif direction == "DOWN":
            self.keyboard.press(Key.down)
            self.keyboard.release(Key.down)
            print("⌨️  SCROLL DOWN")
    
    def execute_enter(self):
        self.keyboard.press(Key.enter)
        self.keyboard.release(Key.enter)
        print("⌨️  ENTER KEY")
    
    def execute_escape(self):
        self.keyboard.press(Key.esc)
        self.keyboard.release(Key.esc)
        print("⌨️  ESCAPE KEY")
    
    def execute_windows_key(self):
        time.sleep(1.05)
        self.keyboard.press(Key.cmd)
        time.sleep(0.05)
        self.keyboard.release(Key.cmd)
        time.sleep(1.05)
        print("⌨️  WINDOWS KEY")
    
    def execute_windows_tab_tab(self):
        """Execute Windows key followed by two tab presses"""
        time.sleep(0.5)  # Small delay before Windows key
        self.keyboard.press(Key.cmd)  # Windows key
        self.keyboard.release(Key.cmd)
        time.sleep(0.3)  # Wait for Windows menu to appear
        
        # Press Tab twice
        self.keyboard.press(Key.tab)
        self.keyboard.release(Key.tab)
        time.sleep(0.1)
        self.keyboard.press(Key.tab)
        self.keyboard.release(Key.tab)
        
        print("⌨️  WINDOWS + TAB + TAB")