# appbar.py
# A Windows AppBar (top-docked) in pure Python via ctypes.
# It reserves space at the top so other windows maximize below it.
# Displays real-time gaze detection status via file-based communication.

import ctypes
from ctypes import wintypes
import threading
import time
import signal
import sys
import atexit
import json
import os
import tempfile

user32   = ctypes.windll.user32
gdi32    = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32
shell32  = ctypes.windll.shell32

# ----------------------------
# Basic typedef fixes (older Python/ctypes may lack these)
# ----------------------------
if not hasattr(wintypes, "LRESULT"):
    # LRESULT is LONG_PTR (pointer-sized signed)
    LRESULT = ctypes.c_longlong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long
else:
    LRESULT = wintypes.LRESULT

if not hasattr(wintypes, "HCURSOR"):
    # HCURSOR is a handle (pointer)
    HCURSOR = wintypes.HANDLE
else:
    HCURSOR = wintypes.HCURSOR

if not hasattr(wintypes, "HBRUSH"):
    # HBRUSH is a handle (pointer)
    HBRUSH = wintypes.HANDLE
else:
    HBRUSH = wintypes.HBRUSH

# Window procedure prototype
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)

# ----------------------------
# Constants
# ----------------------------
WS_POPUP       = 0x80000000
WS_VISIBLE     = 0x10000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_TOPMOST    = 0x00000008

WM_CREATE         = 0x0001
WM_DESTROY        = 0x0002
WM_PAINT          = 0x000F
WM_DISPLAYCHANGE  = 0x007E
WM_SETTINGCHANGE  = 0x001A
WM_DPICHANGED     = 0x02E0

ABM_NEW        = 0x00000000
ABM_REMOVE     = 0x00000001
ABM_QUERYPOS   = 0x00000002
ABM_SETPOS     = 0x00000003

ABE_TOP   = 1

ABN_POSCHANGED     = 0x0000001
ABN_FULLSCREENAPP  = 0x0000002

CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001

COLOR_WINDOW = 5
IDC_ARROW = 32512

SWP_NOSIZE      = 0x0001
SWP_NOMOVE      = 0x0002
SWP_NOZORDER    = 0x0004
SWP_NOACTIVATE  = 0x0010
SWP_SHOWWINDOW  = 0x0040

SM_CXSCREEN = 0

DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)  # Win10+

# Text drawing constants
DT_CENTER = 0x00000001
DT_VCENTER = 0x00000004
DT_SINGLELINE = 0x00000020
TRANSPARENT = 1

# ----------------------------
# Structs
# ----------------------------
class APPBARDATA(ctypes.Structure):
    _fields_ = [
        ('cbSize',            wintypes.DWORD),
        ('hWnd',              wintypes.HWND),
        ('uCallbackMessage',  wintypes.UINT),
        ('uEdge',             wintypes.UINT),
        ('rc',                wintypes.RECT),
        ('lParam',            ctypes.c_int),
    ]

class WNDCLASSEX(ctypes.Structure):
    _fields_ = [
        ('cbSize',        wintypes.UINT),
        ('style',         wintypes.UINT),
        ('lpfnWndProc',   WNDPROC),
        ('cbClsExtra',    ctypes.c_int),
        ('cbWndExtra',    ctypes.c_int),
        ('hInstance',     wintypes.HINSTANCE),
        ('hIcon',         wintypes.HICON),
        ('hCursor',       HCURSOR),
        ('hbrBackground', HBRUSH),
        ('lpszMenuName',  wintypes.LPCWSTR),
        ('lpszClassName', wintypes.LPCWSTR),
        ('hIconSm',       wintypes.HICON),
    ]

class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [
        ('hdc',         wintypes.HDC),
        ('fErase',      wintypes.BOOL),
        ('rcPaint',     wintypes.RECT),
        ('fRestore',    wintypes.BOOL),
        ('fIncUpdate',  wintypes.BOOL),
        ('rgbReserved', ctypes.c_byte * 32),
    ]

class MSG(ctypes.Structure):
    _fields_ = [
        ('hwnd',      wintypes.HWND),
        ('message',   wintypes.UINT),
        ('wParam',    wintypes.WPARAM),
        ('lParam',    wintypes.LPARAM),
        ('time',      wintypes.DWORD),
        ('pt',        wintypes.POINT),
        ('lPrivate',  wintypes.DWORD),
    ]

# ----------------------------
# API prototypes
# ----------------------------
RegisterWindowMessage = user32.RegisterWindowMessageW
RegisterWindowMessage.argtypes = [wintypes.LPCWSTR]
RegisterWindowMessage.restype  = wintypes.UINT

