import cv2
import numpy as np
from config import DISPLAY_CONFIG

def draw_infinite_line(img, center, direction, color, thickness=None):
    """Draw an infinite line through a center point in a given direction"""
    thickness = thickness or DISPLAY_CONFIG['line_thickness']
    h, w = img.shape[:2]
    px, py = float(center[0]), float(center[1])
    vx, vy = float(direction[0]), float(direction[1])
    pts = []
    eps = 1e-6
    
    # Intersect with x = 0 and x = w-1
    if abs(vx) > eps:
        for X in (0, w - 1):
            t = (X - px) / vx
            y = py + t * vy
            if 0 <= y <= h - 1:
                pts.append((X, int(round(y))))
    
    # Intersect with y = 0 and y = h-1
    if abs(vy) > eps:
        for Y in (0, h - 1):
            t = (Y - py) / vy
            x = px + t * vx
            if 0 <= x <= w - 1:
                pts.append((int(round(x)), Y))
    
    pts = list(dict.fromkeys(pts))
    if len(pts) >= 2:
        # Choose the pair with max distance
        max_d, p1, p2 = -1, pts[0], pts[1]
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                d = (pts[i][0] - pts[j][0]) ** 2 + (pts[i][1] - pts[j][1]) ** 2
                if d > max_d:
                    max_d, p1, p2 = d, pts[i], pts[j]
        cv2.line(img, p1, p2, color, thickness, cv2.LINE_AA)

def draw_pupil_visualization(frame, p_left, p_right):
    """Draw pupil visualization with crosshairs"""
    # Draw pupil centers
    cv2.circle(frame, p_left, 3, (0, 255, 0), -1)
    cv2.circle(frame, p_right, 3, (0, 255, 0), -1)
    
    # Draw connecting line
    cv2.line(frame, p_left, p_right, (0, 255, 255), 2, cv2.LINE_AA)
    
    # Draw crosshairs
    cross = DISPLAY_CONFIG['cross_size']
    for (px, py) in (p_left, p_right):
        cv2.line(frame, (px - cross, py), (px + cross, py), (255, 0, 0), 2, cv2.LINE_AA)
        cv2.line(frame, (px, py - cross), (px, py + cross), (255, 0, 0), 2, cv2.LINE_AA)

def draw_landmark_circles(frame, landmarks, w, h):
    """Draw colored circles on key landmarks for verification"""
    # Forehead (yellow)
    cv2.circle(frame, (int(landmarks[10].x * w), int(landmarks[10].y * h)), 
               8, (0, 255, 255), -1)
    # Chin (magenta)
    cv2.circle(frame, (int(landmarks[152].x * w), int(landmarks[152].y * h)), 
               8, (255, 0, 255), -1)

def draw_gaze_status(frame, gaze_result, head_moving, is_blinking=False, position=(12, 300)):
    """Draw the main gaze status display with blink awareness"""
    x, y = position
    
    if head_moving:
        # Head is moving - show disabled status
        gaze_color = (255, 0, 0)  # Red
        gaze_text = "GAZE DISABLED - HEAD MOVING"
    elif is_blinking:
        # Blinking - show disabled status
        gaze_color = (255, 0, 0)  # Red
        gaze_text = "GAZE DISABLED - BLINKING"
    elif gaze_result.get('disabled_reason'):
        # Other disabled reason
        gaze_color = (255, 0, 0)  # Red
        gaze_text = f"GAZE DISABLED - {gaze_result['disabled_reason']}"
    elif gaze_result['gaze_detected']:
        # Gaze detected
        if gaze_result['direction'] == "UP":
            gaze_color = (0, 255, 0)  # Green
            gaze_text = "LOOKING UP"
        else:  # DOWN
            gaze_color = (0, 0, 255)  # Red
            gaze_text = "LOOKING DOWN"
    else:
        # Neutral
        gaze_color = (128, 128, 128)  # Gray
        gaze_text = "NEUTRAL"
    
    # Draw large, easy-to-see gaze status
    cv2.putText(frame, gaze_text, (x, y), 
               cv2.FONT_HERSHEY_SIMPLEX, DISPLAY_CONFIG['font_scale_large'], 
               gaze_color, 3, cv2.LINE_AA)

