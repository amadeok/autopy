import ctypes
from ctypes import wintypes

# Constants
PROCESS_DPI_AWARENESS = 2  # PROCESS_PER_MONITOR_DPI_AWARE
MDT_EFFECTIVE_DPI = 0

# Load required DLLs
user32 = ctypes.windll.user32
shcore = ctypes.windll.shcore

# Make process DPI aware (optional but recommended)
try:
    shcore.SetProcessDpiAwareness(PROCESS_DPI_AWARENESS)
except (OSError, AttributeError):
    # Fallback for older Windows versions
    user32.SetProcessDPIAware()

def get_window_dpi(hwnd):
    """Get DPI for the monitor associated with the given window handle."""
    try:
        # Get monitor from window
        monitor = user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST
        if not monitor:
            return 96  # Default DPI

        # Get DPI
        dpi_x = ctypes.c_uint()
        dpi_y = ctypes.c_uint()
        hr = shcore.GetDpiForMonitor(monitor, MDT_EFFECTIVE_DPI, ctypes.byref(dpi_x), ctypes.byref(dpi_y))
        if hr != 0:
            return 96  # Failed; return default
        return dpi_x.value
    except Exception:
        return 96

def get_scaling_factor(hwnd):
    """Return scaling factor (e.g., 1.0 for 100%, 1.5 for 150%)."""
    dpi = get_window_dpi(hwnd)
    return dpi / 96.0

#if __name__ == "__main__":
#     
#     import my_utils.util_ as ut
# 
#     win = ut.get_first_hwnd_with_partial_titles("GEORG")
#     ret =  get_window_dpi(win._hWnd)
#     print(ret)


import ctypes
from ctypes import wintypes

# Enable Per-Monitor DPI Awareness V2
try:
    ctypes.windll.shcore.SetProcessDpiAwarenessContext(
        ctypes.c_ssize_t(-4)  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
    )
except AttributeError:
    # Fallback for older Windows versions (e.g., Windows 7/8)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except (OSError, AttributeError):
        pass  # Best effort; may result in inaccurate coordinates on high-DPI systems

# Get cursor position
class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

def get_cursor_pos():
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

if __name__ == "__main__":
    while 1:
        x, y = get_cursor_pos()
        print(f"Cursor position: ({x}, {y})")