SHAppBarMessage = shell32.SHAppBarMessage
SHAppBarMessage.argtypes = [wintypes.DWORD, ctypes.POINTER(APPBARDATA)]
SHAppBarMessage.restype  = ctypes.c_ulong

GetSystemMetrics = user32.GetSystemMetrics
GetSystemMetrics.argtypes = [ctypes.c_int]
GetSystemMetrics.restype  = ctypes.c_int

BeginPaint = user32.BeginPaint
BeginPaint.argtypes = [wintypes.HWND, ctypes.POINTER(PAINTSTRUCT)]
BeginPaint.restype  = wintypes.HDC

EndPaint = user32.EndPaint
EndPaint.argtypes = [wintypes.HWND, ctypes.POINTER(PAINTSTRUCT)]
EndPaint.restype  = wintypes.BOOL

GetClientRect = user32.GetClientRect
GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
GetClientRect.restype  = wintypes.BOOL

FillRect = user32.FillRect
FillRect.argtypes = [wintypes.HDC, ctypes.POINTER(wintypes.RECT), HBRUSH]
FillRect.restype  = ctypes.c_int

GetSysColorBrush = user32.GetSysColorBrush
GetSysColorBrush.argtypes = [ctypes.c_int]
GetSysColorBrush.restype  = HBRUSH

DrawText = user32.DrawTextW
DrawText.argtypes = [wintypes.HDC, wintypes.LPCWSTR, ctypes.c_int, ctypes.POINTER(wintypes.RECT), wintypes.UINT]
DrawText.restype  = ctypes.c_int

SetTextColor = gdi32.SetTextColor
SetTextColor.argtypes = [wintypes.HDC, wintypes.COLORREF]
SetTextColor.restype  = wintypes.COLORREF

SetBkMode = gdi32.SetBkMode
SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]
SetBkMode.restype  = ctypes.c_int

DefWindowProc = user32.DefWindowProcW
DefWindowProc.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
DefWindowProc.restype  = LRESULT

GetModuleHandle = kernel32.GetModuleHandleW
GetModuleHandle.argtypes = [wintypes.LPCWSTR]
GetModuleHandle.restype  = wintypes.HINSTANCE

LoadCursor = user32.LoadCursorW
LoadCursor.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR]
LoadCursor.restype  = HCURSOR

GetMessage  = user32.GetMessageW
GetMessage.argtypes  = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
GetMessage.restype   = ctypes.c_int

PeekMessage = user32.PeekMessageW
PeekMessage.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT]
PeekMessage.restype  = wintypes.BOOL

TranslateMessage = user32.TranslateMessage
TranslateMessage.argtypes = [ctypes.POINTER(MSG)]

DispatchMessage  = user32.DispatchMessageW
DispatchMessage.argtypes = [ctypes.POINTER(MSG)]
DispatchMessage.restype  = LRESULT

PostQuitMessage = user32.PostQuitMessage
PostQuitMessage.argtypes = [ctypes.c_int]

SetWindowPos = user32.SetWindowPos
SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
SetWindowPos.restype  = wintypes.BOOL

RegisterClassEx = user32.RegisterClassExW
RegisterClassEx.argtypes = [ctypes.POINTER(WNDCLASSEX)]
RegisterClassEx.restype  = wintypes.ATOM

CreateWindowEx = user32.CreateWindowExW
CreateWindowEx.argtypes = [
    wintypes.DWORD,     # dwExStyle
    wintypes.LPCWSTR,   # lpClassName
    wintypes.LPCWSTR,   # lpWindowName
    wintypes.DWORD,     # dwStyle
    ctypes.c_int,       # X
    ctypes.c_int,       # Y
    ctypes.c_int,       # nWidth
    ctypes.c_int,       # nHeight
    wintypes.HWND,      # hWndParent
    wintypes.HMENU,     # hMenu
    wintypes.HINSTANCE, # hInstance
    wintypes.LPVOID     # lpParam
]
CreateWindowEx.restype = wintypes.HWND

# Optional DPI APIs
try:
    SetProcessDpiAwarenessContext = user32.SetProcessDpiAwarenessContext
    SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
    SetProcessDpiAwarenessContext.restype  = wintypes.BOOL
except Exception:
    SetProcessDpiAwarenessContext = None

# ----------------------------
# Global variables
# ----------------------------
gDesiredDipHeight = 60  # AppBar height in DIPs
gAppbarCallbackMsg = 0
exit_requested = False
status_hwnd = None

# Status monitoring
status_file_path = os.path.join(tempfile.gettempdir(), "gazetalk_appbar_status.json")
current_status = {
    "mode": "STARTING",
    "current_sequence": "",
    "counter": 0,
    "timestamp": ""
}
status_lock = threading.Lock()
monitor_thread = None

