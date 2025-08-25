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
            subprocess.run(['curl', '-LsSf', 'https://astral.sh/uv/install.sh', '|', 'sh'], shell=True, check=True)
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
    
    # Run the application
    print("\n🎯 Starting AFM Trainer...")
    try:
        # Use UV to run the application
        result = subprocess.run([
            'uv', 'run', 'python', '-m', 'afm_trainer.afm_trainer_gui'
        ], cwd=Path(__file__).parent)
        
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