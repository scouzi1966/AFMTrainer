"""
Training controller for AFM Trainer.
Handles the execution of Apple's training scripts with progress monitoring.
"""

import subprocess
import threading
import time
import re
import os
import sys
from pathlib import Path
from typing import Callable, Optional, Dict, Any
import logging
import queue
import signal

# Defer WandB import to avoid startup penalty
# from .wandb_integration import WandBIntegration
from .error_handler import get_error_handler


class TrainingController:
    """Controls the training process and monitors progress."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.process: Optional[subprocess.Popen] = None
        self.training_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.output_queue = queue.Queue()
        self.wandb_integration = None  # Lazy load when needed
        self.error_handler = get_error_handler()
        
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
                    'setup_logging': lambda *args, **kwargs: None,
                    'finish': lambda: None
                })()
        return self.wandb_integration
        
    def run_training(
        self, 
        config: Dict[str, Any], 
        progress_callback: Callable[[float, str], None],
        log_callback: Callable[[str], None]
    ) -> bool:
        """
        Run the training process with progress monitoring.
        
        Args:
            config: Training configuration dictionary
            progress_callback: Callback for progress updates (progress, message)
            log_callback: Callback for log messages
            
        Returns:
            bool: True if training completed successfully
        """
        try:
            self.stop_event.clear()
            
            # Create output directory
            output_dir = Path(config['output_dir'])
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Build training command
            train_cmd = self._build_training_command(config)
            log_callback(f"Training command: {' '.join(train_cmd)}")
            
            # Start training process
            self.process = subprocess.Popen(
                train_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                cwd=config['toolkit_dir']
            )
            
            # Monitor training output
            # Check if draft model training is enabled
            train_draft = config.get('train_draft', False)
            
            # Adjust progress scaling based on whether draft training is enabled
            def main_progress_callback(progress, message):
                if train_draft:
                    # Main training is only 50% of total when draft is enabled
                    progress_callback(progress * 0.5, message)
                else:
                    progress_callback(progress, message)
            
            success = self._monitor_training_output(
                self.process, 
                main_progress_callback, 
                log_callback,
                config
            )
            
            # Train draft model if requested
            if success and train_draft:
                log_callback("Starting draft model training...")
                
                def draft_progress_callback(progress, message):
                    # Draft training is the second 50% of total progress
                    progress_callback(0.5 + (progress * 0.5), f"Draft: {message}")
                    
                draft_success = self._train_draft_model(config, draft_progress_callback, log_callback)
                success = success and draft_success
            
            return success
            
        except Exception as e:
            self.logger.error(f"Training failed: {e}")
            log_callback(f"Training failed: {str(e)}")
            return False
        finally:
            self.process = None
            
    def stop_training(self):
        """Stop the current training process."""
        self.stop_event.set()
        if self.process:
            try:
                # Try graceful termination first
                self.process.terminate()
                
                # Wait a bit for graceful shutdown
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    self.process.kill()
                    self.process.wait()
                    
            except Exception as e:
                self.logger.error(f"Error stopping training: {e}")
                
    def _build_training_command(self, config: Dict[str, Any]) -> list[str]:
        """
        Build the training command from configuration.
        
        Args:
            config: Training configuration
            
        Returns:
            List of command arguments
        """
        cmd = [
            sys.executable, "-m", "examples.train_adapter",
            "--train-data", config['train_data'],
            "--epochs", str(config['epochs']),
            "--learning-rate", str(config['learning_rate']),
            "--batch-size", str(config['batch_size']),
            "--warmup-epochs", str(config.get('warmup_epochs', 1)),
            "--gradient-accumulation-steps", str(config.get('gradient_accumulation_steps', 1)),
            "--weight-decay", str(config.get('weight_decay', 1e-2)),
            "--clip-grad-norm", str(config.get('clip_grad_norm', 1.0)),
            "--precision", config.get('precision', 'bf16-mixed'),
            "--loss-update-frequency", str(config.get('loss_update_frequency', 3)),
            "--checkpoint-dir", config['output_dir'],
            "--checkpoint-frequency", "1"
        ]
        
        # Add evaluation data if provided
        if config.get('eval_data'):
            cmd.extend(["--eval-data", config['eval_data']])
            
        # Add boolean flags
        if config.get('activation_checkpointing', False):
            cmd.append("--activation-checkpointing")
            
        if config.get('compile_model', False):
            cmd.append("--compile-model")
            
        if config.get('fixed_sized_sequences', False):
            cmd.append("--fixed-sized-sequences")
            
        if config.get('pack_sequences', False):
            cmd.append("--pack-sequences")
            
        # Add max sequence length if provided
        if config.get('max_sequence_length'):
            cmd.extend(["--max-sequence-length", str(config['max_sequence_length'])])
            
        return cmd
        
    def _monitor_training_output(
        self, 
        process: subprocess.Popen,
        progress_callback: Callable[[float, str], None],
        log_callback: Callable[[str], None],
        config: Dict[str, Any]
    ) -> bool:
        """
        Monitor training process output and extract progress information.
        
        Args:
            process: Training subprocess
            progress_callback: Progress update callback
            log_callback: Log message callback
            config: Training configuration
            
        Returns:
            bool: True if training completed successfully
        """
        try:
            current_epoch = 0
            total_epochs = config.get('epochs', 2)
            current_batch = 0
            total_batches = 0
            
            # Patterns to extract information from training output
            epoch_pattern = re.compile(r'Epoch (\d+)/(\d+)')
            batch_pattern = re.compile(r'Training.*?(\d+)/(\d+)')
            loss_pattern = re.compile(r'loss[=:]?\s*([0-9.]+)', re.IGNORECASE)
            
            for line in iter(process.stdout.readline, ''):
                if self.stop_event.is_set():
                    return False
                    
                line = line.strip()
                if not line:
                    continue
                    
                log_callback(line)
                
                # Extract epoch information
                epoch_match = epoch_pattern.search(line)
                if epoch_match:
                    current_epoch = int(epoch_match.group(1))
                    total_epochs = int(epoch_match.group(2))
                    
                # Extract batch information
                batch_match = batch_pattern.search(line)
                if batch_match:
                    current_batch = int(batch_match.group(1))
                    total_batches = int(batch_match.group(2))
                    
                # Calculate progress
                if total_epochs > 0:
                    epoch_progress = (current_epoch - 1) / total_epochs
                    if total_batches > 0:
                        batch_progress = current_batch / total_batches / total_epochs
                        progress = epoch_progress + batch_progress
                    else:
                        progress = epoch_progress
                        
                    progress = min(progress, 1.0)
                    
                    # Create progress message
                    if current_batch > 0 and total_batches > 0:
                        message = f"Epoch {current_epoch}/{total_epochs}, Batch {current_batch}/{total_batches}"
                    else:
                        message = f"Epoch {current_epoch}/{total_epochs}"
                        
                    # Extract loss if available
                    loss_match = loss_pattern.search(line)
                    if loss_match:
                        loss_value = float(loss_match.group(1))
                        message += f", Loss: {loss_value:.4f}"
                        
                    progress_callback(progress, message)
                    
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code == 0:
                progress_callback(1.0, "Training completed successfully")
                return True
            else:
                log_callback(f"Training process exited with code {return_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error monitoring training: {e}")
            log_callback(f"Error monitoring training: {str(e)}")
            return False
            
    def _train_draft_model(
        self,
        config: Dict[str, Any],
        progress_callback: Callable[[float, str], None],
        log_callback: Callable[[str], None]
    ) -> bool:
        """
        Train the draft model for speculative decoding.
        
        Args:
            config: Training configuration
            progress_callback: Progress update callback
            log_callback: Log message callback
            
        Returns:
            bool: True if draft training completed successfully
        """
        try:
            # Find the latest adapter checkpoint
            output_dir = Path(config['output_dir'])
            adapter_checkpoints = list(output_dir.glob("adapter-*.pt"))
            
            if not adapter_checkpoints:
                log_callback("No adapter checkpoint found for draft model training")
                return False
                
            # Use the final checkpoint
            latest_checkpoint = max(adapter_checkpoints, key=lambda x: x.stat().st_mtime)
            log_callback(f"Using adapter checkpoint: {latest_checkpoint}")
            
            # Build draft training command
            draft_cmd = [
                sys.executable, "-m", "examples.train_draft_model",
                "--checkpoint", str(latest_checkpoint),
                "--train-data", config['train_data'],
                "--epochs", str(config['epochs']),
                "--learning-rate", str(config['learning_rate']),
                "--batch-size", str(config['batch_size']),
                "--checkpoint-dir", config['output_dir'],
                "--checkpoint-frequency", "1"
            ]
            
            # Add evaluation data if provided
            if config.get('eval_data'):
                draft_cmd.extend(["--eval-data", config['eval_data']])
                
            log_callback(f"Draft training command: {' '.join(draft_cmd)}")
            
            # Start draft training process
            draft_process = subprocess.Popen(
                draft_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                cwd=config['toolkit_dir']
            )
            
            # Monitor draft training with progress tracking
            progress_callback(0.0, "Draft training starting...")
            
            for line in iter(draft_process.stdout.readline, ''):
                if self.stop_event.is_set():
                    draft_process.terminate()
                    return False
                    
                line = line.strip()
                if line:
                    log_callback(f"[Draft] {line}")
                    
                    # Extract progress from draft training output
                    epoch_match = re.search(r'Epoch (\d+)/(\d+)', line)
                    if epoch_match:
                        current = int(epoch_match.group(1))
                        total = int(epoch_match.group(2))
                        progress = (current - 1) / total if total > 0 else 0.0
                        progress_callback(progress, f"Draft: Epoch {current}/{total}")
                    
            return_code = draft_process.wait()
            
            if return_code == 0:
                progress_callback(1.0, "Draft training completed successfully")
                log_callback("Draft model training completed successfully")
                return True
            else:
                log_callback(f"Draft model training failed with code {return_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Draft model training failed: {e}")
            log_callback(f"Draft model training failed: {str(e)}")
            return False
            
    def is_training_active(self) -> bool:
        """Check if training is currently active."""
        return self.process is not None and self.process.poll() is None
        
    def get_training_status(self) -> str:
        """Get current training status."""
        if self.process is None:
            return "idle"
        elif self.process.poll() is None:
            return "running"
        elif self.process.returncode == 0:
            return "completed"
        else:
            return "failed"