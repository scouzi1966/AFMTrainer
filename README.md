# AFM Trainer

NOTE TO USERS: The WanDB intergration remains untested until I get a chance. Apologies for the inconvenience.

Requires Python 3.11+


## On MacOS: $$\color{blue}{python \space run.py}$$ (all packages will be downloaded automatically with uv and will use Pytoch with Metal)

## On Linux (Ubuntu tested): $$\color{blue}{python\space run-linux.py}$$ (all packages will be downloaded automatically with uv and will use Pytoch with CUDA)

A comprehensive GUI wrapper application for Apple's Foundation Models Adapter Training Toolkit, providing an intuitive interface for training LoRA adapters for Apple's on-device foundation models.

![AFM Trainer](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ⚠️ **Disk Space Requirements**

**Important**: The UV package manager will download and cache dependencies that require approximately **~1 GB of available disk space**. This includes:
- PyTorch and related ML libraries (~800 MB)
- CoreML tools and dependencies (~150 MB)
- Additional Python packages (~50 MB)

Ensure you have sufficient free disk space before installation. You can clean up the UV cache later using the built-in cleanup options when quitting the application.

### 🧹 **Disk Space Management**
- **Automatic Cleanup**: When quitting, the app offers to clean up the UV environment automatically
- **Manual Cleanup**: If you decline, detailed instructions are provided for manual cleanup
- **Cache Location**: UV stores packages in a system cache directory (typically `~/.cache/uv/`)
- **Safe to Clean**: The cache will be recreated automatically when you next run AFM Trainer

## 🌟 Features

- **🎯 Modern GUI**: Beautiful, professional interface with dark/light theme switching
- **🎨 Enhanced Theming**: Modern Sun Valley theme for a polished, forest-inspired appearance
- **📊 Real-time Monitoring**: Live training progress with loss visualization and log streaming
- **🔄 Complete Workflow**: From dataset validation to .fmadapter export
- **⚙️ Flexible Configuration**: All Apple toolkit parameters exposed with sensible defaults
- **📈 WandB Integration**: Optional Weights & Biases logging for advanced metrics tracking
- **🛡️ Comprehensive Error Handling**: User-friendly error messages and crash reporting
- **🔧 UV Environment Management**: Transparent dependency handling and installation
- **📁 Smart File Management**: Automatic .gitignore updates and dataset validation
- **🚀 Draft Model Training**: Optional speculative decoding support
- **💾 Configuration Profiles**: Save and load training configurations
- **🌓 Theme Customization**: Real-time switching between dark and light themes

## 📋 Requirements

- **Operating System**: macOS or Linux (Apple Silicon and Intel Macs supported)
- **Python**: 3.11 or higher
- **Package Manager**: UV (will be installed automatically if missing)
- **Apple Toolkit**: Foundation Models Adapter Training Toolkit v26.0.0+ ([requires entitlements](https://developer.apple.com/apple-intelligence/foundation-models-adapter/))

## 🚀 Quick Start

### 1. Get the Application

```bash
# Option 1: Clone the repository
git clone <repository-url>
cd AFMTrainer

# Option 2: Download and extract the release package
```

### 2. Get Apple's Toolkit

**⚠️ Important**: You must have Apple Developer Program entitlements to access the toolkit.

1. **Visit the official Apple documentation**: [Apple Foundation Models Adapter Training](https://developer.apple.com/apple-intelligence/foundation-models-adapter/)
2. **Download the toolkit** from Apple (requires entitlements)
3. **Place it in one of these locations**:
   - `.adapter_training_toolkit_v26_0_0/` (recommended for auto-detection)
   - `adapter_training_toolkit_v26_0_0/`

**Note**: The toolkit is not included with AFM Trainer and must be obtained directly from Apple.

### 3. Launch the Application

```bash
# Simple launcher (recommended)
# For Linux users, it is recommended to use the dedicated Linux launcher:
# python run-linux.py
# For macOS, use the universal launcher:
python run.py

# Or use UV directly
uv run afm-trainer

# Or run the GUI module directly
uv run python -m afm_trainer.afm_trainer_gui
```

The launcher will automatically:
- Check Python version compatibility
- Install UV if missing
- Set up the environment
- Detect the Apple toolkit
- Launch the GUI with modern theming

## 🎨 Visual Experience

AFM Trainer features a modern, professional interface with:

### 🌓 **Theme Options**
- **Dark Theme** (default): Professional dark interface inspired by modern development tools
- **Light Theme**: Clean, bright interface for different preferences
- **Real-time Switching**: Toggle between themes instantly from the header

### ✨ **Visual Enhancements**
- **Modern Styling**: Sun Valley theme providing a forest-inspired, Excel-like appearance
- **Professional Typography**: Enhanced fonts and spacing for better readability
- **Icon Integration**: Meaningful icons throughout the interface for improved navigation
- **Visual Hierarchy**: Clear organization with styled sections and grouped controls
- **Enhanced Controls**: Modern buttons, entries, and interactive elements

### 🎯 **User Experience**
- **Intuitive Layout**: Logical flow from setup to training to export
- **Visual Feedback**: Clear status indicators and progress visualization
- **Accessibility**: High contrast and readable typography in both themes
- **Consistency**: Unified styling across all interface elements

**Try the Theme Demo**: Run `uv run python theme_demo.py` to see the visual improvements!

### ⚡ **Performance Mode**
For ultra-fast tab switching, enable Performance Mode:

```bash
# Enable high-performance mode
AFM_TRAINER_PERFORMANCE_MODE=true python run.py
```

**Performance Mode Features:**
- **⚡ Instant Tab Switching**: 2-3x faster tab switching performance
- **🎯 Optimized Theme**: Fast native theme instead of sv-ttk  
- **🚀 Reduced Overhead**: Minimal theme updates and visual effects
- **💡 Smart Fallbacks**: Maintains full functionality with speed priority

**When to Use Performance Mode:**
- Slow tab switching on your system
- Working with large datasets requiring frequent tab changes
- Older hardware or systems with limited graphics performance
- Preference for speed over visual styling

**Theme Comparison:**
- **Normal Mode**: Beautiful dark theme, ~0.06s tab switching
- **Performance Mode**: Clean native theme, ~0.03s tab switching (**50% faster**)

## 📖 User Guide

### Setup Tab

1. **Toolkit Configuration**
   - Browse and select your Apple toolkit directory
   - The app will automatically validate the toolkit and update .gitignore

2. **Dataset Configuration**
   - Select your training JSONL file (required)
   - Optionally select evaluation JSONL file
   - The app will validate dataset format and show preview

3. **Output Configuration**
   - Choose output directory for checkpoints and exports
   - Directory will be created automatically if it doesn't exist

### Training Tab

Configure all training parameters with real-time validation:

**Basic Parameters:**
- **Epochs**: Number of training passes (default: 2)
- **Learning Rate**: Step size for parameter updates (default: 1e-4)
- **Batch Size**: Samples per training batch (default: 4)

**Advanced Parameters:**
- **Warmup Epochs**: Learning rate warmup period (default: 1)
- **Gradient Accumulation**: Steps to accumulate gradients (default: 1)
- **Weight Decay**: Regularization coefficient (default: 1e-2)
- **Precision**: Training precision (bf16-mixed, f16-mixed, bf16, f32)
- **Activation Checkpointing**: Memory optimization (trades compute for memory)
- **Model Compilation**: Performance optimization (CUDA only)

### Export Tab

Configure adapter metadata and export options:

- **Adapter Name**: Name for your exported adapter
- **Author**: Your name or organization
- **Description**: Detailed adapter description
- **License**: License information
- **Draft Model**: Enable speculative decoding training

**WandB Integration:**
- Enable/disable Weights & Biases logging
- Automatic login status detection
- Real-time training metrics tracking

### Monitor Tab

Real-time training monitoring:
- **Progress Bar**: Visual training progress
- **Live Logs**: Streaming training output with timestamps
- **Loss Tracking**: Real-time loss values and trends
- **Time Estimates**: Estimated completion times

## 📊 Dataset Format

Training data must be in JSONL (JSON Lines) format. Each line represents one training sample:

### Basic Format
```json
[{"role": "user", "content": "Tell me about cats"}, {"role": "assistant", "content": "Cats are fascinating animals..."}]
```

### With System Instructions
```json
[{"role": "system", "content": "You are a helpful pet expert"}, {"role": "user", "content": "Tell me about cats"}, {"role": "assistant", "content": "Cats are fascinating animals..."}]
```

### Multi-turn Conversations
```json
[{"role": "system", "content": "You are a helpful assistant"}, {"role": "user", "content": "What's 2+2?"}, {"role": "assistant", "content": "4"}, {"role": "user", "content": "What about 3+3?"}, {"role": "assistant", "content": "6"}]
```

### Alternative Wrapped Format
```json
{"messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]}
```

The app includes comprehensive dataset validation and will report:
- Format errors with line numbers
- Sample statistics (token counts, message types)
- Preview of first few samples
- Role distribution analysis

## 🔧 Advanced Configuration

### Configuration Profiles

Save frequently used configurations:
- Configurations are saved in `config_profiles/`
- Load/save via the GUI (future enhancement)
- JSON format for easy editing

### Environment Variables

```bash
# WandB configuration
export WANDB_API_KEY=your_api_key
export WANDB_PROJECT=your_project_name

# Logging configuration
export AFM_TRAINER_LOG_LEVEL=DEBUG
```

### Command Line Options

For advanced users, you can bypass the GUI:

```bash
# Run training directly
uv run python -m examples.train_adapter \
  --train-data train.jsonl \
  --eval-data eval.jsonl \
  --epochs 5 \
  --learning-rate 1e-4 \
  --batch-size 4 \
  --checkpoint-dir ./output

# Export adapter
uv run python -m export.export_fmadapter \
  --output-dir ./output \
  --adapter-name my_adapter \
  --checkpoint adapter-final.pt \
  --author "Your Name"
```

## 🐛 Troubleshooting

### Common Issues

**"Toolkit directory not found"**
- Ensure you have Apple Developer Program entitlements to access the toolkit
- Download the toolkit from [Apple's official page](https://developer.apple.com/apple-intelligence/foundation-models-adapter/)
- Ensure the Apple toolkit is in the correct directory
- Use the Browse button to select the toolkit location
- Check that the toolkit contains `examples/`, `export/`, and `assets/` directories

**"Training process failed"**
- Check the logs in the Monitor tab for detailed error messages
- Verify dataset format with the validation feature
- Ensure sufficient memory (4GB+ recommended)
- Try reducing batch size if encountering out-of-memory errors

**"WandB login required"**
- Run `wandb login` in your terminal
- Or set `WANDB_API_KEY` environment variable
- Or disable WandB integration in the Export tab

**"Permission denied errors"**
- Ensure you have write permissions to the output directory
- On macOS, you may need to grant terminal full disk access

### Performance Tips

**Memory Optimization:**
- Enable activation checkpointing for large models
- Reduce batch size if encountering OOM errors
- Use bf16-mixed or f16-mixed precision

**Speed Optimization:**
- Enable model compilation (CUDA only)
- Use larger batch sizes if memory allows
- Train draft model separately if not needed immediately

**Dataset Tips:**
- Keep samples reasonably sized (< 2048 tokens recommended)
- Balance your dataset across different use cases
- Include system messages for consistent behavior

### Log Files

Logs are automatically saved to:
- `logs/afm_trainer.log` - Application logs
- `logs/training_YYYYMMDD_HHMMSS.log` - Training session logs (future enhancement)

## 🤝 Contributing

Contributions are welcome! Please see our contributing guidelines for:
- Code style and formatting
- Testing requirements  
- Documentation standards
- Pull request process

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Note**: The Apple Foundation Models Adapter Training Toolkit is subject to Apple's licensing terms and must be obtained separately from Apple. Access requires Apple Developer Program entitlements. Visit the [official documentation](https://developer.apple.com/apple-intelligence/foundation-models-adapter/) for more information.

## 🙏 Acknowledgments

- Apple for the Foundation Models Adapter Training Toolkit
- The open-source community for the excellent Python libraries used
- Contributors and testers who help improve this application

## 📞 Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join the community discussions for help and tips


---

**Made with ❤️ for the AI community**
