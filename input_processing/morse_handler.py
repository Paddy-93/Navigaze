import time
import cv2
from config import MORSE_CONFIG
from input_processing.morse_dict import MORSE_DICT, MORSE_COMMANDS

# Import keyboard functionality
try:
    from pynput.keyboard import Key, Controller
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("Warning: pynput not available. Keyboard typing will be disabled.")

class MorseInputHandler:
    """Handles Morse code input using gaze detection"""
    
    def __init__(self, enable_typing=True, on_text_submitted=None):
        self.config = MORSE_CONFIG
        self.morse_dict = MORSE_DICT
        self.morse_commands = MORSE_COMMANDS
        
        # Callback for when text is submitted
        self.on_text_submitted = on_text_submitted
        
        # Keyboard functionality
        self.enable_typing = enable_typing and KEYBOARD_AVAILABLE
        if self.enable_typing:
            self.keyboard = Controller()
        else:
            self.keyboard = None
        
        # State variables
        self.current_text = ""
        self.current_morse = ""
        self.current_word = ""
        
        # Gaze state tracking - only change when actually moving eyes
        self.current_gaze_state = None  # "UP", "DOWN", or None (neutral)
        self.last_gaze_state = None     # Previous gaze state
        self.gaze_stable_time = 0       # When current gaze state started
        self.gaze_stability_ms = 100    # Must hold gaze for 100ms to register change
        
        # Timing variables
        self.gaze_start_time = None
        self.last_gaze_direction = None
        self.last_cursor_blink = 0
        self.cursor_visible = True
        
        # Hold detection for UP/DOWN (space/backspace)
        self.hold_start_time = None
        self.hold_direction = None
        self.hold_executed = False
        
        # Separate neutral hold for letter completion and submission
        self.neutral_hold_start = None
        self.letter_completed = False  # Track if 1-second letter completion happened
        
        # Track if we added a symbol that might need to be removed due to hold action
        self.pending_hold_symbol = None  # Track the symbol added for potential hold
        
    def update(self, gaze_result, head_moving):
        """Update morse input based on gaze detection results"""
        now_ms = time.time() * 1000
        
        # If head is moving, just pause processing but don't reset everything
        if head_moving:
            # Pause hold timers but keep morse sequence
            self.hold_start_time = None
            self.hold_direction = None
            self.hold_executed = False
            self.neutral_hold_start = None
            return None
        
        # Don't process if gaze is not ready
        if not gaze_result.get('baseline_established', False):
            return None
        
        # Process gaze detection and hold timing
        self._update_gaze_state(gaze_result, now_ms)
        
        # Check for neutral holds to complete letters or submit text (separate from UP/DOWN holds)
        current_physical_state = gaze_result.get('direction')
        result = None
        if current_physical_state is None:  # In neutral position
            result = self._check_neutral_hold(now_ms)
        else:
            # Reset neutral hold timing if not neutral
            self.neutral_hold_start = None
            self.letter_completed = False
        
        # Update cursor blinking
        self._update_cursor_blink(now_ms)
        
        return result
    
    def _update_gaze_state(self, gaze_result, now_ms):
        """Process gaze detection events and hold timing"""
        current_physical_state = gaze_result.get('direction')  # This tracks physical position
        
        # Handle hold timing
        if current_physical_state != self.hold_direction:
            # Direction changed, start new hold timing
            if current_physical_state:
                self.hold_start_time = now_ms
                self.hold_direction = current_physical_state
                self.hold_executed = False
                self.pending_hold_symbol = None  # Reset pending symbol
            else:
                # Went to neutral, reset hold timing
                self.hold_start_time = None
                self.hold_direction = None
                self.hold_executed = False
                self.pending_hold_symbol = None
        
        # Process gaze detection events (add symbols immediately)
        if gaze_result.get('gaze_detected', False):
            direction = gaze_result.get('direction')
            if direction:
                self._process_gaze_change(direction, now_ms)
                # Track this symbol as potentially needing removal if it becomes a hold
                if direction == "UP":
                    self.pending_hold_symbol = "."
                elif direction == "DOWN":
                    self.pending_hold_symbol = "-"
        
        # Check for completed holds
        if self.hold_start_time and not self.hold_executed:
            hold_duration = now_ms - self.hold_start_time
            
            if (self.hold_direction == "UP" and hold_duration >= self.config['up_hold_time']):
                # Remove the dot that was added when we first detected the UP gaze
                if self.pending_hold_symbol == "." and self.current_morse.endswith("."):
                    self.current_morse = self.current_morse[:-1]
                    print("Removed DOT (converted to SPACE hold)")
                self._add_space()
                self.hold_executed = True
                self.pending_hold_symbol = None
                print("SPACE added (1-second UP hold)")
                
            elif (self.hold_direction == "DOWN" and hold_duration >= self.config['down_hold_time']):
                # Remove the dash that was added when we first detected the DOWN gaze
                if self.pending_hold_symbol == "-" and self.current_morse.endswith("-"):
                    self.current_morse = self.current_morse[:-1]
                    print("Removed DASH (converted to CLEAR/BACKSPACE hold)")
                
                # Check if we have a current morse sequence to clear
                if self.current_morse:
                    # Clear the current morse sequence
                    self.current_morse = ""
                    print("MORSE CLEARED (1-second DOWN hold)")
                else:
                    # No morse sequence, delete the last letter
                    self._backspace()
                    print("BACKSPACE executed (1-second DOWN hold)")
                
                self.hold_executed = True
                self.pending_hold_symbol = None
    
    def _process_gaze_change(self, new_direction, now_ms):
        """Process when gaze direction changes - add ONE symbol per direction change"""
        # Add morse symbol when we ENTER a new UP or DOWN gaze
        if new_direction == "UP":
            self.current_morse += "."
            print(f"DOT - morse: '{self.current_morse}'")
        elif new_direction == "DOWN":
            self.current_morse += "-"
            print(f"DASH - morse: '{self.current_morse}'")
    
    def _check_neutral_hold(self, now_ms):
        """Check for neutral hold to complete letter (1s) or submit text (3s)"""
        if not self.neutral_hold_start:
            # Start neutral hold timing
            self.neutral_hold_start = now_ms
            self.letter_completed = False
            if self.current_morse:
                print(f"Starting NEUTRAL hold with morse: '{self.current_morse}'")
            else:
                print("Starting NEUTRAL hold (no current morse)")
            return
        
        hold_duration = now_ms - self.neutral_hold_start
        
        # Debug: Show neutral hold progress occasionally  
        if hold_duration % 250 < 50:  # Every 250ms
            if hold_duration < self.config['neutral_hold_time']:
                # Show progress toward 1-second letter completion
                progress = (hold_duration / self.config['neutral_hold_time']) * 100
                print(f"NEUTRAL hold progress (letter): {progress:.0f}% ({hold_duration:.0f}ms/{self.config['neutral_hold_time']}ms)")
            elif hold_duration < 3000:  # 3 seconds for submission
                # Show progress toward 3-second submission
                progress = ((hold_duration - self.config['neutral_hold_time']) / (3000 - self.config['neutral_hold_time'])) * 100
                print(f"NEUTRAL hold progress (SUBMIT): {progress:.0f}% ({hold_duration:.0f}ms/3000ms)")
        
        # Complete letter after 1 second neutral hold (only if there's morse to complete)
        if (hold_duration >= self.config['neutral_hold_time'] and 
            not self.letter_completed and self.current_morse):
            self._complete_current_morse()
            self.letter_completed = True
            print("LETTER COMPLETED (1-second NEUTRAL hold)")
        
        # Submit text and hit enter after 3 seconds neutral hold
        if hold_duration >= 3000:  # 3 seconds
            submitted_text = self._submit_text_and_enter()
            self.neutral_hold_start = None
            self.letter_completed = False
            print("TEXT SUBMITTED (3-second NEUTRAL hold)")
            return {
                'text_submitted': True,
                'submitted_text': submitted_text
            }
    

    
    def _check_hold_actions(self, current_direction, now_ms):
        """Check for 2-second hold actions"""
        if not self.hold_start_time or self.hold_executed:
            return
        
        # Check if we're still in the same direction/state
        is_same_state = (
            (self.hold_direction == "UP" and current_direction == "UP") or
            (self.hold_direction == "DOWN" and current_direction == "DOWN") or
            (self.hold_direction == "NEUTRAL" and current_direction is None)
        )
        
        if not is_same_state:
            # Debug: Show when hold is broken
            if self.hold_direction == "NEUTRAL":
                hold_duration = now_ms - self.hold_start_time
                print(f"NEUTRAL hold broken after {hold_duration:.0f}ms (needed {self.config['neutral_hold_time']}ms)")
            self.hold_start_time = None
            self.hold_direction = None
            return
        
        hold_duration = now_ms - self.hold_start_time
        
        # Debug: Show neutral hold progress
        if self.hold_direction == "NEUTRAL" and hold_duration % 500 < 100:  # Every 500ms
            progress = (hold_duration / self.config['neutral_hold_time']) * 100
            print(f"NEUTRAL hold progress: {progress:.0f}% ({hold_duration:.0f}ms/{self.config['neutral_hold_time']}ms)")
        
        # Execute hold actions
        if self.hold_direction == "UP" and hold_duration >= self.config['up_hold_time']:
            self._add_space()
            self.hold_executed = True
            print("SPACE added (2-second UP hold)")
            
        elif self.hold_direction == "DOWN" and hold_duration >= self.config['down_hold_time']:
            self._backspace()
            self.hold_executed = True
            print("BACKSPACE executed (2-second DOWN hold)")
            
        elif self.hold_direction == "NEUTRAL" and hold_duration >= self.config['neutral_hold_time']:
            if self.current_morse:
                # Complete the current morse sequence into a letter
                self._complete_current_morse()
            else:
                # No morse sequence, treat as word separator
                self._new_word()
            self.hold_executed = True
            print("LETTER COMPLETED (2-second NEUTRAL hold)")
    
    def _add_space(self):
        """Add space to text"""
        # First complete any pending morse
        self._complete_current_morse()
        # Add space if not already at end
        if self.current_text and not self.current_text.endswith(" "):
            self.current_text += " "
        
        # Type space key if typing is enabled
        if self.enable_typing and self.keyboard:
            try:
                self.keyboard.press(Key.space)
                self.keyboard.release(Key.space)
                print("TYPED: SPACE key")
            except Exception as e:
                print(f"Error typing space: {e}")
    
    def _backspace(self):
        """Remove last character"""
        if self.current_morse:
            # Remove from current morse sequence
            self.current_morse = self.current_morse[:-1]
        elif self.current_text:
            # Remove from main text
            self.current_text = self.current_text[:-1]
        
        # Type backspace key if typing is enabled
        if self.enable_typing and self.keyboard:
            try:
                self.keyboard.press(Key.backspace)
                self.keyboard.release(Key.backspace)
                print("TYPED: BACKSPACE key")
            except Exception as e:
                print(f"Error typing backspace: {e}")
    
    def _new_word(self):
        """Complete current morse and start new word"""
        self._complete_current_morse()
        # Add space if needed
        if self.current_text and not self.current_text.endswith(" "):
            self.current_text += " "
    
    def _complete_current_morse(self):
        """Convert current morse sequence to letter and add to text"""
        if self.current_morse:
            # Look up morse code in dictionary (morse -> letter)
            letter = self.morse_dict.get(self.current_morse)
            
            if letter:
                # Add to internal text for display
                self.current_text += letter
                
                # Type the letter if typing is enabled
                if self.enable_typing and self.keyboard:
                    try:
                        self.keyboard.type(letter)
                        print(f"TYPED: '{self.current_morse}' -> '{letter}'")
                    except Exception as e:
                        print(f"Error typing letter '{letter}': {e}")
                else:
                    print(f"LETTER: '{self.current_morse}' -> '{letter}' (display only)")
            else:
                # Check for morse commands if no letter found
                command = self.morse_commands.get(self.current_morse)
                if command:
                    self._execute_morse_command(command)
                else:
                    print(f"UNKNOWN MORSE: '{self.current_morse}'")
            
            self.current_morse = ""
    
    def _execute_morse_command(self, command):
        """Execute a morse command"""
        if command == "CLEAR_ALL":
            print(f"🗑️ CLEAR ALL COMMAND - 6 dots detected!")
            self._clear_all()
        else:
            print(f"UNKNOWN COMMAND: '{command}'")
    
    def _clear_all(self):
        """Clear all text (Ctrl+A then Backspace)"""
        # Clear internal state
        self.current_morse = ""
        self.current_text = ""
        
        # Type Ctrl+A then Backspace if typing is enabled
        if self.enable_typing and self.keyboard:
            try:
                # Select all (Ctrl+A)
                self.keyboard.press(Key.ctrl)
                self.keyboard.press('a')
                self.keyboard.release('a')
                self.keyboard.release(Key.ctrl)
                
                # Small delay between commands
                import time
                time.sleep(0.05)
                
                # Delete selected text (Backspace)
                self.keyboard.press(Key.backspace)
                self.keyboard.release(Key.backspace)
                
                print("TYPED: CTRL+A then BACKSPACE (clear all)")
            except Exception as e:
                print(f"Error typing clear all: {e}")
        else:
            print("CLEAR ALL (internal only - typing disabled)")
    
    def _submit_text_and_enter(self):
        """Submit the current text and hit enter"""
        # First complete any pending morse
        if self.current_morse:
            self._complete_current_morse()
        
        # Store the text before clearing it
        submitted_text = self.current_text
        
        # Hit enter to submit the text
        # if self.enable_typing and self.keyboard:
        #     try:
        #         self.keyboard.press(Key.enter)
        #         self.keyboard.release(Key.enter)
        #         print(f"SUBMITTED TEXT: '{submitted_text}' + ENTER")
        #     except Exception as e:
        #         print(f"Error sending enter: {e}")
        # else:
        #     print(f"SUBMIT (display only): '{submitted_text}' + ENTER")
        
        # Clear the text after submission
        self.current_text = ""
        self.current_word = ""  # Also clear current word
        
        # Call the callback if provided
        if self.on_text_submitted:
            try:
                self.on_text_submitted(submitted_text)
            except Exception as e:
                print(f"Error in text submission callback: {e}")
        
        return submitted_text
    
    def _update_cursor_blink(self, now_ms):
        """Update cursor blinking"""
        if now_ms - self.last_cursor_blink > self.config['cursor_blink_rate']:
            self.cursor_visible = not self.cursor_visible
            self.last_cursor_blink = now_ms
    
    def _reset_timing(self):
        """Reset timing when head moves or system is disabled"""
        self.gaze_start_time = None
        self.hold_start_time = None
        self.hold_direction = None
        self.hold_executed = False
    
    def get_display_text(self):
        """Get text to display with cursor"""
        display_text = self.current_text
        
        # Add current morse sequence in progress
        if self.current_morse:
            display_text += f"[{self.current_morse}]"
        
        # Add blinking cursor
        if self.cursor_visible:
            display_text += "_"
        else:
            display_text += " "  # Space to maintain text position
        
        return display_text
    
    def get_morse_status(self):
        """Get current morse input status"""
        status = []
        
        if self.current_morse:
            status.append(f"Morse: {self.current_morse}")
        
        # Show current word if any
        if self.current_word:
            status.append(f"Word: {self.current_word}")
        
        # Show current text if any
        if self.current_text:
            status.append(f"Text: {self.current_text}")
        
        return " | ".join(status) if status else "Ready"