def monitor_status_file():
    """Monitor status file for changes"""
    global current_status, exit_requested, status_hwnd
    last_mtime = 0
    
    while not exit_requested:
        try:
            if os.path.exists(status_file_path):
                mtime = os.path.getmtime(status_file_path)
                if mtime > last_mtime:
                    last_mtime = mtime
                    
                    with open(status_file_path, 'r') as f:
                        new_status = json.load(f)
                    
                    with status_lock:
                        current_status.update(new_status)
                    
                    # Debug: Print when status updates
                    print(f"📱 AppBar updated: {new_status.get('mode', 'N/A')} | {new_status.get('current_sequence', 'N/A')}")
                    
                    # Trigger repaint
                    if status_hwnd:
                        user32.InvalidateRect(status_hwnd, None, True)
                        
        except Exception as e:
            # Silently ignore file read errors (file might be mid-write)
            pass
        
        time.sleep(0.05)  # Check every 50ms

def cleanup_appbar():
    """Cleanup function to unregister appbar"""
    global status_hwnd, monitor_thread, exit_requested
    
    # Stop monitoring thread
    exit_requested = True
    if monitor_thread and monitor_thread.is_alive():
        monitor_thread.join(timeout=1.0)
    
    if status_hwnd:
        print("Cleaning up appbar...")
        unregister_appbar(status_hwnd)
        status_hwnd = None

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    global exit_requested
    print(f"\nReceived signal {signum}, requesting exit...")
    exit_requested = True
    # Also post quit message to help break the loop faster
    PostQuitMessage(0)

def appbar_setpos_top(hwnd):
    """Registers/updates the AppBar to the top edge with our desired height."""
    abd = APPBARDATA()
    abd.cbSize = ctypes.sizeof(APPBARDATA)
    abd.hWnd = hwnd
    abd.uEdge = ABE_TOP

    screen_w = GetSystemMetrics(SM_CXSCREEN)
    height_px = gDesiredDipHeight  # Simple fixed height

    # Desired rect (system may adjust it during QUERYPOS)
    abd.rc.left = 0
    abd.rc.top = 0
    abd.rc.right = screen_w
    abd.rc.bottom = height_px

    # Let the shell adjust/approve
    SHAppBarMessage(ABM_QUERYPOS, ctypes.byref(abd))
    # Commit position
    SHAppBarMessage(ABM_SETPOS, ctypes.byref(abd))

    # Size/move our window to the final rect
    SetWindowPos(hwnd, None,
                 abd.rc.left, abd.rc.top,
                 abd.rc.right - abd.rc.left,
                 abd.rc.bottom - abd.rc.top,
                 SWP_NOZORDER | SWP_NOACTIVATE | SWP_SHOWWINDOW)

def register_appbar(hwnd):
    """Register this window as an AppBar and set initial position."""
    global gAppbarCallbackMsg
    abd = APPBARDATA()
    abd.cbSize = ctypes.sizeof(APPBARDATA)
    abd.hWnd = hwnd

    # Unique callback message for ABN_* notifications
    gAppbarCallbackMsg = RegisterWindowMessage("PythonAppBarCallback")
    abd.uCallbackMessage = gAppbarCallbackMsg
    SHAppBarMessage(ABM_NEW, ctypes.byref(abd))
    appbar_setpos_top(hwnd)

def unregister_appbar(hwnd):
    abd = APPBARDATA()
    abd.cbSize = ctypes.sizeof(APPBARDATA)
    abd.hWnd = hwnd
    SHAppBarMessage(ABM_REMOVE, ctypes.byref(abd))

