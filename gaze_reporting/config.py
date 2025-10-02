# Configuration file for pupil_lines.py system

# Head Motion Detection Configuration
HEAD_MOTION_CONFIG = {
    'ema_alpha': 0.4,                  # smoothing factor
    'on_ms': 150,                      # activation time (wait for sustained movement) - increased
    'off_ms': 400,                     # deactivation time (ensure movement stopped) - increased
    'tx_on': 0.20,                     # horizontal movement threshold (less sensitive)
    'tx_off': 0.12,                    # horizontal movement off threshold
    'ty_on': 0.16,                     # vertical movement threshold (less sensitive)
    'ty_off': 0.10,                    # vertical movement off threshold
    'ang_on_deg': 10.0,                # roll angle threshold (less sensitive)
    'ang_off_deg': 6.0,                # roll angle off threshold
    'scale_on': 0.10,                  # scale change threshold (less sensitive)
    'scale_off': 0.06,                 # scale change off threshold
    'auto_rebase': True,               # enable auto-rebase
    'rebase_hold_ms': 1000,            # wait 1 second before rebase
    'gaze_neutral_enable': True,       # enable gaze-neutral assist
    'gaze_neutral_window': 0.03,       # gaze neutral window
    'gaze_hold_ms': 800                # gaze hold time
}

# Gaze Detection Configuration
GAZE_CONFIG = {
    'threshold_up': 0.012,             # up gaze threshold (1.2% of face height)
    'threshold_down': 0.005,           # down gaze threshold (0.6% of face height) - more sensitive  
    'baseline_frames': 15,             # frames to establish baseline
    'cooldown_ms': 200,                # cooldown between detections
    'long_gaze_threshold_ms': 1250,     # duration threshold for long gaze (milliseconds)
    'continuous_action_rate_ms': 100,  # rate limit for continuous actions (milliseconds)
    'arrow_colors': [
        (0, 255, 255),   # cyan
        (255, 0, 255),   # magenta
        (255, 255, 0),   # yellow
        (0, 255, 0),     # green
        (255, 0, 0),     # blue
        (0, 0, 255),     # red
        (128, 255, 128), # light green
        (255, 128, 128), # light blue
        (128, 128, 255), # light red
    ]
}

# Calibration Popup Configuration
CALIBRATION_CONFIG = {
    'window_width': 800,           # Calibration window width
    'window_height': 500,          # Calibration window height
    'position_mode': 'center',     # 'center', 'custom', or 'auto'
    'custom_x': 400,              # Custom X position (when position_mode = 'custom')
    'custom_y': 300,              # Custom Y position (when position_mode = 'custom')
    'fallback_x': 400,            # Fallback X position if auto-detection fails
    'fallback_y': 400,            # Fallback Y position if auto-detection fails
    'red_dot_position': 'upper_third',  # 'center', 'upper_third', 'custom'
    'red_dot_custom_y': 200,      # Custom Y position for red dot (when red_dot_position = 'custom')
    'red_dot_size': 20,           # Radius of the red dot
    'red_dot_border_width': 2,    # White border width around red dot
}

# Blink Detection Configuration
BLINK_CONFIG = {
    'ear_threshold': 0.25,             # Eye Aspect Ratio threshold for blink detection
    'consecutive_frames': 2,           # Consecutive frames below threshold to confirm blink
    'min_blink_duration_ms': 50,       # Minimum blink duration to filter noise
    'max_blink_duration_ms': 500       # Maximum blink duration before considering it a deliberate close
}

# MediaPipe Landmark Indices
LANDMARK_INDICES = {
    'LEFT_IRIS': list(range(468, 473)),
    'RIGHT_IRIS': list(range(473, 478)),
    'L_EYE_CORNER': 33,
    'R_EYE_CORNER': 263,
    'FOREHEAD': 10,
    'CHIN': 152
}

# Eye landmark indices for blink detection
EYE_LANDMARKS = {
    'LEFT_EYE': [362, 385, 387, 263, 373, 380],   # 6-point left eye contour
    'RIGHT_EYE': [33, 160, 158, 133, 153, 144]    # 6-point right eye contour
}

# Display Configuration
DISPLAY_CONFIG = {
    'cross_size': 15,                  # pupil crosshair size
    'arrow_size': 10,                  # status arrow size
    'font_scale_large': 1.2,           # large text scale
    'font_scale_medium': 0.8,          # medium text scale
    'font_scale_small': 0.5,           # small text scale
    'line_thickness': 2,               # default line thickness
    'arrow_thickness': 3               # arrow thickness
}

# Morse Code Input Configuration
MORSE_CONFIG = {
    'up_hold_time': 1000,              # 1 second for space
    'neutral_hold_time': 1000,         # 1 second for letter completion
    'down_hold_time': 1000,            # 1 second for backspace
    'neutral_timeout': 3000,           # 3 seconds neutral timeout to exit text mode
    'dot_time': 50,                    # 50ms minimum for any gaze input
    'dash_time': 50,                   # 50ms minimum for any gaze input
    'cursor_blink_rate': 500,          # cursor blink every 500ms
    'text_position': (50, 50),         # text display position
    'text_font_scale': 1.0,            # text size
    'text_color': (255, 255, 255),     # white text
    'cursor_color': (0, 255, 0),       # green cursor
}

# App-specific mode configuration
APP_MODE_CONFIG = {
    # Default mode for unknown apps
    'default_mode': 'TAB',
    
    # Specific app configurations
    'apps': {
        'Start': 'SCROLL', # Start menu - use SCROLL mode
    }
}

# Continuous gaze firing configuration
CONTINUOUS_GAZE_CONFIG = {
    'hold_threshold_ms': 1000,    # Hold gaze for 1 second before continuous firing starts
    'repeat_rate_ms': 250,        # Repeat key every 500ms while held
}