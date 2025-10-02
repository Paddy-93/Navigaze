#!/usr/bin/env python3
"""
Focused App Detector - Monitors which application currently has focus and returns recommended modes
"""

import time
import platform
from config import APP_MODE_CONFIG

# Windows-specific imports
if platform.system() == "Windows":
    try:
        import win32gui
        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
        print("Warning: win32gui not available. App detection disabled.")
else:
    WINDOWS_AVAILABLE = False

class FocusedAppDetector:
    """Detects which application currently has focus and returns recommended modes"""
    
    def __init__(self):
        self.last_focused_app = None
        self.available = WINDOWS_AVAILABLE
        self.config = APP_MODE_CONFIG
    
    def get_focused_app(self):
        """Get the name of the currently focused application"""
        if not self.available:
            return "Unknown"
        
        try:
            if platform.system() == "Windows":
                hwnd = win32gui.GetForegroundWindow()
                app_name = win32gui.GetWindowText(hwnd)
                return app_name if app_name else "Unknown"
            else:
                return "Unknown"
        except Exception as e:
            print(f"⚠️ Error getting focused app: {e}")
            return "Unknown"
    
    def get_mode_for_app(self, app_name):
        """Get the recommended mode for a specific app"""
        if app_name in self.config['apps']:
            return self.config['apps'][app_name]
        return self.config['default_mode']
    
    def detect_app_change(self):
        """Check if the focused app has changed and return recommended mode"""
        current_app = self.get_focused_app()
        
        if current_app != self.last_focused_app:
            old_app = self.last_focused_app
            self.last_focused_app = current_app
            
            # Get recommended mode for new app
            recommended_mode = self.get_mode_for_app(current_app)
            
            print(f"🔄 App changed: {old_app} → {current_app}")
            return recommended_mode
        
        return None  # No change
