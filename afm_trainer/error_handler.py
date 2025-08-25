"""
Error handling utilities for AFM Trainer.
Provides comprehensive error handling, logging, and user-friendly error messages.
"""

import logging
import traceback
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import tkinter as tk
from tkinter import messagebox
import functools
import threading
import queue


class ErrorHandler:
    """Centralized error handling for the application."""
    
    def __init__(self, log_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.error_queue = queue.Queue()
        self.gui_callback: Optional[Callable] = None
        
        # Setup logging
        self.setup_logging(log_file)
        
    def setup_logging(self, log_file: Optional[str] = None):
        """
        Setup comprehensive logging configuration.
        
        Args:
            log_file: Optional log file path
        """
        # Create logs directory if it doesn't exist
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
        # Configure logging format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # File handler if log file specified
        handlers = [console_handler]
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
            
        # Configure root logger
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=handlers,
            force=True
        )
        
    def set_gui_callback(self, callback: Callable[[str, str], None]):
        """
        Set callback for GUI error display.
        
        Args:
            callback: Function to call with (error_message, error_level)
        """
        self.gui_callback = callback
        
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Handle uncaught exceptions.
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        error_msg = f"Uncaught exception: {exc_value}"
        traceback_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        self.logger.error(f"{error_msg}\n{traceback_str}")
        
        if self.gui_callback:
            self.gui_callback(f"Unexpected error: {exc_value}", "ERROR")
            
    def log_error(self, error: Exception, context: str = "", show_gui: bool = True):
        """
        Log an error with context.
        
        Args:
            error: Exception object
            context: Context information
            show_gui: Whether to show GUI error message
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)
        traceback_str = traceback.format_exc()
        
        self.logger.error(f"{error_msg}\n{traceback_str}")
        
        if show_gui and self.gui_callback:
            user_friendly_msg = self.get_user_friendly_message(error, context)
            self.gui_callback(user_friendly_msg, "ERROR")
            
    def log_warning(self, message: str, show_gui: bool = False):
        """
        Log a warning message.
        
        Args:
            message: Warning message
            show_gui: Whether to show GUI warning
        """
        self.logger.warning(message)
        
        if show_gui and self.gui_callback:
            self.gui_callback(message, "WARNING")
            
    def log_info(self, message: str, show_gui: bool = False):
        """
        Log an info message.
        
        Args:
            message: Info message
            show_gui: Whether to show GUI message
        """
        self.logger.info(message)
        
        if show_gui and self.gui_callback:
            self.gui_callback(message, "INFO")
            
    def get_user_friendly_message(self, error: Exception, context: str = "") -> str:
        """
        Convert technical error to user-friendly message.
        
        Args:
            error: Exception object
            context: Context information
            
        Returns:
            User-friendly error message
        """
        error_type = type(error).__name__
        error_str = str(error)
        
        # Common error patterns and their user-friendly messages
        if "FileNotFoundError" in error_type:
            if "train_data" in error_str or "eval_data" in error_str:
                return "Dataset file not found. Please check that the training/evaluation data files exist."
            elif "toolkit" in error_str or "examples" in error_str:
                return "Apple toolkit directory not found or incomplete. Please check the toolkit path."
            else:
                return f"Required file not found: {error_str}"
                
        elif "PermissionError" in error_type:
            return "Permission denied. Please check file/directory permissions or run with appropriate privileges."
            
        elif "subprocess.CalledProcessError" in error_type:
            return f"Training process failed. Check the logs for details. Error code: {getattr(error, 'returncode', 'unknown')}"
            
        elif "JSONDecodeError" in error_type:
            return "Invalid JSON format in dataset file. Please check your JSONL file format."
            
        elif "ImportError" in error_type or "ModuleNotFoundError" in error_type:
            missing_module = error_str.split("'")[1] if "'" in error_str else "unknown"
            return f"Missing required dependency: {missing_module}. Please install it using UV or pip."
            
        elif "CUDA" in error_str or "GPU" in error_str:
            return "GPU/CUDA error. The model may require more memory or CUDA may not be properly configured."
            
        elif "Memory" in error_str or "OOM" in error_str:
            return "Out of memory error. Try reducing batch size or enabling activation checkpointing."
            
        elif "ValidationError" in error_type:
            return f"Configuration validation failed: {error_str}"
            
        elif "TimeoutError" in error_type:
            return "Operation timed out. The process may be taking longer than expected."
            
        elif "ConnectionError" in error_type or "URLError" in error_type:
            return "Network connection error. Check your internet connection if using WandB or downloading models."
            
        elif "ValueError" in error_type:
            if "learning_rate" in error_str:
                return "Invalid learning rate. Please use a positive number."
            elif "batch_size" in error_str:
                return "Invalid batch size. Please use a positive integer."
            elif "epochs" in error_str:
                return "Invalid number of epochs. Please use a positive integer."
            else:
                return f"Invalid parameter value: {error_str}"
                
        elif "KeyError" in error_type:
            return f"Missing required configuration parameter: {error_str}"
            
        else:
            # Generic error message with context
            if context:
                return f"{context} failed: {error_str}"
            else:
                return f"Error: {error_str}"
                
    def wrap_with_error_handling(self, func: Callable, context: str = "") -> Callable:
        """
        Decorator to wrap functions with error handling.
        
        Args:
            func: Function to wrap
            context: Context for error reporting
            
        Returns:
            Wrapped function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.log_error(e, context or func.__name__)
                raise
        return wrapper
        
    def safe_execute(self, func: Callable, context: str = "", default_return=None):
        """
        Safely execute a function with error handling.
        
        Args:
            func: Function to execute
            context: Context for error reporting
            default_return: Default return value on error
            
        Returns:
            Function result or default_return on error
        """
        try:
            return func()
        except Exception as e:
            self.log_error(e, context)
            return default_return
            
    def create_error_dialog(self, parent, error_message: str, error_details: str = ""):
        """
        Create a detailed error dialog.
        
        Args:
            parent: Parent widget
            error_message: Main error message
            error_details: Detailed error information
        """
        dialog = tk.Toplevel(parent)
        dialog.title("Error")
        dialog.geometry("500x300")
        dialog.resizable(True, True)
        
        # Main error message
        msg_frame = tk.Frame(dialog, bg="white", relief="raised", bd=1)
        msg_frame.pack(fill="x", padx=10, pady=10)
        
        error_label = tk.Label(
            msg_frame, 
            text=error_message,
            wraplength=480,
            justify="left",
            bg="white",
            fg="red",
            font=("Arial", 10, "bold")
        )
        error_label.pack(padx=10, pady=10)
        
        # Details section if provided
        if error_details:
            details_frame = tk.LabelFrame(dialog, text="Details")
            details_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            details_text = tk.Text(
                details_frame,
                wrap="word",
                height=8,
                font=("Courier", 9)
            )
            details_text.pack(fill="both", expand=True, padx=5, pady=5)
            details_text.insert("1.0", error_details)
            details_text.config(state="disabled")
            
        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(
            button_frame,
            text="OK",
            command=dialog.destroy,
            width=10
        ).pack(side="right", padx=(5, 0))
        
        if error_details:
            def copy_details():
                dialog.clipboard_clear()
                dialog.clipboard_append(error_details)
                
            tk.Button(
                button_frame,
                text="Copy Details",
                command=copy_details,
                width=12
            ).pack(side="right")
            
        # Center the dialog
        dialog.transient(parent)
        dialog.grab_set()
        
        # Center on parent
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
    def validate_system_requirements(self) -> tuple[bool, list[str]]:
        """
        Validate system requirements.
        
        Returns:
            tuple[bool, list[str]]: (all_valid, error_messages)
        """
        errors = []
        
        try:
            # Check Python version
            if sys.version_info < (3, 11):
                errors.append(f"Python 3.11+ required, found {sys.version_info.major}.{sys.version_info.minor}")
                
            # Check for required modules
            required_modules = [
                ('torch', 'PyTorch'),
                ('sentencepiece', 'SentencePiece'),
                ('tqdm', 'tqdm'),
                ('pydantic', 'Pydantic')
            ]
            
            for module_name, display_name in required_modules:
                try:
                    __import__(module_name)
                except ImportError:
                    errors.append(f"Missing required module: {display_name}")
                    
            # Check available memory (rough estimate)
            try:
                import psutil
                available_memory = psutil.virtual_memory().available / (1024**3)  # GB
                if available_memory < 4:
                    errors.append(f"Low available memory: {available_memory:.1f}GB (4GB+ recommended)")
            except ImportError:
                pass  # psutil not available, skip memory check
                
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"System validation failed: {str(e)}")
            return False, errors
            
    def create_crash_report(self, error: Exception, config: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a detailed crash report.
        
        Args:
            error: Exception that caused the crash
            config: Optional configuration data
            
        Returns:
            Formatted crash report
        """
        import platform
        from datetime import datetime
        
        report_lines = [
            "=" * 60,
            "AFM TRAINER CRASH REPORT",
            "=" * 60,
            f"Timestamp: {datetime.now().isoformat()}",
            f"Platform: {platform.platform()}",
            f"Python: {platform.python_version()}",
            "",
            "ERROR INFORMATION:",
            f"Type: {type(error).__name__}",
            f"Message: {str(error)}",
            "",
            "TRACEBACK:",
            traceback.format_exc(),
            ""
        ]
        
        if config:
            report_lines.extend([
                "CONFIGURATION:",
                json.dumps(config, indent=2, default=str),
                ""
            ])
            
        # System information
        try:
            import psutil
            report_lines.extend([
                "SYSTEM INFORMATION:",
                f"CPU Count: {psutil.cpu_count()}",
                f"Memory Total: {psutil.virtual_memory().total / (1024**3):.1f}GB",
                f"Memory Available: {psutil.virtual_memory().available / (1024**3):.1f}GB",
                ""
            ])
        except ImportError:
            pass
            
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def setup_global_error_handling(log_file: Optional[str] = None):
    """
    Setup global error handling.
    
    Args:
        log_file: Optional log file path
    """
    global _error_handler
    _error_handler = ErrorHandler(log_file)
    
    # Set as global exception handler
    sys.excepthook = _error_handler.handle_exception