# ----------------------------
# Window procedure
# ----------------------------
@WNDPROC
def WndProc(hwnd, msg, wParam, lParam):
    # Handle shell notifications (ABN_*)
    if gAppbarCallbackMsg and msg == gAppbarCallbackMsg:
        notify = wParam
        if notify == ABN_POSCHANGED:
            appbar_setpos_top(hwnd)
        elif notify == ABN_FULLSCREENAPP:
            # lParam != 0 means entering fullscreen.
            appbar_setpos_top(hwnd)
        return 0

    if msg == WM_CREATE:
        global status_hwnd, monitor_thread
        status_hwnd = hwnd
        register_appbar(hwnd)
        
        # Start status monitoring thread
        monitor_thread = threading.Thread(target=monitor_status_file, daemon=True)
        monitor_thread.start()
        
        return 0

    if msg in (WM_DISPLAYCHANGE, WM_SETTINGCHANGE, WM_DPICHANGED):
        appbar_setpos_top(hwnd)
        return 0

    if msg == WM_PAINT:
        ps = PAINTSTRUCT()
        hdc = BeginPaint(hwnd, ctypes.byref(ps))
        
        # Fill background with light gray
        brush = GetSysColorBrush(COLOR_WINDOW)
        rect = wintypes.RECT()
        GetClientRect(hwnd, ctypes.byref(rect))
        FillRect(hdc, ctypes.byref(rect), brush)
        
        # Draw status text in two lines
        with status_lock:
            mode_text = f"MODE: {current_status['mode']}"
            if current_status['mode'] == "PROMPT":
                sequence_text = f"PROMPT: {current_status.get('prompt', '')}"
            else:
                sequence_text = f"SEQUENCE: {current_status['current_sequence']} | COUNT: {current_status['counter']} | {current_status['timestamp']}"
        
        # Set text properties
        SetBkMode(hdc, TRANSPARENT)
        SetTextColor(hdc, 0x000000)  # Black text
        
        # Calculate line heights
        line_height = rect.bottom // 2
        
        # Top line - Mode (left aligned)
        top_rect = wintypes.RECT()
        top_rect.left = rect.left + 10  # 10px padding from left
        top_rect.top = rect.top + 5     # 5px padding from top
        top_rect.right = rect.right
        top_rect.bottom = rect.top + line_height
        DrawText(hdc, mode_text, -1, ctypes.byref(top_rect), DT_SINGLELINE)
        
        # Bottom line - Sequence (left aligned)
        bottom_rect = wintypes.RECT()
        bottom_rect.left = rect.left + 10  # 10px padding from left
        bottom_rect.top = rect.top + line_height
        bottom_rect.right = rect.right
        bottom_rect.bottom = rect.bottom
        DrawText(hdc, sequence_text, -1, ctypes.byref(bottom_rect), DT_SINGLELINE)
        
        EndPaint(hwnd, ctypes.byref(ps))
        return 0

    if msg == WM_DESTROY:
        unregister_appbar(hwnd)
        PostQuitMessage(0)
        return 0

    return DefWindowProc(hwnd, msg, wParam, lParam)

# ----------------------------
# Setup & message loop
# ----------------------------
def make_window():
    # Per-monitor DPI awareness (best results on Win10+)
    if SetProcessDpiAwarenessContext:
        try:
            SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
        except Exception:
            pass

    hInstance = GetModuleHandle(None)
    className = "CleanAppBarClass"

    wcx = WNDCLASSEX()
    wcx.cbSize = ctypes.sizeof(WNDCLASSEX)
    wcx.style = CS_HREDRAW | CS_VREDRAW
    wcx.lpfnWndProc = WndProc
    wcx.cbClsExtra = 0
    wcx.cbWndExtra = 0
    wcx.hInstance = hInstance
    wcx.hIcon = None
    wcx.hCursor = LoadCursor(None, ctypes.c_wchar_p(IDC_ARROW))
    wcx.hbrBackground = GetSysColorBrush(COLOR_WINDOW)
    wcx.lpszMenuName = None
    wcx.lpszClassName = className
    wcx.hIconSm = None

    if not RegisterClassEx(ctypes.byref(wcx)):
        raise ctypes.WinError()

    ex_style = WS_EX_TOOLWINDOW | WS_EX_TOPMOST
    style = WS_POPUP | WS_VISIBLE

    hwnd = CreateWindowEx(
        ex_style,
        className,
        "Clean AppBar",
        style,
        0, 0,                # x, y (real pos set by ABM_SETPOS)
        100, 50,             # w, h placeholder
        None, None, hInstance, None
    )

    if not hwnd:
        raise ctypes.WinError()
    
    return hwnd

def message_loop():
    global exit_requested
    msg = MSG()
    PM_REMOVE = 0x0001
    
    while not exit_requested:
        # Use PeekMessage with timeout instead of blocking GetMessage
        if PeekMessage(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
            if msg.message == 0x0012:  # WM_QUIT
                break
            TranslateMessage(ctypes.byref(msg))
            DispatchMessage(ctypes.byref(msg))
        else:
            # No messages, sleep briefly to allow signal checking
            time.sleep(0.01)  # 10ms sleep
    
    print("Appbar message loop exiting gracefully")
    cleanup_appbar()

if __name__ == "__main__":
    # Register cleanup handlers
    atexit.register(cleanup_appbar)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Clean AppBar Starting...")
    
    hwnd = make_window()
    print("Clean AppBar registered successfully")
    
    try:
        message_loop()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received")
    finally:
        cleanup_appbar()
