#!/usr/bin/env python3
"""
AFM Trainer Launcher
Simple launcher script for the AFM Trainer GUI application.
"""

import sys
import subprocess
from pathlib import Path
import os


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
        # Install UV using the official installer
        if sys.platform.startswith('win'):
            # Windows
            subprocess.run(['powershell', '-c', 'irm https://astral.sh/uv/install.ps1 | iex'], check=True)
        else:
            # macOS/Linux
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
        subprocess.run(['uv', 'sync'], cwd=Path(__file__).parent, check=True)
        print("  ✓ GUI dependencies installed")
        
        # Install Apple toolkit dependencies
        print("  Installing Apple toolkit dependencies...")
        if sys.platform == 'darwin':
            # macOS: Install default PyTorch (for Metal) and other dependencies from the file
            print("    Detected macOS. Installing PyTorch for Metal...")
            
            with open('requirements-toolkit.txt', 'r') as f:
                lines = f.readlines()
            
            # Filter out CUDA-specific torch and the index URL
            non_torch_reqs = [
                line.strip() for line in lines 
                if 'torch' not in line and 'extra-index-url' not in line and line.strip() and not line.strip().startswith('#')
            ]
            
            # Install other packages
            if non_torch_reqs:
                subprocess.run(
                    ['uv', 'pip', 'install'] + non_torch_reqs,
                    cwd=Path(__file__).parent, check=True
                )

            # Install default PyTorch for Metal support
            subprocess.run(
                ['uv', 'pip', 'install', 'torch', 'torchvision', 'torchaudio'],
                cwd=Path(__file__).parent, check=True
            )
            print("    ✓ PyTorch for Metal installed.")
        else:
            # Linux/Windows: Install from requirements-toolkit.txt (CUDA)
            print("    Detected Linux/Windows. Installing PyTorch for CUDA from requirements-toolkit.txt...")
            subprocess.run(
                ['uv', 'pip', 'install', '-r', 'requirements-toolkit.txt'],
                cwd=Path(__file__).parent, check=True
            )
        
        print("  ✓ Toolkit dependencies installed")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to install dependencies: {e}")
        print("  Check your internet connection and requirements files")
        return False
    except FileNotFoundError:
        print("  ✗ Requirements file not found")
        print("  Make sure you're running from the AFMTrainer directory")
        return False



def main():
    """Main launcher function."""
    print("🚀 AFM Trainer Launcher")
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
    
    # Install all dependencies using UV
    if not install_dependencies():
        print("\n✗ Dependency installation failed")
        print("Check your internet connection and try again.")
        sys.exit(1)
    
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
    
    # Run the application using UV-managed environment
    print("\n🎯 Starting AFM Trainer...")
    try:
        # Set up environment for Linux X11 compatibility
        env = os.environ.copy()
        if sys.platform.startswith('linux'):
            env.update({
                'QT_X11_NO_MITSHM': '1',
                'XLIB_SKIP_ARGB_VISUALS': '1',
                'XDG_SESSION_TYPE': 'x11',
                'AFM_TRAINER_LINUX_MODE': '1',
                'PYTHONUNBUFFERED': '1'
            })
        
        # Use UV to run the application with all dependencies managed
        if sys.platform.startswith('linux'):
            print("🛡️  Using Linux X11 safe mode...")
            # On Linux, use system Python with UV packages in PYTHONPATH to avoid X11 issues
            uv_site_packages = Path(__file__).parent / ".venv" / "lib" / "python3.11" / "site-packages"
            env['PYTHONPATH'] = f"{uv_site_packages}:{Path(__file__).parent}:{env.get('PYTHONPATH', '')}"
            
            # Find a working Python with tkinter (prioritize conda/system Python)
            working_python = None
            for python_path in ['/usr/bin/python3', 'python3']:
                try:
                    test_result = subprocess.run([python_path, '-c', 'import tkinter'], 
                                               capture_output=True, timeout=5)
                    if test_result.returncode == 0:
                        working_python = python_path
                        break
                except:
                    continue
            
            if working_python:
                print(f"✓ Using working Python: {working_python}")
                result = subprocess.run([
                    working_python, 'linux_uv_safe.py'
                ], cwd=Path(__file__).parent, env=env)
            else:
                print("⚠ Falling back to UV Python (may have X11 issues)")
                result = subprocess.run(
                    ['uv', 'run', 'python', 'linux_uv_safe.py'],
                    cwd=Path(__file__).parent,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                # Filter out known X11 error messages, but keep all other output
                filtered_lines = []
                x11_error_patterns = [
                    "[xcb]",
                    "python3:.*xcb"
                ]
                import re
                for line in result.stdout.splitlines():
                    if any(re.search(pattern, line) for pattern in x11_error_patterns):
                        continue
                    filtered_lines.append(line)
                print("\n".join(filtered_lines))
        else:
            result = subprocess.run([
                'uv', 'run', 'python', '-m', 'afm_trainer.afm_trainer_gui'
            ], cwd=Path(__file__).parent, env=env)
        
        sys.exit(result.returncode)
        
    except KeyboardInterrupt:
        print("\n👋 AFM Trainer stopped by user")
        sys.exit(0)
    except FileNotFoundError:
        print("✗ Could not start AFM Trainer")
        print("Make sure you're in the AFMTrainer directory and UV is properly installed.")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error starting AFM Trainer: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()