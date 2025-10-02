#!/usr/bin/env python3
"""
Minimal test to isolate the crash
"""

import tkinter as tk
from tkinter import ttk
import os
import time
from datetime import datetime

class MinimalTester:
    def __init__(self, master):
        self.root = master
        self.root.title("Crash Test")
        self.root.geometry("400x300")
        
        # Simple UI
        frame = ttk.Frame(self.root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.start_button = ttk.Button(frame, text="Start Test", command=self.start_test)
        self.start_button.pack(pady=10)
        
        self.results_text = tk.Text(frame, height=10)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        self.log_result("Minimal tester initialized")
    
    def log_result(self, message):
        timestamp = time.strftime("[%H:%M:%S]")
        self.results_text.insert(tk.END, f"{timestamp} {message}\n")
        self.results_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_test(self):
        try:
            self.log_result("Starting test...")
            
            # Create directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = f"gaze_recordings/session_{timestamp}"
            os.makedirs(session_dir, exist_ok=True)
            self.log_result(f"Created directory: {session_dir}")
            
            # Disable button
            self.start_button.config(state=tk.DISABLED)
            self.log_result("Button disabled")
            
            # Schedule next step
            self.root.after(2000, self.next_step)
            self.log_result("Scheduled next step")
            
        except Exception as e:
            self.log_result(f"ERROR in start_test: {e}")
            import traceback
            self.log_result(f"Traceback: {traceback.format_exc()}")
    
    def next_step(self):
        try:
            self.log_result("Next step called")
            self.start_button.config(state=tk.NORMAL)
            self.log_result("Test completed successfully")
        except Exception as e:
            self.log_result(f"ERROR in next_step: {e}")
            import traceback
            self.log_result(f"Traceback: {traceback.format_exc()}")

def main():
    root = tk.Tk()
    app = MinimalTester(root)
    
    try:
        root.mainloop()
    except Exception as e:
        print(f"Main loop error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

