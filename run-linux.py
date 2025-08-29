#!/usr/bin/env python3
"""
AFM Trainer Universal Launcher
Unified launcher that handles all platforms and common issues.
"""

import sys
import subprocess
import os
from pathlib import Path
import platform
import shutil


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
        if sys.platform.startswith('win'):
            # Windows
            subprocess.run(['powershell', '-c', 'irm https://astral.sh/uv/install.ps1 | iex'], check=True)
        else:
            # macOS/Linux
            subprocess.run(['curl', '-LsSf', 'https://astral.sh/uv/install.sh'], 
                          stdout=subprocess.PIPE, shell=False)
            subprocess.run(['sh'], input=subprocess.run(['curl', '-LsSf', 'https://astral.sh/uv/install.sh'], 
                          capture_output=True, text=True).stdout, text=True, check=True)
        
        print("✓ UV installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install UV: {e}")
        return False


def check_toolkit_directory():
    """Check if the Apple toolkit directory exists."""
    possible_dirs = [
        Path.cwd() / ".adapter_training_toolkit_v26_0_0",
        Path.cwd() / "adapter_training_toolkit_v26_0_0",
    ]
    
    # Also check for any directory matching the pattern
    for pattern in [".adapter_training_toolkit_v*", "adapter_training_toolkit_v*"]:
        possible_dirs.extend(Path.cwd().glob(pattern))
    
    for toolkit_dir in possible_dirs:
        if toolkit_dir.exists() and (toolkit_dir / "examples").exists():
            return toolkit_dir
            
    return None


def install_dependencies():
    """Install all dependencies using UV."""
    print("\n📦 Installing dependencies with UV...")
    
    try:
        # Install GUI wrapper dependencies (from pyproject.toml)
        print("  Installing AFM Trainer GUI dependencies...")
        print("    This may take several minutes to download CUDA libraries...")
        result = subprocess.run(['uv', 'sync'], cwd=Path(__file__).parent, check=False)
        if result.returncode == 0:
            print("  ✓ GUI dependencies installed")
        else:
            print(f"  ⚠ GUI dependencies installation had issues (exit code: {result.returncode})")
            print("    Continuing anyway - some features may not work")
        
        # Install Apple toolkit dependencies (from requirements-toolkit.txt)
        if Path('requirements-toolkit.txt').exists():
            print("  Installing Apple toolkit dependencies...")
            try:
                result = subprocess.run([
                    'uv', 'add', '-r', 'requirements-toolkit.txt'
                ], cwd=Path(__file__).parent, check=False)
                if result.returncode == 0:
                    print("  ✓ Toolkit dependencies installed")
                else:
                    print("  ⚠ Some toolkit dependencies unavailable (requires Apple toolkit)")
                    print("    GUI will run but training may require additional setup")
            except Exception as e:
                print(f"  ⚠ Error installing toolkit dependencies: {e}")
                print("    GUI will run but training may require additional setup")
        
        return True
    except Exception as e:
        print(f"  ⚠ Dependency installation error: {e}")
        print("  Continuing anyway - some features may not work")
        return True  # Continue even if dependencies fail


