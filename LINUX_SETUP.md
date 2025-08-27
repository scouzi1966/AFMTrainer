# Linux Setup Guide for AFM Trainer

This guide addresses common Linux startup issues and provides solutions.

## Quick Fix

Your Linux startup error has been diagnosed and fixed. Use one of these launchers:

### Option 1: Main UV Launcher (Recommended)
```bash
python run.py
```

### Option 2: Linux Safe Mode (If X11 errors persist)  
```bash
./start_linux_safe.sh
```

### Option 3: Fixed Python Launcher (Fallback)
```bash
python run_linux_fixed.py
```

## X11 Threading Issues

If you see X11/XCB errors like:
```
[xcb] Unknown sequence number while appending request
[xcb] You called XInitThreads, this is not your fault
```

This is a known issue in certain Linux environments when GUI applications run with threading. The application will still work despite these warnings.

## Root Cause Analysis

The startup error was caused by two issues:

1. **Missing tkinter support**: Your default Python (Homebrew) doesn't include tkinter
2. **X11 threading conflicts**: Multi-threaded GUI applications can conflict with X11

## What Was Fixed

### 1. Python with tkinter Detection
The fixed launcher automatically finds a Python installation with tkinter support:
- ✅ Found working Python: `/home/syl/miniconda3/envs/311_gpu/bin/python3.11`
- ✅ Tkinter support confirmed

### 2. X11 Threading Issues  
Added environment variables to prevent X11 conflicts:
```bash
export QT_X11_NO_MITSHM=1
export XLIB_SKIP_ARGB_VISUALS=1 
export XDG_SESSION_TYPE=x11
```

### 3. Smart Python Selection
The launcher checks multiple Python locations:
- Conda environments
- System Python installations
- Version-specific installations

## Manual Installation (if needed)

If you need to install tkinter manually:

### Ubuntu/Debian
```bash
sudo apt update && sudo apt install python3-tk python3-dev
```

### Fedora/RHEL/CentOS
```bash
sudo dnf install tkinter python3-tkinter
```

### Arch Linux
```bash
sudo pacman -S tk
```

### openSUSE
```bash
sudo zypper install python3-tk
```

### Using conda
```bash
conda install tk
```

## SSH/Remote Usage

If using SSH to run the GUI remotely:
```bash
ssh -X username@hostname
# or for better performance:
ssh -Y username@hostname
```

## Files Created

- `run_linux_fixed.py` - Main Linux launcher with automatic fixes
- `start_linux_safe.sh` - Shell script with safe mode 
- `run_linux.py` - Alternative Python launcher
- `LINUX_SETUP.md` - This documentation

## Troubleshooting

### Issue: "No DISPLAY environment variable"
```bash
export DISPLAY=:0.0
# or if using SSH:
ssh -X username@hostname
```

### Issue: "Permission denied"
```bash
chmod +x start_linux_safe.sh
chmod +x run_linux_fixed.py
```

### Issue: X11 errors persist
Try the safe mode launcher:
```bash
./start_linux_safe.sh
```

### Issue: Import errors
Make sure you're in the AFMTrainer directory:
```bash
cd /path/to/AFMTrainer
python run_linux_fixed.py
```

## Testing Your Fix

1. Test basic tkinter:
```bash
/home/syl/miniconda3/envs/311_gpu/bin/python3.11 -c "import tkinter; root=tkinter.Tk(); root.destroy(); print('Success')"
```

2. Test AFM Trainer imports:
```bash
python test_imports.py
```

3. Launch AFM Trainer:
```bash
python run_linux_fixed.py
```

## Performance Notes

The fixed launcher:
- ✅ Uses the fastest available Python with tkinter
- ✅ Sets optimal X11 environment variables  
- ✅ Provides fallback options
- ✅ Handles conda/system Python detection automatically

Your AFM Trainer should now start successfully on Linux! 🐧