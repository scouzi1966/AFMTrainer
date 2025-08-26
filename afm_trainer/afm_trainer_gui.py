#!/usr/bin/env python3
"""
AFM Trainer GUI - Main application interface for Apple Foundation Models Adapter Training.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
from pathlib import Path
from typing import Optional
import logging
import datetime

# Import sv-ttk for modern theming
try:
    import sv_ttk
    SV_TTK_AVAILABLE = True
except ImportError:
    SV_TTK_AVAILABLE = False

from .config_manager import ConfigManager, TrainingConfig
from .training_controller import TrainingController
from .export_handler import ExportHandler
from .file_manager import FileManager
# Defer WandB import to avoid 2+ second startup penalty
# from .wandb_integration import WandBIntegration
from .error_handler import get_error_handler, setup_global_error_handling


class AFMTrainerGUI:
    """Main GUI application for AFM Trainer."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AFM Trainer - Apple Foundation Models Adapter Training")
        self.root.geometry("900x700")
        
        # Apply modern theme
        self.apply_theme()
        
        # Performance optimization: reduce unnecessary redraws
        self.root.configure(background='#2d2d2d' if SV_TTK_AVAILABLE else '#f0f0f0')
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.training_controller = TrainingController()
        self.export_handler = ExportHandler()
        self.file_manager = FileManager()
        self.wandb_integration = None  # Lazy load when needed
        self.error_handler = get_error_handler()
        
        # Set up error handling callback
        self.error_handler.set_gui_callback(self.handle_error_message)
        
        # State variables
        self.training_in_progress = False
        self.current_toolkit_dir = tk.StringVar()
        self.current_output_dir = tk.StringVar()
        
        # Set default toolkit directory if exists
        default_toolkit = Path.cwd() / ".adapter_training_toolkit_v26_0_0"
        if default_toolkit.exists():
            self.current_toolkit_dir.set(str(default_toolkit))
            
        # Set default output directory
        self.current_output_dir.set(str(Path.cwd() / "output"))
        
        self.setup_ui()
        self.setup_logging()
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)
        
        # Set up keyboard shortcuts
        self.root.bind('<Control-q>', lambda e: self.quit_application())
        self.root.bind('<Command-q>', lambda e: self.quit_application())  # macOS
        
    def apply_theme(self):
        """Apply modern theme to the GUI."""
        # Check for performance mode environment variable
        performance_mode = os.getenv('AFM_TRAINER_PERFORMANCE_MODE', '').lower() == 'true'
        
        if SV_TTK_AVAILABLE and not performance_mode:
            # Apply Sun Valley theme (modern forest-like appearance)
            # Choose dark theme for a more modern look
            sv_ttk.set_theme("dark")
            # Defer logging to avoid blocking
            if not hasattr(self, '_theme_logged'):
                self.root.after_idle(self._log_theme_applied)
                self._theme_logged = True
        else:
            # High-performance fallback theme
            style = ttk.Style()
            
            # Use the fastest available theme
            available_themes = style.theme_names()
            if performance_mode:
                # Use fastest theme for performance mode
                if 'clam' in available_themes:
                    style.theme_use('clam')
                else:
                    style.theme_use('default')
                
                # Minimal styling for speed
                style.configure("TNotebook.Tab", padding=[8, 4])
                style.configure("Accent.TButton", foreground="white", background="#0066cc")
                
                if hasattr(self, 'logger'):
                    self.root.after_idle(lambda: self.logger.info("Applied high-performance theme"))
            else:
                # Enhanced theme without sv-ttk
                if 'vista' in available_themes:
                    style.theme_use('vista')
                elif 'aqua' in available_themes:  # macOS
                    style.theme_use('aqua') 
                elif 'clam' in available_themes:
                    style.theme_use('clam')
                else:
                    style.theme_use('default')
                
                # Enhanced styling for better appearance
                style.configure("TFrame", background="#f8f8f8")
                style.configure("TLabel", background="#f8f8f8", foreground="#333333")
                style.configure("TLabelFrame", background="#f8f8f8", foreground="#333333")
                style.configure("TLabelFrame.Label", background="#f8f8f8", foreground="#2e7d32", font=("Arial", 9, "bold"))
                
                # Button styling
                style.configure("TButton", 
                              background="#e8e8e8", 
                              foreground="#333333",
                              font=("Arial", 9))
                style.map("TButton",
                         background=[('active', '#d8d8d8'), ('pressed', '#c8c8c8')])
                
                # Accent button for primary actions
                style.configure("Accent.TButton", 
                              background="#2e7d32", 
                              foreground="white",
                              font=("Arial", 9, "bold"))
                style.map("Accent.TButton",
                         background=[('active', '#1b5e20'), ('pressed', '#0d3f14')])
                
                # Entry styling
                style.configure("TEntry",
                              fieldbackground="white",
                              bordercolor="#cccccc",
                              focuscolor="#2e7d32")
                
                # Notebook styling
                style.configure("TNotebook", background="#f8f8f8")
                style.configure("TNotebook.Tab", 
                              background="#e8e8e8",
                              foreground="#333333",
                              padding=[10, 6])
                style.map("TNotebook.Tab",
                         background=[('selected', '#2e7d32'), ('active', '#d8d8d8')],
                         foreground=[('selected', 'white')])
                
                # Progressbar styling
                style.configure("TProgressbar",
                              background="#2e7d32",
                              troughcolor="#e8e8e8")
            
            if hasattr(self, 'logger'):
                self.root.after_idle(lambda: self.logger.info("Applied custom enhanced theme (sv-ttk not available)"))
                
    def _log_theme_applied(self):
        """Log theme application after GUI is ready."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Applied Sun Valley dark theme")
        
    def _get_wandb_integration(self):
        """Lazy load WandB integration to avoid startup penalty."""
        if self.wandb_integration is None:
            try:
                from .wandb_integration import WandBIntegration
                self.wandb_integration = WandBIntegration()
            except ImportError as e:
                print(f"Warning: Could not import WandB integration: {e}")
                # Create a dummy WandB integration
                self.wandb_integration = type('DummyWandB', (), {
                    'is_available': lambda: False,
                    'finish': lambda: None
                })()
        return self.wandb_integration
        
                
    def change_theme(self, event=None):
        """Change between light and dark themes."""
        if SV_TTK_AVAILABLE:
            theme = self.theme_var.get()
            sv_ttk.set_theme(theme)
            self.log_message(f"Theme changed to: {theme.capitalize()}", "INFO")
            
        
    def setup_ui(self):
        """Setup the main user interface."""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Header
        self.create_header(main_frame)
        
        # Create notebook for tabs with optimized performance
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Optimize tab switching performance
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
        # Create tabs (simplified approach for stability)
        self.create_setup_tab()
        self.create_training_tab()
        self.create_export_tab()
        self.create_monitor_tab()
        
        # Bottom control panel
        self.create_control_panel(main_frame)
        
    def create_header(self, parent):
        """Create the header section."""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        header_frame.columnconfigure(1, weight=1)
        
        # Create a styled header with icon
        header_container = ttk.Frame(header_frame, style="Header.TFrame")
        header_container.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Title with icon
        title_frame = ttk.Frame(header_container)
        title_frame.pack(anchor="w", pady=5)
        
        # App icon/emoji
        icon_label = ttk.Label(title_frame, text="🧠", font=("Arial", 20))
        icon_label.pack(side="left", padx=(0, 10))
        
        title_label = ttk.Label(title_frame, text="AFM Trainer", 
                               font=("Arial", 18, "bold"))
        title_label.pack(side="left")
        
        # Subtitle with better styling
        subtitle_label = ttk.Label(header_container, 
                                  text="🍎 Apple Foundation Models Adapter Training Toolkit GUI",
                                  font=("Arial", 11))
        subtitle_label.pack(anchor="w", pady=(0, 5))
        
        # Version info and theme toggle
        info_frame = ttk.Frame(header_container)
        info_frame.pack(anchor="w", fill="x")
        
        version_label = ttk.Label(info_frame,
                                 text="v0.1.0 • Modern GUI for LoRA Adapter Training",
                                 font=("Arial", 9))
        version_label.pack(side="left")
        
        # Theme toggle button (if sv-ttk is available and not in performance mode)
        performance_mode = os.getenv('AFM_TRAINER_PERFORMANCE_MODE', '').lower() == 'true'
        if SV_TTK_AVAILABLE and not performance_mode:
            theme_frame = ttk.Frame(info_frame)
            theme_frame.pack(side="right")
            
            ttk.Label(theme_frame, text="Theme:", font=("Arial", 9)).pack(side="left", padx=(10, 5))
            
            self.theme_var = tk.StringVar(value="dark")
            theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var,
                                     values=["dark", "light"], width=8, state="readonly")
            theme_combo.pack(side="left")
            theme_combo.bind("<<ComboboxSelected>>", self.change_theme)
        elif performance_mode:
            # Show performance mode indicator
            perf_frame = ttk.Frame(info_frame)
            perf_frame.pack(side="right")
            ttk.Label(perf_frame, text="⚡ Performance Mode", font=("Arial", 9, "bold"), 
                     foreground="green").pack(side="left", padx=(10, 0))
    
    def _on_tab_changed(self, event):
        """Optimized tab change handler using update_idletasks for better performance."""
        # Use update_idletasks instead of update for much faster tab switching
        self.root.update_idletasks()
        
    def create_setup_tab(self):
        """Create the setup and configuration tab."""
        setup_frame = ttk.Frame(self.notebook)
        self.notebook.add(setup_frame, text="Setup")
        
        # Toolkit directory selection
        toolkit_group = ttk.LabelFrame(setup_frame, text="🔧 Toolkit Configuration", padding="10")
        toolkit_group.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(toolkit_group, text="Toolkit Directory:", font=("Arial", 9, "bold")).pack(anchor="w")
        warning_label = ttk.Label(toolkit_group, text="⚠️ Requires Apple Developer Program entitlements and must be downloaded directly from Apple", 
                                 font=("Arial", 10, "bold"), foreground="red")
        warning_label.pack(anchor="w", pady=(0, 8))
        toolkit_dir_frame = ttk.Frame(toolkit_group)
        toolkit_dir_frame.pack(fill="x", pady=5)
        
        self.toolkit_dir_entry = ttk.Entry(toolkit_dir_frame, textvariable=self.current_toolkit_dir)
        self.toolkit_dir_entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(toolkit_dir_frame, text="Browse", 
                  command=self.browse_toolkit_dir).pack(side="right", padx=(5, 0))
        
        # Dataset configuration
        dataset_group = ttk.LabelFrame(setup_frame, text="📊 Dataset Configuration", padding="10")
        dataset_group.pack(fill="x", padx=10, pady=5)
        
        # Training data
        ttk.Label(dataset_group, text="Training Data (JSONL):", font=("Arial", 9, "bold")).pack(anchor="w")
        train_frame = ttk.Frame(dataset_group)
        train_frame.pack(fill="x", pady=2)
        
        self.train_data_var = tk.StringVar()
        self.train_data_entry = ttk.Entry(train_frame, textvariable=self.train_data_var)
        self.train_data_entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(train_frame, text="Browse", 
                  command=lambda: self.browse_file("Training Data", self.train_data_var, 
                                                  [("JSONL files", "*.jsonl")])).pack(side="right", padx=(5, 0))
        
        # Evaluation data
        ttk.Label(dataset_group, text="Evaluation Data (JSONL, optional):", font=("Arial", 9, "bold")).pack(anchor="w", pady=(10, 0))
        eval_frame = ttk.Frame(dataset_group)
        eval_frame.pack(fill="x", pady=2)
        
        self.eval_data_var = tk.StringVar()
        self.eval_data_entry = ttk.Entry(eval_frame, textvariable=self.eval_data_var)
        self.eval_data_entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(eval_frame, text="Browse", 
                  command=lambda: self.browse_file("Evaluation Data", self.eval_data_var, 
                                                  [("JSONL files", "*.jsonl")])).pack(side="right", padx=(5, 0))
        
        # Output directory
        output_group = ttk.LabelFrame(setup_frame, text="📁 Output Configuration", padding="10")
        output_group.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(output_group, text="Output Directory:", font=("Arial", 9, "bold")).pack(anchor="w")
        output_frame = ttk.Frame(output_group)
        output_frame.pack(fill="x", pady=5)
        
        self.output_dir_entry = ttk.Entry(output_frame, textvariable=self.current_output_dir)
        self.output_dir_entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(output_frame, text="Browse", 
                  command=self.browse_output_dir).pack(side="right", padx=(5, 0))
        
    def create_training_tab(self):
        """Create the training configuration tab."""
        training_frame = ttk.Frame(self.notebook)
        self.notebook.add(training_frame, text="Training")
        
        # Create optimized scrollable frame for training options
        container = ttk.Frame(training_frame)
        container.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Optimize configure binding - only update when needed
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        scrollable_frame.bind("<Configure>", on_frame_configure)
        
        # Create window with better sizing
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def on_canvas_configure(event):
            # Update scrollable frame width to match canvas width
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # Bind mouse wheel events
        canvas.bind("<MouseWheel>", on_mousewheel)  # Windows
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux
        
        # Pack with better configuration
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Basic training parameters
        basic_group = ttk.LabelFrame(scrollable_frame, text="⚙️ Basic Parameters", padding="10")
        basic_group.pack(fill="x", padx=10, pady=5)
        
        # Epochs
        epochs_frame = ttk.Frame(basic_group)
        epochs_frame.pack(fill="x", pady=2)
        ttk.Label(epochs_frame, text="Epochs:", width=20).pack(side="left")
        self.epochs_var = tk.StringVar(value="2")
        ttk.Entry(epochs_frame, textvariable=self.epochs_var, width=10).pack(side="left")
        ttk.Label(epochs_frame, text="Number of training passes over the dataset").pack(side="left", padx=(10, 0))
        
        # Learning rate
        lr_frame = ttk.Frame(basic_group)
        lr_frame.pack(fill="x", pady=2)
        ttk.Label(lr_frame, text="Learning Rate:", width=20).pack(side="left")
        self.lr_var = tk.StringVar(value="1e-4")
        ttk.Entry(lr_frame, textvariable=self.lr_var, width=10).pack(side="left")
        ttk.Label(lr_frame, text="Initial step size for parameter updates").pack(side="left", padx=(10, 0))
        
        # Batch size
        batch_frame = ttk.Frame(basic_group)
        batch_frame.pack(fill="x", pady=2)
        ttk.Label(batch_frame, text="Batch Size:", width=20).pack(side="left")
        self.batch_size_var = tk.StringVar(value="4")
        ttk.Entry(batch_frame, textvariable=self.batch_size_var, width=10).pack(side="left")
        ttk.Label(batch_frame, text="Number of samples per training batch").pack(side="left", padx=(10, 0))
        
        # Advanced parameters
        advanced_group = ttk.LabelFrame(scrollable_frame, text="🔬 Advanced Parameters", padding="10")
        advanced_group.pack(fill="x", padx=10, pady=5)
        
        # Warmup epochs
        warmup_frame = ttk.Frame(advanced_group)
        warmup_frame.pack(fill="x", pady=2)
        ttk.Label(warmup_frame, text="Warmup Epochs:", width=20).pack(side="left")
        self.warmup_var = tk.StringVar(value="1")
        ttk.Entry(warmup_frame, textvariable=self.warmup_var, width=10).pack(side="left")
        
        # Gradient accumulation
        grad_acc_frame = ttk.Frame(advanced_group)
        grad_acc_frame.pack(fill="x", pady=2)
        ttk.Label(grad_acc_frame, text="Grad Accumulation:", width=20).pack(side="left")
        self.grad_acc_var = tk.StringVar(value="1")
        ttk.Entry(grad_acc_frame, textvariable=self.grad_acc_var, width=10).pack(side="left")
        
        # Weight decay
        weight_decay_frame = ttk.Frame(advanced_group)
        weight_decay_frame.pack(fill="x", pady=2)
        ttk.Label(weight_decay_frame, text="Weight Decay:", width=20).pack(side="left")
        self.weight_decay_var = tk.StringVar(value="1e-2")
        ttk.Entry(weight_decay_frame, textvariable=self.weight_decay_var, width=10).pack(side="left")
        
        # Gradient clipping norm
        clip_grad_frame = ttk.Frame(advanced_group)
        clip_grad_frame.pack(fill="x", pady=2)
        ttk.Label(clip_grad_frame, text="Clip Grad Norm:", width=20).pack(side="left")
        self.clip_grad_norm_var = tk.StringVar(value="1.0")
        ttk.Entry(clip_grad_frame, textvariable=self.clip_grad_norm_var, width=10).pack(side="left")
        ttk.Label(clip_grad_frame, text="Gradient clipping for training stability (0.1-5.0)").pack(side="left", padx=(10, 0))
        
        # Loss update frequency
        loss_freq_frame = ttk.Frame(advanced_group)
        loss_freq_frame.pack(fill="x", pady=2)
        ttk.Label(loss_freq_frame, text="Loss Log Frequency:", width=20).pack(side="left")
        self.loss_update_frequency_var = tk.StringVar(value="3")
        ttk.Entry(loss_freq_frame, textvariable=self.loss_update_frequency_var, width=10).pack(side="left")
        ttk.Label(loss_freq_frame, text="How often to log loss values (steps)").pack(side="left", padx=(10, 0))
        
        # Precision
        precision_frame = ttk.Frame(advanced_group)
        precision_frame.pack(fill="x", pady=2)
        ttk.Label(precision_frame, text="Precision:", width=20).pack(side="left")
        self.precision_var = tk.StringVar(value="bf16-mixed")
        precision_combo = ttk.Combobox(precision_frame, textvariable=self.precision_var, 
                                      values=["f32", "bf16", "bf16-mixed", "f16-mixed"], width=15)
        precision_combo.pack(side="left")
        
        # Checkboxes for boolean options
        self.activation_checkpointing_var = tk.BooleanVar()
        ttk.Checkbutton(advanced_group, text="Enable Activation Checkpointing", 
                       variable=self.activation_checkpointing_var).pack(anchor="w", pady=2)
        
        self.compile_model_var = tk.BooleanVar()
        ttk.Checkbutton(advanced_group, text="Compile Model", 
                       variable=self.compile_model_var).pack(anchor="w", pady=2)
        
        # Draft model options
        draft_group = ttk.LabelFrame(scrollable_frame, text="🚀 Draft Model (Optional)", padding="10")
        draft_group.pack(fill="x", padx=10, pady=5)
        
        self.train_draft_var = tk.BooleanVar()
        ttk.Checkbutton(draft_group, text="Train Draft Model for Speculative Decoding", 
                       variable=self.train_draft_var).pack(anchor="w", pady=2)
        
        ttk.Label(draft_group, text="Improves inference speed but increases training time").pack(anchor="w", pady=2)
        
        # WandB integration
        wandb_group = ttk.LabelFrame(scrollable_frame, text="📈 WandB Integration (Optional)", padding="10")
        wandb_group.pack(fill="x", padx=10, pady=5)
        
        self.use_wandb_var = tk.BooleanVar()
        wandb_check = ttk.Checkbutton(wandb_group, text="Enable WandB Logging", 
                                     variable=self.use_wandb_var,
                                     command=self._on_wandb_toggle)
        wandb_check.pack(anchor="w", pady=2)
        
        # WandB status
        self.wandb_status_label = ttk.Label(wandb_group, text="WandB status will be checked when enabled")
        self.wandb_status_label.pack(anchor="w", pady=2)
        
        # Initialize WandB status (completely deferred until WandB tab is accessed)
        self.wandb_status_cache = None
        self.wandb_status_checked = False
        # Don't check WandB status on startup - only when user toggles it
        # self._schedule_wandb_status_update()
        
    def create_export_tab(self):
        """Create the export configuration tab."""
        export_frame = ttk.Frame(self.notebook)
        self.notebook.add(export_frame, text="Export")
        
        # Adapter metadata
        metadata_group = ttk.LabelFrame(export_frame, text="📦 Adapter Metadata", padding="10")
        metadata_group.pack(fill="x", padx=10, pady=5)
        
        # Adapter name
        name_frame = ttk.Frame(metadata_group)
        name_frame.pack(fill="x", pady=2)
        ttk.Label(name_frame, text="Adapter Name:", width=15).pack(side="left")
        self.adapter_name_var = tk.StringVar(value="my_adapter")
        ttk.Entry(name_frame, textvariable=self.adapter_name_var).pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        # Author
        author_frame = ttk.Frame(metadata_group)
        author_frame.pack(fill="x", pady=2)
        ttk.Label(author_frame, text="Author:", width=15).pack(side="left")
        self.author_var = tk.StringVar(value="3P developer")
        ttk.Entry(author_frame, textvariable=self.author_var).pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        # Description
        desc_frame = ttk.Frame(metadata_group)
        desc_frame.pack(fill="x", pady=2)
        ttk.Label(desc_frame, text="Description:", width=15).pack(side="left", anchor="n")
        self.description_text = tk.Text(desc_frame, height=4, wrap="word")
        self.description_text.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        # License
        license_frame = ttk.Frame(metadata_group)
        license_frame.pack(fill="x", pady=2)
        ttk.Label(license_frame, text="License:", width=15).pack(side="left")
        self.license_var = tk.StringVar()
        ttk.Entry(license_frame, textvariable=self.license_var).pack(side="left", fill="x", expand=True, padx=(5, 0))
        
    def create_monitor_tab(self):
        """Create the monitoring and logs tab."""
        monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitor_frame, text="Monitor")
        
        # Progress section
        progress_group = ttk.LabelFrame(monitor_frame, text="Training Progress", padding="10")
        progress_group.pack(fill="x", padx=10, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_group, mode='determinate')
        self.progress_bar.pack(fill="x", pady=2)
        
        self.progress_label = ttk.Label(progress_group, text="Ready to start training")
        self.progress_label.pack(anchor="w", pady=2)
        
        # Log output
        log_group = ttk.LabelFrame(monitor_frame, text="Training Logs", padding="10")
        log_group.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_group, wrap=tk.WORD, height=20)
        self.log_text.pack(fill="both", expand=True)
        
        # Clear logs button
        ttk.Button(log_group, text="Clear Logs", command=self.clear_logs).pack(anchor="e", pady=(5, 0))
        
    def create_control_panel(self, parent):
        """Create the bottom control panel."""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        control_frame.columnconfigure(0, weight=1)
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side="right")
        
        # Validate button
        self.validate_btn = ttk.Button(button_frame, text="✓ Validate Setup", 
                                      command=self.validate_setup)
        self.validate_btn.pack(side="left", padx=(0, 5))
        
        # Start training button
        self.start_btn = ttk.Button(button_frame, text="🚀 Start Training", 
                                   command=self.start_training, style="Accent.TButton")
        self.start_btn.pack(side="left", padx=(0, 5))
        
        # Stop training button
        self.stop_btn = ttk.Button(button_frame, text="⏹ Stop Training", 
                                  command=self.stop_training, state="disabled")
        self.stop_btn.pack(side="left", padx=(0, 5))
        
        # Export button
        self.export_btn = ttk.Button(button_frame, text="📦 Export Adapter", 
                                    command=self.export_adapter, state="disabled")
        self.export_btn.pack(side="left", padx=(0, 5))
        
        # Quit button
        self.quit_btn = ttk.Button(button_frame, text="🚪 Quit (Ctrl+Q)", 
                                  command=self.quit_application)
        self.quit_btn.pack(side="left")
        
        # Status label
        self.status_label = ttk.Label(control_frame, text="Ready", foreground="green")
        self.status_label.pack(side="left")
        
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def browse_toolkit_dir(self):
        """Browse for toolkit directory."""
        directory = filedialog.askdirectory(
            title="Select Apple Foundation Models Adapter Training Toolkit Directory",
            initialdir=self.current_toolkit_dir.get() or str(Path.cwd())
        )
        if directory:
            self.current_toolkit_dir.set(directory)
            # Update .gitignore to exclude toolkit directory
            try:
                self.file_manager.update_gitignore(str(Path.cwd()), directory)
                self.log_message("Updated .gitignore to exclude toolkit directory", "INFO")
            except Exception as e:
                self.log_message(f"Warning: Could not update .gitignore: {str(e)}", "WARNING")
            
    def browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.current_output_dir.get() or str(Path.cwd())
        )
        if directory:
            self.current_output_dir.set(directory)
            
    def browse_file(self, title: str, var: tk.StringVar, filetypes: list):
        """Browse for a file."""
        filename = filedialog.askopenfilename(
            title=f"Select {title}",
            filetypes=filetypes + [("All files", "*.*")]
        )
        if filename:
            var.set(filename)
            
    def validate_setup(self):
        """Validate the current setup configuration."""
        self.log_message("Validating setup...")
        
        try:
            # Validate toolkit directory
            toolkit_dir = Path(self.current_toolkit_dir.get())
            if not toolkit_dir.exists():
                raise ValueError("Toolkit directory does not exist")
                
            # Check for required toolkit files
            required_files = ["examples", "export", "assets", "requirements.txt"]
            for req_file in required_files:
                if not (toolkit_dir / req_file).exists():
                    raise ValueError(f"Missing required toolkit component: {req_file}")
                    
            # Validate training data
            train_data = self.train_data_var.get()
            if not train_data:
                raise ValueError("Training data file is required")
                
            if not Path(train_data).exists():
                raise ValueError("Training data file does not exist")
                
            # Validate eval data if provided
            eval_data = self.eval_data_var.get()
            if eval_data and not Path(eval_data).exists():
                raise ValueError("Evaluation data file does not exist")
                
            # Validate output directory
            output_dir = Path(self.current_output_dir.get())
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Validate numeric parameters
            try:
                epochs = int(self.epochs_var.get())
                lr = float(self.lr_var.get())
                batch_size = int(self.batch_size_var.get())
                clip_grad_norm = float(self.clip_grad_norm_var.get())
                loss_update_freq = int(self.loss_update_frequency_var.get())
                
                # Validate parameter ranges
                if epochs <= 0:
                    raise ValueError("Epochs must be greater than 0")
                if lr <= 0:
                    raise ValueError("Learning rate must be greater than 0") 
                if batch_size <= 0:
                    raise ValueError("Batch size must be greater than 0")
                if clip_grad_norm <= 0 or clip_grad_norm > 10:
                    raise ValueError("Gradient clipping norm must be between 0 and 10")
                if loss_update_freq <= 0:
                    raise ValueError("Loss update frequency must be greater than 0")
                    
            except ValueError as ve:
                if "invalid literal" in str(ve):
                    raise ValueError("Invalid numeric parameter values")
                else:
                    raise ve
                
            self.log_message("✓ Setup validation passed!", "SUCCESS")
            self.status_label.config(text="Setup validated", foreground="green")
            self.start_btn.config(state="normal")
            
        except Exception as e:
            self.log_message(f"✗ Setup validation failed: {str(e)}", "ERROR")
            self.status_label.config(text="Setup invalid", foreground="red")
            self.start_btn.config(state="disabled")
            messagebox.showerror("Validation Error", str(e))
            
    def start_training(self):
        """Start the training process."""
        if self.training_in_progress:
            return
            
        self.log_message("Starting training process...")
        self.training_in_progress = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.export_btn.config(state="disabled")
        self.status_label.config(text="Training in progress...", foreground="orange")
        
        # Switch to monitor tab
        self.notebook.select(3)  # Monitor tab
        
        # Start training in separate thread
        training_thread = threading.Thread(target=self._run_training)
        training_thread.daemon = True
        training_thread.start()
        
    def _run_training(self):
        """Run training in background thread."""
        try:
            # Collect training configuration
            config = {
                'toolkit_dir': self.current_toolkit_dir.get(),
                'train_data': self.train_data_var.get(),
                'eval_data': self.eval_data_var.get() or None,
                'output_dir': self.current_output_dir.get(),
                'epochs': int(self.epochs_var.get()),
                'learning_rate': float(self.lr_var.get()),
                'batch_size': int(self.batch_size_var.get()),
                'warmup_epochs': int(self.warmup_var.get()),
                'gradient_accumulation_steps': int(self.grad_acc_var.get()),
                'weight_decay': float(self.weight_decay_var.get()),
                'clip_grad_norm': float(self.clip_grad_norm_var.get()),
                'loss_update_frequency': int(self.loss_update_frequency_var.get()),
                'precision': self.precision_var.get(),
                'activation_checkpointing': self.activation_checkpointing_var.get(),
                'compile_model': self.compile_model_var.get(),
                'train_draft': self.train_draft_var.get(),
                'use_wandb': self.use_wandb_var.get(),
            }
            
            # Run training
            success = self.training_controller.run_training(
                config, 
                progress_callback=self._update_progress,
                log_callback=self._log_callback
            )
            
            if success:
                self.root.after(0, self._training_completed_success)
            else:
                self.root.after(0, self._training_completed_error)
                
        except Exception as e:
            self.root.after(0, lambda: self._training_completed_error(str(e)))
            
    def _update_progress(self, progress: float, message: str):
        """Update progress bar and message."""
        self.root.after(0, lambda: self._update_progress_ui(progress, message))
        
    def _update_progress_ui(self, progress: float, message: str):
        """Update progress UI elements."""
        self.progress_bar['value'] = progress * 100
        self.progress_label.config(text=message)
        
    def _log_callback(self, message: str):
        """Callback for training and export log messages."""
        self.root.after(0, lambda: self.log_message(message))
        
    def _training_completed_success(self):
        """Handle successful training completion."""
        self.training_in_progress = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.export_btn.config(state="normal")
        self.status_label.config(text="Training completed", foreground="green")
        
        # Add clear completion separator
        self.log_message("=" * 50, "SUCCESS")
        self.log_message("🎯 TRAINING COMPLETED SUCCESSFULLY!", "SUCCESS")
        
        # Show appropriate completion message based on draft training
        if self.train_draft_var.get():
            self.log_message("✅ Main adapter training completed", "SUCCESS")
            self.log_message("✅ Draft model training completed", "SUCCESS") 
            self.log_message("📦 Ready to export adapter with speculative decoding support", "SUCCESS")
            completion_msg = "Training completed successfully!\n\n✅ Main adapter checkpoints saved\n✅ Draft model checkpoints saved\n🚀 Speculative decoding enabled\n📦 Ready to export .fmadapter file\n\nClick 'Export Adapter' to create your deployment package."
        else:
            self.log_message("✅ Adapter training completed", "SUCCESS")
            self.log_message("📦 Ready to export adapter - click 'Export Adapter' button", "SUCCESS")
            completion_msg = "Training completed successfully!\n\n✅ Adapter checkpoints saved\n📦 Ready to export .fmadapter file\n\nClick 'Export Adapter' to create your deployment package."
            
        self.log_message("=" * 50, "SUCCESS")
        
        messagebox.showinfo("Training Complete", completion_msg)
        
    def _training_completed_error(self, error_msg: str = None):
        """Handle training completion with error."""
        self.training_in_progress = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="Training failed", foreground="red")
        
        if error_msg:
            self.log_message(f"✗ Training failed: {error_msg}", "ERROR")
            messagebox.showerror("Training Failed", f"Training failed: {error_msg}")
        else:
            self.log_message("✗ Training failed", "ERROR")
            messagebox.showerror("Training Failed", "Training failed. Check logs for details.")
            
    def stop_training(self):
        """Stop the training process."""
        if not self.training_in_progress:
            return
            
        if messagebox.askyesno("Stop Training", "Are you sure you want to stop the training process?"):
            self.training_controller.stop_training()
            self.log_message("Training stopped by user")
            self._training_completed_error()
            
    def export_adapter(self):
        """Export the trained adapter."""
        try:
            # Switch to monitor tab to show export progress
            self.notebook.select(3)  # Monitor tab
            
            self.log_message("=" * 50, "INFO")
            self.log_message("🚀 STARTING ADAPTER EXPORT", "INFO") 
            self.log_message("=" * 50, "INFO")
            
            # Collect export configuration
            export_config = {
                'output_dir': self.current_output_dir.get(),
                'adapter_name': self.adapter_name_var.get(),
                'author': self.author_var.get(),
                'description': self.description_text.get("1.0", "end-1c"),
                'license': self.license_var.get(),
                'toolkit_dir': self.current_toolkit_dir.get(),
            }
            
            # Disable export button during export
            self.export_btn.config(state="disabled")
            self.status_label.config(text="Exporting adapter...", foreground="orange")
            
            # Set progress bar to indeterminate mode for export
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start()
            self.progress_label.config(text="Exporting adapter...")
            
            # Run export with log callback
            success = self.export_handler.export_adapter(export_config, self._log_callback)
            
            if success:
                self.log_message("=" * 50, "SUCCESS")
                self.log_message("🎉 ADAPTER EXPORT COMPLETED SUCCESSFULLY!", "SUCCESS")
                self.log_message("=" * 50, "SUCCESS")
                self.status_label.config(text="Export completed", foreground="green")
                
                # Stop progress bar and set completion
                self.progress_bar.stop()
                self.progress_bar.config(mode='determinate')
                self.progress_bar['value'] = 100
                self.progress_label.config(text="Export completed successfully")
                
                # Show completion message
                adapter_path = f"{export_config['output_dir']}/{export_config['adapter_name']}.fmadapter"
                messagebox.showinfo(
                    "Export Complete", 
                    f"Adapter exported successfully!\n\nLocation: {adapter_path}\n\nYou can now use this .fmadapter file in your iOS/macOS applications."
                )
            else:
                raise Exception("Export failed")
                
        except Exception as e:
            self.log_message("=" * 50, "ERROR")
            self.log_message(f"💥 ADAPTER EXPORT FAILED", "ERROR")
            self.log_message(f"Error: {str(e)}", "ERROR")
            self.log_message("=" * 50, "ERROR")
            self.status_label.config(text="Export failed", foreground="red")
            
            # Stop progress bar on error
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
            self.progress_bar['value'] = 0
            self.progress_label.config(text="Export failed")
            
            messagebox.showerror("Export Failed", f"Export failed: {str(e)}")
        finally:
            # Re-enable export button
            self.export_btn.config(state="normal")
            
    def log_message(self, message: str, level: str = "INFO"):
        """Add a message to the log display."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        if level == "SUCCESS":
            prefix = "✅"
        elif level == "ERROR":
            prefix = "❌"
        elif level == "WARNING":
            prefix = "⚠️"
        else:
            prefix = "ℹ️"
            
        # Format log line differently for separators
        if message.startswith("="):
            log_line = f"{message}\n"
        else:
            log_line = f"[{timestamp}] {prefix} {message}\n"
        
        # Only log to GUI if Monitor tab has been created
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text.insert(tk.END, log_line)
            self.log_text.see(tk.END)
            # Ensure the GUI updates
            self.root.update_idletasks()
        else:
            # Store messages for later display or just print to console
            print(log_line.strip())  # Fallback to console logging
        
    def clear_logs(self):
        """Clear the log display."""
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text.delete(1.0, tk.END)
        
    def handle_error_message(self, message: str, level: str):
        """
        Handle error messages from the error handler.
        
        Args:
            message: Error message
            level: Error level (ERROR, WARNING, INFO)
        """
        self.log_message(message, level)
        
        if level == "ERROR":
            # Show error dialog for critical errors
            messagebox.showerror("Error", message)
            
    def _on_wandb_toggle(self):
        """Handle WandB checkbox toggle."""
        # Only check WandB status when user actually toggles it
        self._schedule_wandb_status_update()
        
    def _schedule_wandb_status_update(self):
        """Schedule WandB status update to run after UI is ready."""
        # Defer the status check to avoid blocking the UI
        self.root.after(100, self._update_wandb_status_deferred)
        
    def _update_wandb_status_deferred(self):
        """Update WandB status with caching and background checking."""
        # Show initial loading message
        if not self.wandb_status_checked:
            self.wandb_status_label.config(
                text="Checking WandB status...",
                foreground="gray"
            )
            # Do the actual check in background
            self.root.after(10, self._check_wandb_status_background)
        else:
            # Use cached result
            self._update_wandb_status_from_cache()
            
    def _check_wandb_status_background(self):
        """Check WandB status in background without blocking UI."""
        try:
            wandb_integration = self._get_wandb_integration()
            if not wandb_integration.is_available():
                self.wandb_status_cache = {
                    'available': False,
                    'text': "WandB not installed. Install with: pip install wandb",
                    'color': "orange"
                }
            else:
                # Quick check without full login verification to avoid blocking
                try:
                    import wandb
                    # Just check if wandb is importable and has basic config
                    if hasattr(wandb, 'api') and wandb.api.api_key:
                        self.wandb_status_cache = {
                            'available': True,
                            'text': "✓ WandB ready for logging",
                            'color': "green"
                        }
                    else:
                        self.wandb_status_cache = {
                            'available': True,
                            'text': "Please run 'wandb login' first",
                            'color': "red"
                        }
                except Exception:
                    self.wandb_status_cache = {
                        'available': True,
                        'text': "Please run 'wandb login' first",
                        'color': "red"
                    }
                    
        except Exception:
            self.wandb_status_cache = {
                'available': False,
                'text': "WandB status check failed",
                'color': "red"
            }
            
        self.wandb_status_checked = True
        self._update_wandb_status_from_cache()
        
    def _update_wandb_status_from_cache(self):
        """Update WandB status display from cached result."""
        if not self.wandb_status_cache:
            return
            
        if not self.wandb_status_cache['available']:
            self.wandb_status_label.config(
                text=self.wandb_status_cache['text'],
                foreground=self.wandb_status_cache['color']
            )
            self.use_wandb_var.set(False)
            return
            
        if self.use_wandb_var.get():
            self.wandb_status_label.config(
                text=self.wandb_status_cache['text'],
                foreground=self.wandb_status_cache['color']
            )
        else:
            self.wandb_status_label.config(
                text="WandB logging disabled",
                foreground="gray"
            )
            
    def _update_wandb_status(self):
        """Legacy method - redirect to deferred version."""
        if not self.wandb_status_checked:
            self._schedule_wandb_status_update()
        else:
            self._update_wandb_status_from_cache()
            
    def quit_application(self):
        """Quit the application gracefully."""
        try:
            # Check if training is in progress
            if self.training_in_progress:
                response = messagebox.askyesno(
                    "Training in Progress",
                    "Training is currently running. Do you want to stop training and quit?\n\nThis will terminate the training process."
                )
                if not response:
                    return  # User cancelled
                    
                # Stop training process
                self.log_message("🛑 Stopping training due to application quit...", "WARNING")
                self.training_controller.stop_training()
                
            # Ask about environment cleanup
            cleanup_response = messagebox.askyesno(
                "Environment Cleanup",
                "Do you want to clean up the UV environment?\n\n" +
                "This will:\n" +
                "• Clean UV package cache (~800MB)\n" +
                "• Remove .venv directory\n" +
                "• Remove UV lock and config files\n" +
                "• Free up approximately 1GB of disk space\n\n" +
                "The environment will be recreated automatically when you restart AFM Trainer.\n\n" +
                "Clean up environment now?",
                icon="question"
            )
            
            # Clean up resources
            self.log_message("🔄 Cleaning up resources...", "INFO")
            
            # Stop WandB if active
            if self.wandb_integration is not None:
                try:
                    self.wandb_integration.finish()
                except Exception as e:
                    self.logger.warning(f"Error finishing WandB: {e}")
                    
            # Stop any background monitoring
            if hasattr(self.training_controller, 'stop_log_monitoring'):
                self.training_controller.stop_log_monitoring()
                
            # Handle environment cleanup
            if cleanup_response:
                self._cleanup_environment()
            else:
                self._show_manual_cleanup_instructions()
                
            self.log_message("✅ Application shutdown complete", "SUCCESS")
            
            # Small delay to let the log message display
            self.root.after(100, self._force_quit)
            
        except Exception as e:
            self.logger.error(f"Error during application shutdown: {e}")
            # Force quit even if cleanup fails
            self._force_quit()
            
    def _cleanup_environment(self):
        """Clean up the UV environment - performs all manual cleanup actions."""
        try:
            self.log_message("🧹 Starting comprehensive environment cleanup...", "INFO")
            
            # 1. Clean UV cache
            self.log_message("🗑️ Cleaning UV cache...", "INFO")
            try:
                import subprocess
                result = subprocess.run(
                    ['uv', 'cache', 'clean'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    self.log_message("✅ UV cache cleaned successfully", "SUCCESS")
                    if result.stdout.strip():
                        self.log_message(f"   {result.stdout.strip()}", "INFO")
                else:
                    self.log_message(f"⚠️ UV cache clean warning: {result.stderr.strip()}", "WARNING")
                    
            except subprocess.TimeoutExpired:
                self.log_message("⚠️ UV cache cleanup timed out", "WARNING")
            except FileNotFoundError:
                self.log_message("ℹ️ UV not found, skipping cache cleanup", "INFO")
            
            # 2. Remove .venv directory
            self.log_message("📁 Removing project virtual environment (.venv)...", "INFO")
            venv_path = Path.cwd() / ".venv"
            if venv_path.exists():
                try:
                    import shutil
                    shutil.rmtree(venv_path)
                    self.log_message("✅ .venv directory removed successfully", "SUCCESS")
                except Exception as e:
                    self.log_message(f"⚠️ Failed to remove .venv: {str(e)}", "WARNING")
            else:
                self.log_message("ℹ️ .venv directory not found (already clean)", "INFO")
            
            # 3. Remove other UV-related files
            self.log_message("🧹 Cleaning additional UV files...", "INFO")
            cleanup_files = [
                Path.cwd() / "uv.lock",
                Path.cwd() / ".python-version",
                Path.cwd() / ".uv-cache"
            ]
            
            removed_count = 0
            for file_path in cleanup_files:
                try:
                    if file_path.exists():
                        if file_path.is_file():
                            file_path.unlink()
                        else:
                            import shutil
                            shutil.rmtree(file_path)
                        self.log_message(f"   ✅ Removed {file_path.name}", "SUCCESS")
                        removed_count += 1
                except Exception as e:
                    self.log_message(f"   ⚠️ Failed to remove {file_path.name}: {str(e)}", "WARNING")
            
            if removed_count == 0:
                self.log_message("ℹ️ No additional UV files found to clean", "INFO")
            
            # 4. Check disk space freed (approximation)
            self.log_message("📊 Environment cleanup completed", "SUCCESS")
            self.log_message("💡 Estimated space freed: ~800MB - 1GB", "INFO")
            self.log_message("🔄 Environment will be recreated on next startup", "INFO")
                
        except Exception as e:
            self.log_message(f"⚠️ Environment cleanup failed: {str(e)}", "WARNING")
            
    def _show_manual_cleanup_instructions(self):
        """Show manual cleanup instructions in GUI and console."""
        self.log_message("ℹ️ Environment cleanup skipped", "INFO")
        self.log_message("📋 Manual cleanup instructions shown in dialog", "INFO")
        
        # Show GUI dialog with cleanup instructions
        instructions_text = """To manually clean up the AFM Trainer environment later, run these commands:

🧹 Clean UV cache:
    uv cache clean

🗑️ Remove project dependencies:
    rm -rf .venv

📊 Check cache location/size:
    uv cache dir

💡 Tip: The cache will be recreated automatically when you next run AFM Trainer"""
        
        # Create custom dialog for cleanup instructions
        dialog = tk.Toplevel(self.root)
        dialog.title("Cleanup Instructions")
        dialog.geometry("520x420")  # Make wider and taller for buttons
        dialog.resizable(False, False)
        dialog.configure(bg="#ffffff")  # White background
        dialog.grab_set()  # Make it modal
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Header with icon
        header_frame = tk.Frame(dialog, bg="#f0f0f0", relief="ridge", bd=1)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        header_label = tk.Label(
            header_frame,
            text="🧹 CLEANUP INSTRUCTIONS",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0",
            fg="#333333"
        )
        header_label.pack(pady=10)
        
        # Instructions text
        text_frame = tk.Frame(dialog, bg="#ffffff")
        text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        
        instructions_display = tk.Text(
            text_frame,
            wrap="word",
            font=("Courier", 10),
            bg="#f8f8f8",
            fg="#000000",  # Black text
            relief="sunken",
            bd=1,
            padx=10,
            pady=10
        )
        instructions_display.pack(fill="both", expand=True)
        instructions_display.insert("1.0", instructions_text)
        instructions_display.config(state="disabled")  # Make read-only
        
        # Separator line
        separator = tk.Frame(dialog, height=2, bg="#cccccc")
        separator.pack(fill="x", padx=10, pady=5)
        
        # Button frame
        button_frame = tk.Frame(dialog, bg="#ffffff")
        button_frame.pack(fill="x", padx=20, pady=15)
        
        # Copy to clipboard button
        def copy_instructions():
            dialog.clipboard_clear()
            dialog.clipboard_append(instructions_text)
            copy_btn.config(text="✓ Copied!")
            dialog.after(2000, lambda: copy_btn.config(text="📋 Copy to Clipboard"))
        
        copy_btn = tk.Button(
            button_frame,
            text="📋 Copy to Clipboard",
            command=copy_instructions,
            font=("Arial", 9),
            bg="#e0e0e0",
            fg="#000000",
            activebackground="#d0d0d0",
            relief="raised",
            bd=2,
            width=18,
            height=1
        )
        copy_btn.grid(row=0, column=0, sticky="w")
        
        # Spacer to push OK button to the right
        button_frame.columnconfigure(1, weight=1)
        
        # OK button
        ok_btn = tk.Button(
            button_frame,
            text="OK",
            command=dialog.destroy,
            font=("Arial", 10, "bold"),
            bg="#e0e0e0",
            fg="#000000",
            activebackground="#d0d0d0",
            activeforeground="#000000",
            relief="raised",
            bd=2,
            width=8,
            height=1
        )
        ok_btn.grid(row=0, column=2, sticky="e")
        
        # Focus on OK button
        ok_btn.focus_set()
        
        # Handle Enter key
        dialog.bind('<Return>', lambda e: dialog.destroy())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        
        # Wait for dialog to close before continuing
        dialog.wait_window()
        
        # Also print to console for reference
        cleanup_instructions = """
┌─────────────────────────────────────────────────┐
│                 CLEANUP INSTRUCTIONS             │
├─────────────────────────────────────────────────┤
│ To manually clean up the AFM Trainer            │
│ environment later, run these commands:          │
│                                                 │
│ 🧹 Clean UV cache:                              │
│    uv cache clean                               │
│                                                 │
│ 🗑️ Remove project dependencies:                 │
│    rm -rf .venv                                 │
│                                                 │
│ 📊 Check cache location/size:                   │
│    uv cache dir                                 │
│                                                 │
│ 💡 Tip: The cache will be recreated             │
│    automatically when you next run AFM Trainer │
└─────────────────────────────────────────────────┘
"""
        print(cleanup_instructions)
        
    def _force_quit(self):
        """Force quit the application."""
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            # Ultimate fallback
            import sys
            sys.exit(0)


def main():
    """Main entry point for the application."""
    # Setup global error handling
    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "afm_trainer.log"
    setup_global_error_handling(str(log_file))
    
    root = tk.Tk()
    
    # The theme will be applied by the AFMTrainerGUI class
    app = AFMTrainerGUI(root)
    
    try:
        # Set window to center of screen
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")
        
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
        app.quit_application()
    except Exception as e:
        # Handle any unhandled exceptions
        error_handler = get_error_handler()
        error_handler.log_error(e, "Application runtime")
        print(f"❌ Application error: {e}")
        try:
            app.quit_application()
        except:
            pass
        raise
    finally:
        # Final cleanup
        print("\n👋 AFM Trainer shutdown complete")
        print("Thank you for using AFM Trainer!")


if __name__ == "__main__":
    main()