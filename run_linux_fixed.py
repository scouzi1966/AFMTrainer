#!/usr/bin/env python3
"""
AFM Trainer Linux Launcher - Fixed Version
Handles common Linux issues: tkinter availability and X11 threading.
"""

import sys
import subprocess
import os
from pathlib import Path
import shutil


def check_uv_python():
    """Check if UV can provide a Python with tkinter support."""
    try:
        # Test if uv run python works and has tkinter
        result = subprocess.run([
            'uv', 'run', 'python', '-c', 'import tkinter; import _tkinter; print("tkinter available")'
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            return True
        else:
            return False
    except Exception:
        return False


def install_tkinter_instructions():
    """Provide instructions for installing tkinter on different Linux distributions."""
    print("✗ No Python installation found with tkinter support")
    print()
    print("To fix this issue, install tkinter for your Linux distribution:")
    print()
    print("Ubuntu/Debian:")
    print("  sudo apt update && sudo apt install python3-tk python3-dev")
    print()
    print("Fedora/RHEL/CentOS:")
    print("  sudo dnf install tkinter python3-tkinter")
    print()
    print("Arch Linux:")
    print("  sudo pacman -S tk")
    print()
    print("openSUSE:")
    print("  sudo zypper install python3-tk")
    print()
    print("Using conda:")
    print("  conda install tk")
    print()
    print("Using homebrew:")
    print("  brew install python-tk")
    print()
    

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
        subprocess.run(['curl', '-LsSf', 'https://astral.sh/uv/install.sh', '|', 'sh'], 
                      shell=True, check=True)
        print("✓ UV installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install UV: {e}")
        return False


def main():
    """Main launcher function."""
    print("🐧 AFM Trainer - Linux Launcher (Fixed)")
    print("=" * 45)
    
    # Check for UV first (required for dependency management)
    if not check_uv_installed():
        print("✗ UV package manager not found")
        response = input("Install UV now? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            if not install_uv():
                print("Please install UV manually: https://docs.astral.sh/uv/getting-started/installation/")
                sys.exit(1)
        else:
            print("UV is required for AFM Trainer dependency management.")
            print("Install it manually: https://docs.astral.sh/uv/getting-started/installation/")
            sys.exit(1)
    
    print("✓ UV package manager available")
    
    # Install dependencies using UV (this ensures tkinter availability too)
    print("\n📦 Installing dependencies with UV...")
    try:
        # Install GUI wrapper dependencies
        subprocess.run(['uv', 'sync'], cwd=Path(__file__).parent, check=True)
        print("✓ GUI dependencies installed")
        
        # Install toolkit dependencies
        subprocess.run(['uv', 'pip', 'install', '-r', 'requirements-toolkit.txt'], 
                      cwd=Path(__file__).parent, check=True)
        print("✓ Toolkit dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        sys.exit(1)
    
    # Check if UV-managed Python has tkinter
    if not check_uv_python():
        print("✗ UV-managed Python doesn't have tkinter support")
        install_tkinter_instructions()
        print("\nAfter installing tkinter, try running the regular launcher:")
        print("  python run.py")
        sys.exit(1)
    
    print("✓ UV-managed Python with tkinter confirmed")
    
    # Check if display is available
    if not os.environ.get('DISPLAY'):
        print("⚠ No DISPLAY environment variable found")
        print("Make sure you're running in a graphical environment")
        print("For SSH connections, use: ssh -X username@hostname")
    else:
        print("✓ Display environment available")
    
    # Set up Linux-specific environment to prevent X11 issues
    env = os.environ.copy()
    env.update({
        'QT_X11_NO_MITSHM': '1',
        'XLIB_SKIP_ARGB_VISUALS': '1', 
        'XDG_SESSION_TYPE': 'x11',
        'AFM_TRAINER_LINUX_MODE': '1',
        'PYTHONUNBUFFERED': '1'
    })
    
    print("✓ Linux X11 environment configured")
    
    # Check for Apple toolkit
    toolkit_dirs = [
        Path.cwd() / ".adapter_training_toolkit_v26_0_0",
        Path.cwd() / "adapter_training_toolkit_v26_0_0",
    ]
    
    toolkit_found = False
    for toolkit_dir in toolkit_dirs:
        if toolkit_dir.exists() and (toolkit_dir / "examples").exists():
            print(f"✓ Apple toolkit found: {toolkit_dir.name}")
            toolkit_found = True
            break
    
    if not toolkit_found:
        print("⚠ Apple Foundation Models Adapter Training Toolkit not found")
        print("You can select the toolkit directory in the GUI")
    
    print("\n🎯 Starting AFM Trainer...")
    
    try:
        # Use UV to run the application with all dependencies managed
        print("Starting with UV-managed environment...")
        result = subprocess.run([
            'uv', 'run', 'python', '-m', 'afm_trainer.afm_trainer_gui'
        ], cwd=Path(__file__).parent, env=env)
        
        sys.exit(result.returncode)
        
    except KeyboardInterrupt:
        print("\n👋 AFM Trainer stopped by user")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"✗ Could not start AFM Trainer: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're in the AFMTrainer directory")
        print("2. Install missing dependencies:")
        print(f"   {python_exec} -m pip install -r requirements.txt")  
        print("3. Check that all Python modules are available")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error starting AFM Trainer: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()