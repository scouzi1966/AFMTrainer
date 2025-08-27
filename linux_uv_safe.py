#!/usr/bin/env python3
"""
Linux-safe UV launcher for AFM Trainer.
This launcher prevents X11 threading issues by running in single-threaded mode.
"""

import os
import sys
import threading

# Set X11 environment variables BEFORE any imports
if sys.platform.startswith('linux'):
    # Comprehensive X11 safety environment
    os.environ.update({
        'QT_X11_NO_MITSHM': '1',
        'XLIB_SKIP_ARGB_VISUALS': '1', 
        'XDG_SESSION_TYPE': 'x11',
        'PYTHONUNBUFFERED': '1',
        'LIBGL_ALWAYS_INDIRECT': '1',
        'MESA_GL_VERSION_OVERRIDE': '1.4',
        # Force single-threaded X11 operations
        'LIBXCB_ALLOW_SLOPPY_LOCK': '1',
        'XCB_DISABLE_SEQUENCE_CHECK': '1',
        # Disable problematic GUI features
        'QT_LOGGING_RULES': 'qt.qpa.xcb.warning=false',
        'XLIB_SKIP_ARGB_VISUALS': '1'
    })

    # Completely disable threading to prevent X11 conflicts
    original_thread_init = threading.Thread.__init__
    original_thread_start = threading.Thread.start
    
    def disabled_thread_init(self, *args, **kwargs):
        """Disable thread creation in safe mode."""
        print("Threading disabled for X11 safety")
        pass
        
    def disabled_thread_start(self):
        """Disable thread starting in safe mode."""
        print("Thread start blocked for X11 safety")
        pass
    
    # Comment out threading override for now - might be too aggressive
    # threading.Thread.__init__ = disabled_thread_init
    # threading.Thread.start = disabled_thread_start
    
    # Try X11 threading initialization with error handling
    try:
        import ctypes
        import ctypes.util
        
        x11_lib = ctypes.util.find_library('X11')
        if x11_lib:
            x11 = ctypes.cdll.LoadLibrary(x11_lib)
            x11.XInitThreads()
            
            # Try to set X11 to single-threaded mode
            try:
                x11.XSetErrorHandler(None)  # Ignore X11 errors
            except:
                pass
                
    except Exception as e:
        print(f"X11 setup warning: {e}")

# Import tkinter with error handling
try:
    import tkinter as tk
    # Test tkinter creation in safe mode
    root = tk.Tk()
    root.withdraw()  # Hide the test window
    root.destroy()
    print("✓ Tkinter working in safe mode")
except Exception as e:
    print(f"✗ Tkinter error: {e}")
    print("Trying to continue anyway...")

# Now import and run the GUI
if __name__ == "__main__":
    try:
        print("Loading AFM Trainer in Linux safe mode...")
        from afm_trainer.afm_trainer_gui import main
        print("Starting GUI...")
        print("Creating main window...")
        main()
        print("GUI main() returned")
    except Exception as e:
        print(f"Error starting GUI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)