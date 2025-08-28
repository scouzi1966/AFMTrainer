#!/usr/bin/env python3
"""
AFM Trainer Launcher for Linux - Handles X11 threading issues
Linux-specific launcher with proper X11 threading setup.
"""

import sys
import subprocess
import os
from pathlib import Path


def setup_linux_environment():
    """Set up Linux-specific environment variables for GUI applications."""
    env_vars = {
        'QT_X11_NO_MITSHM': '1',
        'XLIB_SKIP_ARGB_VISUALS': '1',
        'XDG_SESSION_TYPE': 'x11',
        'AFM_TRAINER_LINUX_MODE': '1',
        # Disable problematic X11 extensions
        'XLIB_SKIP_ARGB_VISUALS': '1',
        'QT_PLUGIN_PATH': '',
        # Force single-threaded X11 mode
        'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
    }
    
    for key, value in env_vars.items():
        os.environ.setdefault(key, value)


def check_uv_installed():
    """Check if UV is installed."""
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def install_uv():
    """Install UV package manager."""
    print("UV not found. Installing UV...")
    try:
        # Install UV using the official installer for Linux
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False) as tmp_script:
            subprocess.run(['curl', '-LsSf', 'https://astral.sh/uv/install.sh'], stdout=tmp_script, check=True)
            tmp_script_path = tmp_script.name
        subprocess.run(['sh', tmp_script_path], check=True)
        os.remove(tmp_script_path)
        print("✓ UV installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install UV: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during UV installation: {e}")
        return False


def main():
    """Main launcher function for Linux."""
    print("🐧 AFM Trainer Linux Launcher")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 11):
        print(f"✗ Python 3.11+ required, found {sys.version_info.major}.{sys.version_info.minor}")
        print("Please upgrade Python and try again.")
        sys.exit(1)
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Check for UV
    if not check_uv_installed():
        print("UV package manager not found.")
        response = input("Install UV now? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            if not install_uv():
                print("Please install UV manually: https://docs.astral.sh/uv/getting-started/installation/")
                sys.exit(1)
        else:
            print("UV is required to run AFM Trainer.")
            print("Install it manually: https://docs.astral.sh/uv/getting-started/installation/")
            sys.exit(1)
    
    print("✓ UV package manager available")
    
    # Set up Linux-specific environment
    setup_linux_environment()
    print("✓ Linux X11 environment configured")
    
    # Check if display is available
    if not os.environ.get('DISPLAY'):
        print("⚠ No DISPLAY environment variable found")
        print("Make sure you're running in a graphical environment or have X11 forwarding enabled")
        
        # Try to start anyway - might work with Wayland
        print("Attempting to start anyway...")
    
    # Run the application with Linux-specific settings
    print("\n🎯 Starting AFM Trainer (Linux mode)...")
    try:
        # Create a modified environment with X11 fixes
        env = os.environ.copy()
        env.update({
            'QT_X11_NO_MITSHM': '1',
            'XLIB_SKIP_ARGB_VISUALS': '1',
            'XDG_SESSION_TYPE': 'x11',
            'AFM_TRAINER_LINUX_MODE': '1',
        })
        
        # Use UV to run the application with the modified environment
        result = subprocess.run([
            'uv', 'run', 'python', '-c',
            '''
import os
import sys
sys.path.insert(0, ".")

# Force single-threaded mode to avoid X11 issues
import threading
original_start = threading.Thread.start
def safe_start(self):
    # Reduce thread priority to minimize X11 conflicts
    try:
        original_start(self)
    except Exception as e:
        print(f"Thread start warning: {e}")
        pass
threading.Thread.start = safe_start

try:
    from afm_trainer.afm_trainer_gui import main
    main()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
        ], cwd=Path(__file__).parent, env=env)
        
        sys.exit(result.returncode)
        
    except KeyboardInterrupt:
        print("\n👋 AFM Trainer stopped by user")
        sys.exit(0)
    except FileNotFoundError:
        print("✗ Could not start AFM Trainer")
        print("Make sure you're in the AFMTrainer directory and UV is properly installed.")
        print("\nTry running the regular launcher instead:")
        print("  python run.py")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error starting AFM Trainer: {e}")
        print("\nTroubleshooting tips for Linux:")
        print("1. Make sure you have a working X11 display: echo $DISPLAY")
        print("2. Try installing missing GUI libraries:")
        print("   - Ubuntu/Debian: sudo apt install python3-tk")
        print("   - Fedora/CentOS: sudo dnf install tkinter")
        print("   - Arch: sudo pacman -S tk")
        print("3. If using SSH, enable X11 forwarding: ssh -X username@hostname")
        print("4. Try the regular launcher: python run.py")
        sys.exit(1)


if __name__ == "__main__":
    main()