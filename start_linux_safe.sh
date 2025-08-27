#!/bin/bash
# AFM Trainer Safe Linux Starter
# This script works around X11 threading issues on Linux

echo "🐧 AFM Trainer - Linux Safe Mode"
echo "=================================="

# Check for UV package manager
if ! command -v uv >/dev/null 2>&1; then
    echo "✗ UV package manager not found"
    echo ""
    echo "Install UV first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  # or use the regular launcher: python run.py"
    exit 1
fi

echo "✓ UV package manager found"

# Install dependencies using UV
echo "Installing dependencies with UV..."
if ! uv sync >/dev/null 2>&1; then
    echo "✗ Failed to install GUI dependencies"
    exit 1
fi

if ! uv pip install -r requirements-toolkit.txt >/dev/null 2>&1; then
    echo "✗ Failed to install toolkit dependencies"  
    exit 1
fi

echo "✓ Dependencies installed"

# Export environment variables to prevent X11 issues
export QT_X11_NO_MITSHM=1
export XLIB_SKIP_ARGB_VISUALS=1
export XDG_SESSION_TYPE=x11
export AFM_TRAINER_SAFE_MODE=1

# Check if DISPLAY is set
if [ -z "$DISPLAY" ]; then
    echo "⚠ Warning: No DISPLAY environment variable found"
    echo "Make sure you're in a graphical environment or have X11 forwarding enabled"
    echo ""
fi

echo "✓ Environment configured for X11 compatibility"
echo "🎯 Starting AFM Trainer in safe mode..."
echo ""

# Run with UV in safe mode
echo ""
echo "🎯 Starting AFM Trainer with UV..."

PYTHONUNBUFFERED=1 uv run python -c "
import os
# Set safe mode flag  
os.environ['AFM_TRAINER_SAFE_MODE'] = '1'

try:
    print('Loading AFM Trainer modules...')
    from afm_trainer.afm_trainer_gui import main
    print('Starting GUI...')
    main()
except ImportError as e:
    print(f'Import error: {e}')
    print('Make sure you are in the AFMTrainer directory')
    exit(1)
except Exception as e:
    print(f'Startup error: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"