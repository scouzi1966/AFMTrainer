"""
WandB integration for AFM Trainer.
Provides optional Weights & Biases logging and monitoring for training runs.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import threading
import time
import re
from dataclasses import asdict

try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False
    wandb = None


class WandBIntegration:
    """Handles WandB integration for training monitoring."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.run = None
        self.enabled = False
        self.project_name = "afm-trainer"
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()
        
    def is_available(self) -> bool:
        """Check if WandB is available."""
        return WANDB_AVAILABLE
        
    def initialize(self, config: Dict[str, Any], run_name: Optional[str] = None) -> bool:
        """
        Initialize WandB logging.
        
        Args:
            config: Training configuration
            run_name: Optional run name
            
        Returns:
            bool: True if initialized successfully
        """
        if not WANDB_AVAILABLE:
            self.logger.warning("WandB not available. Install with: pip install wandb")
            return False
            
        try:
            # Check if user is logged in
            if not self._is_logged_in():
                self.logger.warning("WandB not logged in. Run 'wandb login' to enable logging.")
                return False
                
            # Create run configuration
            wandb_config = self._create_wandb_config(config)
            
            # Initialize run
            self.run = wandb.init(
                project=self.project_name,
                name=run_name,
                config=wandb_config,
                tags=self._create_tags(config)
            )
            
            self.enabled = True
            self.logger.info(f"WandB initialized: {self.run.url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WandB: {e}")
            return False
            
    def _is_logged_in(self) -> bool:
        """Check if user is logged in to WandB."""
        try:
            # Check for API key
            api_key = os.environ.get('WANDB_API_KEY')
            if api_key:
                return True
                
            # Check for login file
            wandb_dir = Path.home() / ".wandb"
            if (wandb_dir / "settings").exists():
                return True
                
            return False
        except Exception:
            return False
            
    def _create_wandb_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create WandB configuration from training config.
        
        Args:
            config: Training configuration
            
        Returns:
            WandB configuration dictionary
        """
        wandb_config = {
            # Training parameters
            "epochs": config.get('epochs', 2),
            "learning_rate": config.get('learning_rate', 1e-4),
            "batch_size": config.get('batch_size', 4),
            "warmup_epochs": config.get('warmup_epochs', 1),
            "gradient_accumulation_steps": config.get('gradient_accumulation_steps', 1),
            "weight_decay": config.get('weight_decay', 1e-2),
            "precision": config.get('precision', 'bf16-mixed'),
            
            # Model parameters
            "activation_checkpointing": config.get('activation_checkpointing', False),
            "compile_model": config.get('compile_model', False),
            "max_sequence_length": config.get('max_sequence_length'),
            
            # Dataset information
            "train_data": Path(config.get('train_data', '')).name if config.get('train_data') else None,
            "eval_data": Path(config.get('eval_data', '')).name if config.get('eval_data') else None,
            "train_draft": config.get('train_draft', False),
        }
        
        return wandb_config
        
    def _create_tags(self, config: Dict[str, Any]) -> List[str]:
        """
        Create WandB tags from configuration.
        
        Args:
            config: Training configuration
            
        Returns:
            List of tags
        """
        tags = ["afm-trainer", "lora", "apple-foundation-models"]
        
        # Add precision tag
        if config.get('precision'):
            tags.append(f"precision-{config['precision']}")
            
        # Add draft model tag
        if config.get('train_draft', False):
            tags.append("draft-model")
            
        # Add activation checkpointing tag
        if config.get('activation_checkpointing', False):
            tags.append("activation-checkpointing")
            
        return tags
        
    def log_training_start(self, config: Dict[str, Any]):
        """
        Log training start information.
        
        Args:
            config: Training configuration
        """
        if not self.enabled:
            return
            
        try:
            # Log dataset statistics if available
            train_stats = self._get_dataset_stats(config.get('train_data'))
            if train_stats:
                wandb.log({"dataset/train_samples": train_stats.get('valid_samples', 0)})
                wandb.log({"dataset/train_avg_tokens": train_stats.get('average_tokens_per_sample', 0)})
                
            eval_stats = self._get_dataset_stats(config.get('eval_data'))
            if eval_stats:
                wandb.log({"dataset/eval_samples": eval_stats.get('valid_samples', 0)})
                wandb.log({"dataset/eval_avg_tokens": eval_stats.get('average_tokens_per_sample', 0)})
                
            # Log system information
            self._log_system_info()
            
        except Exception as e:
            self.logger.error(f"Error logging training start: {e}")
            
    def log_metrics(self, metrics: Dict[str, Any], step: Optional[int] = None):
        """
        Log training metrics.
        
        Args:
            metrics: Dictionary of metrics to log
            step: Optional step number
        """
        if not self.enabled:
            return
            
        try:
            wandb.log(metrics, step=step)
        except Exception as e:
            self.logger.error(f"Error logging metrics: {e}")
            
    def log_training_progress(self, epoch: int, batch: int, total_batches: int, loss: float):
        """
        Log training progress.
        
        Args:
            epoch: Current epoch
            batch: Current batch
            total_batches: Total batches per epoch
            loss: Current loss value
        """
        if not self.enabled:
            return
            
        try:
            step = epoch * total_batches + batch
            metrics = {
                "train/loss": loss,
                "train/epoch": epoch,
                "train/batch": batch,
                "train/progress": (epoch * total_batches + batch) / (total_batches * self.run.config.get('epochs', 1))
            }
            self.log_metrics(metrics, step=step)
        except Exception as e:
            self.logger.error(f"Error logging training progress: {e}")
            
    def log_evaluation_metrics(self, epoch: int, eval_loss: float):
        """
        Log evaluation metrics.
        
        Args:
            epoch: Current epoch
            eval_loss: Evaluation loss
        """
        if not self.enabled:
            return
            
        try:
            metrics = {
                "eval/loss": eval_loss,
                "eval/epoch": epoch
            }
            self.log_metrics(metrics)
        except Exception as e:
            self.logger.error(f"Error logging evaluation metrics: {e}")
            
    def log_training_completion(self, final_metrics: Dict[str, Any]):
        """
        Log training completion.
        
        Args:
            final_metrics: Final training metrics
        """
        if not self.enabled:
            return
            
        try:
            # Log final metrics
            completion_metrics = {
                "final/train_loss": final_metrics.get('train_loss'),
                "final/eval_loss": final_metrics.get('eval_loss'),
                "final/total_epochs": final_metrics.get('epochs'),
                "final/status": "completed"
            }
            
            # Remove None values
            completion_metrics = {k: v for k, v in completion_metrics.items() if v is not None}
            
            self.log_metrics(completion_metrics)
            
            # Mark run as finished
            if self.run:
                self.run.finish()
                
        except Exception as e:
            self.logger.error(f"Error logging training completion: {e}")
            
    def log_training_failure(self, error_message: str):
        """
        Log training failure.
        
        Args:
            error_message: Error message
        """
        if not self.enabled:
            return
            
        try:
            failure_metrics = {
                "final/status": "failed",
                "final/error": error_message
            }
            self.log_metrics(failure_metrics)
            
            if self.run:
                self.run.finish(exit_code=1)
                
        except Exception as e:
            self.logger.error(f"Error logging training failure: {e}")
            
    def start_log_monitoring(self, log_file: Optional[str] = None):
        """
        Start monitoring log files for automatic metric extraction.
        
        Args:
            log_file: Optional log file to monitor
        """
        if not self.enabled:
            return
            
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
            
        self.stop_monitoring.clear()
        self.monitoring_thread = threading.Thread(
            target=self._monitor_logs,
            args=(log_file,)
        )
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
    def stop_log_monitoring(self):
        """Stop log monitoring."""
        self.stop_monitoring.set()
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
            
    def _monitor_logs(self, log_file: Optional[str] = None):
        """
        Monitor logs for automatic metric extraction.
        
        Args:
            log_file: Log file to monitor
        """
        if not log_file:
            return
            
        try:
            log_path = Path(log_file)
            
            # Patterns for extracting metrics from logs
            patterns = {
                'loss': re.compile(r'loss[=:]?\s*([0-9.]+)', re.IGNORECASE),
                'epoch': re.compile(r'Epoch (\d+)/(\d+)'),
                'batch': re.compile(r'(\d+)/(\d+)\s*\|'),
                'lr': re.compile(r'lr[=:]?\s*([0-9.e-]+)', re.IGNORECASE)
            }
            
            if log_path.exists():
                with open(log_path, 'r') as f:
                    f.seek(0, 2)  # Go to end of file
                    
                    while not self.stop_monitoring.is_set():
                        line = f.readline()
                        if line:
                            self._extract_metrics_from_line(line, patterns)
                        else:
                            time.sleep(0.5)
                            
        except Exception as e:
            self.logger.error(f"Error monitoring logs: {e}")
            
    def _extract_metrics_from_line(self, line: str, patterns: Dict[str, re.Pattern]):
        """
        Extract metrics from a log line.
        
        Args:
            line: Log line
            patterns: Regex patterns for extraction
        """
        try:
            metrics = {}
            
            for metric_name, pattern in patterns.items():
                match = pattern.search(line)
                if match:
                    if metric_name == 'epoch':
                        current_epoch = int(match.group(1))
                        total_epochs = int(match.group(2))
                        metrics['train/current_epoch'] = current_epoch
                        metrics['train/total_epochs'] = total_epochs
                    elif metric_name == 'batch':
                        current_batch = int(match.group(1))
                        total_batches = int(match.group(2))
                        metrics['train/current_batch'] = current_batch
                        metrics['train/total_batches'] = total_batches
                    else:
                        metrics[f'train/{metric_name}'] = float(match.group(1))
                        
            if metrics:
                self.log_metrics(metrics)
                
        except Exception as e:
            self.logger.error(f"Error extracting metrics from line: {e}")
            
    def _get_dataset_stats(self, dataset_path: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Get dataset statistics.
        
        Args:
            dataset_path: Path to dataset file
            
        Returns:
            Dataset statistics or None
        """
        if not dataset_path:
            return None
            
        try:
            from .file_manager import FileManager
            file_manager = FileManager()
            is_valid, _, stats = file_manager.validate_jsonl_file(dataset_path)
            return stats if is_valid else None
        except Exception:
            return None
            
    def _log_system_info(self):
        """Log system information."""
        try:
            import platform
            import psutil
            
            system_info = {
                "system/platform": platform.platform(),
                "system/python_version": platform.python_version(),
                "system/cpu_count": psutil.cpu_count(),
                "system/memory_total_gb": psutil.virtual_memory().total / (1024**3)
            }
            
            # GPU information if available
            try:
                import torch
                if torch.cuda.is_available():
                    system_info["system/cuda_available"] = True
                    system_info["system/cuda_device_count"] = torch.cuda.device_count()
                    system_info["system/cuda_device_name"] = torch.cuda.get_device_name(0)
                else:
                    system_info["system/cuda_available"] = False
                    
                if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    system_info["system/mps_available"] = True
                else:
                    system_info["system/mps_available"] = False
                    
            except ImportError:
                pass
                
            self.log_metrics(system_info)
            
        except Exception as e:
            self.logger.error(f"Error logging system info: {e}")
            
    def create_run_name(self, config: Dict[str, Any]) -> str:
        """
        Create a descriptive run name based on configuration.
        
        Args:
            config: Training configuration
            
        Returns:
            Generated run name
        """
        try:
            # Get adapter name or use default
            adapter_name = config.get('adapter_name', 'adapter')
            
            # Get key parameters
            epochs = config.get('epochs', 2)
            lr = config.get('learning_rate', 1e-4)
            batch_size = config.get('batch_size', 4)
            precision = config.get('precision', 'bf16-mixed')
            
            # Create timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%m%d_%H%M")
            
            # Construct name
            run_name = f"{adapter_name}_e{epochs}_lr{lr}_bs{batch_size}_{precision}_{timestamp}"
            
            return run_name
            
        except Exception:
            return "afm_trainer_run"
            
    def finish(self):
        """Clean up WandB integration."""
        try:
            self.stop_log_monitoring()
            
            if self.run:
                try:
                    self.run.finish()
                    self.logger.info("WandB run finished successfully")
                except Exception as e:
                    self.logger.warning(f"Error finishing WandB run: {e}")
                finally:
                    self.run = None
                    
            self.enabled = False
            self.logger.info("WandB integration cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error finishing WandB integration: {e}")