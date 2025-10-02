"""
Sequence Manager - Routes completed sequences and manages modes
"""

import time
from input_processing.command_executor import CommandExecutor

class SequenceManager:
    def __init__(self):
        self.command_executor = CommandExecutor()
        
        # Prompt management (mode management moved to main.py)
        self.prompt_timeout = 5000  # 5 seconds to choose
        self.prompt_start_time = 0
        
        # Sequence tracking (merged from SequenceTracker)
        self.sequence_pattern = []  # Track gaze sequence
        self.sequence_start_time = 0
        self.sequence_timeout_ms = 3000  # 3 seconds to complete sequence
        
        # Define sequence patterns
        self.sequences = {
            "mode_switch": {
                "pattern": ["UP", "DOWN", "UP", "DOWN"],
                "description": "Mode switching"
            },
            "enter": {
                "pattern": ["DOWN", "UP", "DOWN", "UP"],
                "description": "Enter key"
            },
            "escape": {
                "pattern": ["UP", "UP", "DOWN", "DOWN"],
                "description": "Escape key"
            },
            "windows": {
                "pattern": ["DOWN", "DOWN", "UP", "UP"],
                "description": "Windows key"
            }
        }
    
    def handle_sequence_complete(self, sequence_type):
        """Route completed sequences to appropriate handlers"""
        if sequence_type == "mode_switch":
            return self._handle_mode_switch_sequence()
        elif sequence_type == "enter":
            return self.command_executor.execute_enter()
        elif sequence_type == "escape":
            return self.command_executor.execute_escape()
        elif sequence_type == "windows":
            print("🔄 About to execute Windows key...")
            result = self.command_executor.execute_windows_key()
            print("✅ Windows key execution completed")
            return result
        else:
            print(f"⚠️ Unknown sequence type: {sequence_type}")
            return None
    
    def handle_gaze(self, direction, current_mode):
        """Handle gaze based on current mode"""
        if current_mode == "PROMPT":
            return self._handle_gaze_in_prompt(direction)
        elif current_mode == "TAB":
            return self.command_executor.execute_tab_command(direction)
        elif current_mode == "SCROLL":
            return self.command_executor.execute_scroll_command(direction)
        else:
            print(f"⚠️ Unknown mode: {current_mode}")
            return None
    
    def check_timeouts(self, current_mode):
        """Check for any timeouts (prompt and sequence)"""
        # Check prompt timeout
        prompt_timeout = self._check_prompt_timeout(current_mode)
        if prompt_timeout:
            return prompt_timeout
        
        # Check sequence timeout
        sequence_timeout = self._check_sequence_timeout()
        if sequence_timeout:
            return sequence_timeout
        
        return None
    
    # Mode management removed - main.py is now the single source of truth
    
    def add_gaze(self, direction):
        """Add a gaze direction to the sequence and check for patterns"""
        now_ms = time.time() * 1000.0
        
        # Start or continue sequence tracking
        if len(self.sequence_pattern) == 0:
            # Starting new sequence
            self.sequence_pattern = [direction]
            self.sequence_start_time = now_ms
            print(f"Sequence: Started with {direction} (1/?)")
            return {
                'sequence_complete': False,
                'sequence_type': None,
                'current_sequence': '-'.join(self.sequence_pattern),
                'timeout': False
            }
        
        # Add the new direction to the pattern (continuing existing sequence)
        self.sequence_pattern.append(direction)
        pattern_str = ''.join(self.sequence_pattern)
        print(f"Sequence: Added {direction} - {pattern_str}")
        
        # Check if current pattern matches any of our target sequences
        for seq_name, seq_info in self.sequences.items():
            target_pattern = seq_info["pattern"]
            
            
            # Check if we have a complete match
            if len(self.sequence_pattern) == len(target_pattern):
                if self.sequence_pattern == target_pattern:
                    print(f"🎯 SEQUENCE COMPLETE: {'-'.join(self.sequence_pattern)} ({seq_info['description']}) in {(now_ms - self.sequence_start_time)/1000:.1f}s")
                    
                    # Reset sequence for next detection
                    completed_sequence = '-'.join(self.sequence_pattern)
                    self.sequence_pattern = []
                    
                    return {
                        'sequence_complete': True,
                        'sequence_type': seq_name,
                        'current_sequence': '',  # Cleared after completion
                        'timeout': False,
                        'completed_sequence': completed_sequence
                    }
            
            # Check if we're on track for this sequence (partial match)
            elif len(self.sequence_pattern) < len(target_pattern):
                if self.sequence_pattern == target_pattern[:len(self.sequence_pattern)]:
                    # Still matching this sequence - continue
                    progress = f"({len(self.sequence_pattern)}/{len(target_pattern)})"
                    print(f"Sequence: Progress {progress} for {seq_info['description']}")
                    return {
                        'sequence_complete': False,
                        'sequence_type': None,
                        'current_sequence': '-'.join(self.sequence_pattern),
                        'timeout': False
                    }
        
        # If we get here, no sequence matches - clear and restart with current direction
        print(f"Sequence: No match - Clearing invalid sequence {'-'.join(self.sequence_pattern)}")
        self.sequence_pattern = [direction]
        self.sequence_start_time = now_ms
        print(f"Sequence: Started fresh with {direction} (1/?)")
        
        return {
            'sequence_complete': False,
            'sequence_type': None,
            'current_sequence': '-'.join(self.sequence_pattern),
            'timeout': False,
            'invalid_cleared': True
        }
    
    def get_current_sequence(self):
        """Get the current sequence as a string"""
        return '-'.join(self.sequence_pattern) if self.sequence_pattern else ''
    
    def clear_sequence(self):
        """Clear the current sequence"""
        self.sequence_pattern = []
        self.sequence_start_time = 0
    
    def _handle_mode_switch_sequence(self):
        """Handle the specific mode switch sequence completion"""
        self.prompt_start_time = time.time() * 1000  # Convert to ms
        return {
            "mode": "PROMPT", 
            "prompt": "Look UP for SCROLL, DOWN for TAB",
            "timeout": self.prompt_timeout
        }
    
    def _handle_gaze_in_prompt(self, direction):
        """Handle gaze when in prompt mode"""
        if direction == "UP":
            return {"mode": "SCROLL", "prompt": ""}
        elif direction == "DOWN":
            return {"mode": "TAB", "prompt": ""}
        return None
    
    def _check_prompt_timeout(self, current_mode):
        """Check if prompt has timed out"""
        if current_mode == "PROMPT":
            now_ms = time.time() * 1000
            if now_ms - self.prompt_start_time > self.prompt_timeout:
                return {"mode": "TAB", "prompt": "", "timeout": True}
        return None
    
    def _check_sequence_timeout(self):
        """Check if sequence has timed out"""
        if len(self.sequence_pattern) > 0:
            now_ms = time.time() * 1000.0
            if now_ms - self.sequence_start_time > self.sequence_timeout_ms:
                print(f"Sequence: Timeout - Clearing {'-'.join(self.sequence_pattern)}")
                self.sequence_pattern = []
                self.sequence_start_time = 0
                return {"sequence_cleared": True, "timeout": True}
        return None