def check_tkinter_support():
    """Check if Python has tkinter support."""
    try:
        # First try UV-managed Python
        result = subprocess.run([
            'uv', 'run', 'python', '-c', 'import tkinter; import _tkinter; print("OK")'
        ], capture_output=True, text=True, cwd=Path(__file__).parent, timeout=10)
        
        if result.returncode == 0:
            return True, 'uv'
            
        # Try system Python alternatives
        python_candidates = ['python3', 'python', sys.executable]
        
        for python_cmd in python_candidates:
            try:
                result = subprocess.run([
                    python_cmd, '-c', 'import tkinter; import _tkinter; print("OK")'
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    return True, python_cmd
            except:
                continue
                
        return False, None
        
    except Exception:
        return False, None


def setup_linux_environment():
    """Set up Linux-specific environment variables."""
    return {
        'QT_X11_NO_MITSHM': '1',
        'XLIB_SKIP_ARGB_VISUALS': '1',
        'XDG_SESSION_TYPE': 'x11',
        'AFM_TRAINER_LINUX_MODE': '1',
        'PYTHONUNBUFFERED': '1'
    }


def find_working_python_linux():
    """Find a Python installation with tkinter that works on Linux."""
    # Priority order: conda environments, system Python, UV Python
    python_candidates = [
        '/usr/bin/python3',
        '/usr/bin/python',
        'python3',
        'python'
    ]
    
    for python_path in python_candidates:
        try:
            test_result = subprocess.run([
                python_path, '-c', 'import tkinter; import sys; print(sys.executable)'
            ], capture_output=True, text=True, timeout=5)
            
            if test_result.returncode == 0:
                return python_path
        except:
            continue
    
    return None


def main():
    """Main launcher function."""
    system_name = platform.system()
    
    if system_name == "Linux":
        print("🐧 AFM Trainer - Universal Launcher (Linux)")
    elif system_name == "Darwin":
        print("🍎 AFM Trainer - Universal Launcher (macOS)")
    elif system_name == "Windows":
        print("🪟 AFM Trainer - Universal Launcher (Windows)")
    else:
        print("🚀 AFM Trainer - Universal Launcher")
    
    print("=" * 50)
    
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
    
    # Install all dependencies using UV
    if not install_dependencies():
        print("\n✗ Dependency installation failed")
        print("Check your internet connection and try again.")
        sys.exit(1)
    
    # Check tkinter support
    tkinter_ok, python_cmd = check_tkinter_support()
    if not tkinter_ok:
        print("✗ No Python installation found with tkinter support")
        print("\nTo fix this issue, install tkinter for your system:")
        if system_name == "Linux":
            print("\nUbuntu/Debian: sudo apt update && sudo apt install python3-tk")
            print("Fedora/RHEL:   sudo dnf install tkinter python3-tkinter")
            print("Arch Linux:    sudo pacman -S tk")
            print("Using conda:   conda install tk")
        elif system_name == "Darwin":
            print("\nUsing Homebrew: brew install python-tk")
            print("Using conda:    conda install tk")
        elif system_name == "Windows":
            print("\nReinstall Python from python.org with tkinter included")
        sys.exit(1)
    
    print(f"✓ tkinter support confirmed ({python_cmd})")
    
    # Check for toolkit directory
    toolkit_dir = check_toolkit_directory()
    if not toolkit_dir:
        print("⚠ Apple Foundation Models Adapter Training Toolkit not found")
        print("\n📋 To get the toolkit:")
        print("  1. Ensure you have Apple Developer Program entitlements")
        print("  2. Visit: https://developer.apple.com/apple-intelligence/foundation-models-adapter/")
        print("  3. Download and place in:")
        print("     - .adapter_training_toolkit_v26_0_0/ (recommended)")
        print("     - adapter_training_toolkit_v26_0_0/")
        print("\n💡 You can also select the toolkit directory in the GUI.")
    else:
        print(f"✓ Apple toolkit found: {toolkit_dir.name}")
    
    # Set up environment
    env = os.environ.copy()
    
    if system_name == "Linux":
        # Linux-specific setup
        if not env.get('DISPLAY'):
            print("⚠ No DISPLAY environment variable found")
            print("Make sure you're running in a graphical environment")
            print("For SSH: ssh -X username@hostname")
        else:
            print("✓ Display environment available")
        
        env.update(setup_linux_environment())
        print("✓ Linux X11 environment configured")
    
    # Run the application
    print("\n🎯 Starting AFM Trainer...")
    
    try:
        if system_name == "Linux":
            # On Linux, run directly in the same process to avoid subprocess X11 issues
            print("🛡️  Running in Linux X11 safe mode (direct execution)...")
            
            # Set up environment variables for the current process
            for key, value in env.items():
                if key not in os.environ:  # Don't override existing vars
                    os.environ[key] = value
            
            # Set up Python path to include UV packages
            uv_site_packages = Path(__file__).parent / ".venv" / "lib" / "python3.11" / "site-packages"
            if uv_site_packages.exists():
                if 'PYTHONPATH' in os.environ:
                    os.environ['PYTHONPATH'] = f"{uv_site_packages}:{Path(__file__).parent}:{os.environ['PYTHONPATH']}"
                else:
                    os.environ['PYTHONPATH'] = f"{uv_site_packages}:{Path(__file__).parent}"
            
            # Add current directory to Python path
            sys.path.insert(0, str(Path(__file__).parent))
            
            # Import and run directly
            try:
                from afm_trainer.afm_trainer_gui import main
                main()
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
        else:
            # macOS and Windows - use UV subprocess
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
        print("2. Try running directly: python -m afm_trainer.afm_trainer_gui")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error starting AFM Trainer: {e}")
        if system_name == "Linux":
            print("\nLinux troubleshooting:")
            print("1. Check display: echo $DISPLAY")
            print("2. For SSH: ssh -X username@hostname") 
            print("3. Install GUI libs: sudo apt install python3-tk (Ubuntu)")
        sys.exit(1)


if __name__ == "__main__":
    main()
