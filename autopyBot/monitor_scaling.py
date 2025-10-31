# get_monitor_scaling.py
import ctypes
from ctypes import wintypes
import json

def main():
    # Enable per-monitor DPI awareness
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass

    monitors = []

    def _monitor_enum_proc(hMonitor, hdc, lprcMonitor, dwData):
        try:
            dpi_x = ctypes.c_uint()
            ctypes.windll.shcore.GetDpiForMonitor(hMonitor, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_x))
            scaling = dpi_x.value / 96.0
            rect = lprcMonitor.contents
            monitors.append({
                "handle": hMonitor,
                "rect": {
                    "left": rect.left,
                    "top": rect.top,
                    "right": rect.right,
                    "bottom": rect.bottom,
                    "width": rect.right - rect.left,
                    "height": rect.bottom - rect.top
                },
                "dpi": dpi_x.value,
                "scaling": round(scaling, 4)
            })
        except Exception:
            pass
        return True

    MonitorEnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
    ctypes.windll.user32.EnumDisplayMonitors(None, None, MonitorEnumProc(_monitor_enum_proc), 0)

    # Output as JSON for easy parsing
    print(json.dumps(monitors, indent=2))




# Example usage:
# hwnd = 123456  # Replace with actual window handle
# print(f"Scaling factor: {get_scaling_factor(hwnd):.2f}")

if __name__ == "__main__":
    main()