def draw_gaze_progress_bars(frame, gaze_result, position=(12, 320)):
    """Draw progress bars showing gaze level for each direction"""
    if not gaze_result.get('baseline_established', False):
        return
    
    bar_x, bar_y = position
    bar_w, bar_h = 200, 20
    
    # Get thresholds from config
    from config import GAZE_CONFIG
    threshold_up = GAZE_CONFIG['threshold_up']
    threshold_down = GAZE_CONFIG['threshold_down']
    
    offset = gaze_result.get('offset', 0)
    
    # Up gaze bar (green)
    up_fill = min(max(offset / threshold_up, 0.0), 1.0)
    up_fill_w = int(bar_w * up_fill)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (64, 64, 64), -1)
    if up_fill > 0:
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + up_fill_w, bar_y + bar_h), (0, 255, 0), -1)
    
    # Down gaze bar (red) - below the up bar
    bar_y2 = bar_y + bar_h + 10
    down_fill = min(max(-offset / threshold_down, 0.0), 1.0)
    down_fill_w = int(bar_w * down_fill)
    cv2.rectangle(frame, (bar_x, bar_y2), (bar_x + bar_w, bar_y2 + bar_h), (64, 64, 64), -1)
    if down_fill > 0:
        cv2.rectangle(frame, (bar_x, bar_y2), (bar_x + down_fill_w, bar_y2 + bar_h), (0, 0, 255), -1)
    
    # Bar labels
    cv2.putText(frame, f"Up: {up_fill:.1%}", (bar_x, bar_y + bar_h + 20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(frame, f"Down: {down_fill:.1%}", (bar_x, bar_y2 + bar_h + 20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)

def draw_debug_info(frame, gaze_result, face_metrics, position=(12, 120)):
    """Draw debug information on the left side of the frame"""
    x, y = position
    
    # Face metrics
    cv2.putText(frame, f"Forehead Y: {face_metrics['forehead_y']:.1f}", 
               (x, y), cv2.FONT_HERSHEY_SIMPLEX, DISPLAY_CONFIG['font_scale_small'], 
               (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, f"Chin Y: {face_metrics['chin_y']:.1f}", 
               (x, y + 20), cv2.FONT_HERSHEY_SIMPLEX, DISPLAY_CONFIG['font_scale_small'], 
               (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, f"Pupil Y: {face_metrics['pupil_y']:.1f}", 
               (x, y + 40), cv2.FONT_HERSHEY_SIMPLEX, DISPLAY_CONFIG['font_scale_small'], 
               (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, f"Face Height: {face_metrics['face_height']:.1f}", 
               (x, y + 60), cv2.FONT_HERSHEY_SIMPLEX, DISPLAY_CONFIG['font_scale_small'], 
               (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, f"Pupil Relative: {face_metrics['pupil_relative']:.3f}", 
               (x, y + 80), cv2.FONT_HERSHEY_SIMPLEX, DISPLAY_CONFIG['font_scale_small'], 
               (255, 255, 255), 1, cv2.LINE_AA)
    
    # Blink status
    blink_text = "BLINKING" if face_metrics.get('is_blinking', False) else "Eyes Open"
    blink_color = (0, 0, 255) if face_metrics.get('is_blinking', False) else (0, 255, 0)
    cv2.putText(frame, f"Blink: {blink_text}", 
               (x, y + 100), cv2.FONT_HERSHEY_SIMPLEX, DISPLAY_CONFIG['font_scale_small'], 
               blink_color, 1, cv2.LINE_AA)
    
    # Gaze metrics
    if gaze_result.get('baseline_established', False):
        cv2.putText(frame, f"Baseline: {face_metrics.get('baseline_y', 0):.3f}", 
                   (x, y + 140), cv2.FONT_HERSHEY_SIMPLEX, DISPLAY_CONFIG['font_scale_small'], 
                   (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"Offset: {gaze_result.get('offset', 0):.3f}", 
                   (x, y + 160), cv2.FONT_HERSHEY_SIMPLEX, DISPLAY_CONFIG['font_scale_small'], 
                   (255, 255, 255), 1, cv2.LINE_AA)
        
        # Show thresholds
        from config import GAZE_CONFIG
        cv2.putText(frame, f"Up Threshold: {GAZE_CONFIG['threshold_up']:.3f}", 
                   (x, y + 180), cv2.FONT_HERSHEY_SIMPLEX, DISPLAY_CONFIG['font_scale_small'], 
                   (0, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(frame, f"Down Threshold: {GAZE_CONFIG['threshold_down']:.3f}", 
                   (x, y + 200), cv2.FONT_HERSHEY_SIMPLEX, DISPLAY_CONFIG['font_scale_small'], 
                   (0, 0, 255), 1, cv2.LINE_AA)

def draw_gaze_arrow(frame, gaze_result, position, w, h):
    """Draw gaze arrow in the top-right corner"""
    arrow_x, arrow_y = position
    
    if gaze_result.get('baseline_established', False) and not gaze_result['gaze_detected']:
        # Show baseline status
        if gaze_result['direction']:
            # Show last detected gaze
            from config import GAZE_CONFIG
            arrow_color = GAZE_CONFIG['arrow_colors'][gaze_result['color_index']]
            
            if gaze_result['direction'] == "UP":
                # Up arrow
                cv2.arrowedLine(frame, (arrow_x, arrow_y + 20), (arrow_x, arrow_y), 
                              arrow_color, DISPLAY_CONFIG['arrow_thickness'], tipLength=0.3)
            else:  # DOWN
                # Down arrow
                cv2.arrowedLine(frame, (arrow_x, arrow_y), (arrow_x, arrow_y + 20), 
                              arrow_color, DISPLAY_CONFIG['arrow_thickness'], tipLength=0.3)
            
            # Show gaze direction text
            cv2.putText(frame, f"GAZE: {gaze_result['direction']}", 
                       (w - 120, arrow_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                       arrow_color, 2, cv2.LINE_AA)
        else:
            # Show neutral status
            cv2.putText(frame, "GAZE: NEUTRAL", (w - 120, arrow_y + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (128, 128, 128), 2, cv2.LINE_AA)
        
        # Show current gaze metrics
        cv2.putText(frame, f"Pupil Relative: {gaze_result.get('pupil_relative', 0):.3f}", 
                   (w - 200, arrow_y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                   (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"Baseline: {gaze_result.get('baseline_y', 0):.3f}", 
                   (w - 200, arrow_y + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                   (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"Face Height: {gaze_result.get('face_height', 0):.1f}px", 
                   (w - 200, arrow_y + 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                   (255, 255, 255), 1, cv2.LINE_AA)

def draw_morse_display(frame, morse_handler, position=(50, 50)):
    """Draw Morse code input text and status"""
    from config import MORSE_CONFIG
    
    x, y = position
    
    # Draw main text with cursor
    display_text = morse_handler.get_display_text()
    cv2.putText(frame, display_text, (x, y), 
               cv2.FONT_HERSHEY_SIMPLEX, MORSE_CONFIG['text_font_scale'], 
               MORSE_CONFIG['text_color'], 2, cv2.LINE_AA)
    
    # Draw morse status
    status_lines = morse_handler.get_morse_status()
    for i, status in enumerate(status_lines):
        cv2.putText(frame, status, (x, y + 40 + i * 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                   (200, 200, 200), 1, cv2.LINE_AA)
    
    # Draw instructions
    instructions = [
        "UP gaze: DOT | DOWN gaze: DASH", 
        "NEUTRAL 1s: complete letter | UP 1s: space",
        "DOWN 1s: clear morse OR backspace letter"
    ]
    
    h, w = frame.shape[:2]
    for i, instruction in enumerate(instructions):
        cv2.putText(frame, instruction, (x, h - 60 + i * 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                   (150, 150, 150), 1, cv2.LINE_AA)

def draw_velocity_debug(frame, velocity, threshold, is_reading_movement):
    """Show velocity information for debugging reading detection"""
    h, w = frame.shape[:2]
    
    # Position velocity display in top-left corner
    base_x, base_y = 10, 200
    
    # Velocity bar (0 to 2x threshold for good scale)
    max_display = threshold * 2
    bar_width = int(min(velocity / max_display, 1.0) * 200)
    
    # Color: Red if reading movement, Green if intentional
    bar_color = (0, 0, 255) if is_reading_movement else (0, 255, 0)
    
    # Draw velocity bar background
    cv2.rectangle(frame, (base_x, base_y), (base_x + 200, base_y + 20), (40, 40, 40), -1)
    
    # Draw velocity bar
    if bar_width > 0:
        cv2.rectangle(frame, (base_x, base_y), (base_x + bar_width, base_y + 20), bar_color, -1)
    
    # Draw border
    cv2.rectangle(frame, (base_x, base_y), (base_x + 200, base_y + 20), (255, 255, 255), 1)
    
    # Draw threshold line
    threshold_x = base_x + int((threshold / max_display) * 200)
    cv2.line(frame, (threshold_x, base_y), (threshold_x, base_y + 20), (255, 255, 0), 2)
    
    # Text labels
    velocity_text = f"Velocity: {velocity:.3f}"
    status_text = "READING" if is_reading_movement else "INTENTIONAL"
    threshold_text = f"Threshold: {threshold:.3f}"
    
    cv2.putText(frame, velocity_text, (base_x, base_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, status_text, (base_x, base_y + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, bar_color, 2)
    cv2.putText(frame, threshold_text, (base_x, base_y + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)