"""
Configuration management for AFM Trainer.
Handles saving/loading training configurations and parameter validation.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging


@dataclass
class TrainingConfig:
    """Training configuration data class matching Apple's AdapterTrainingConfiguration."""
    
    # Basic parameters
    epochs: int = 2
    learning_rate: float = 1e-4
    batch_size: int = 4
    
    # Advanced parameters
    linear_warmup_epochs: int = 1
    gradient_accumulation_steps: int = 1
    weight_decay: float = 1e-2
    clip_grad_norm: float = 1.0
    precision: str = "bf16-mixed"
    
    # Boolean flags
    enable_activation_checkpointing: bool = False
    compile_model: bool = False
    fixed_sized_sequences: bool = False
    pack_sequences: bool = False
    
    # Optional parameters
    max_sequence_length: Optional[int] = None
    loss_update_frequency: int = 3
    
    # File paths
    toolkit_dir: str = ""
    train_data: str = ""
    eval_data: str = ""
    output_dir: str = ""
    
    # Export configuration
    adapter_name: str = "my_adapter"
    author: str = "3P developer"
    description: str = ""
    license: str = ""
    train_draft: bool = False
    
    def validate(self) -> tuple[bool, str]:
        """
        Validate the configuration parameters.
        
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        try:
            # Validate epochs
            if self.epochs <= 0:
                return False, "Epochs must be greater than 0"
                
            # Validate learning rate
            if self.learning_rate <= 0:
                return False, "Learning rate must be greater than 0"
                
            # Validate batch size
            if self.batch_size <= 0:
                return False, "Batch size must be greater than 0"
                
            # Validate warmup epochs
            if self.linear_warmup_epochs < 0:
                return False, "Warmup epochs must be non-negative"
                
            # Validate gradient accumulation
            if self.gradient_accumulation_steps <= 0:
                return False, "Gradient accumulation steps must be greater than 0"
                
            # Validate weight decay
            if self.weight_decay < 0:
                return False, "Weight decay must be non-negative"
                
            # Validate clip grad norm
            if self.clip_grad_norm <= 0:
                return False, "Gradient clipping norm must be greater than 0"
                
            # Validate precision
            valid_precisions = ["f32", "bf16", "bf16-mixed", "f16-mixed"]
            if self.precision not in valid_precisions:
                return False, f"Precision must be one of {valid_precisions}"
                
            # Validate max sequence length if provided
            if self.max_sequence_length is not None and self.max_sequence_length <= 0:
                return False, "Max sequence length must be greater than 0"
                
            # Check sequence packing requirements
            if self.pack_sequences and self.max_sequence_length is None:
                return False, "Max sequence length must be set when pack sequences is enabled"
                
            if self.fixed_sized_sequences and self.max_sequence_length is None:
                return False, "Max sequence length must be set when fixed sized sequences is enabled"
                
            # Validate file paths
            if not self.toolkit_dir:
                return False, "Toolkit directory is required"
                
            if not Path(self.toolkit_dir).exists():
                return False, "Toolkit directory does not exist. Ensure you have Apple Developer Program entitlements and download from: https://developer.apple.com/apple-intelligence/foundation-models-adapter/"
                
            if not self.train_data:
                return False, "Training data file is required"
                
            if not Path(self.train_data).exists():
                return False, "Training data file does not exist"
                
            if self.eval_data and not Path(self.eval_data).exists():
                return False, "Evaluation data file does not exist"
                
            if not self.output_dir:
                return False, "Output directory is required"
                
            # Validate adapter name
            if not self.adapter_name.strip():
                return False, "Adapter name is required"
                
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"


class ConfigManager:
    """Manages configuration loading, saving, and validation."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path.cwd() / "config_profiles"
        self.config_dir.mkdir(exist_ok=True)
        
    def save_config(self, config: TrainingConfig, name: str) -> bool:
        """
        Save a training configuration to a file.
        
        Args:
            config: Training configuration to save
            name: Name for the configuration profile
            
        Returns:
            bool: True if saved successfully
        """
        try:
            config_file = self.config_dir / f"{name}.json"
            config_dict = asdict(config)
            
            with open(config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
                
            self.logger.info(f"Configuration saved to {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
            
    def load_config(self, name: str) -> Optional[TrainingConfig]:
        """
        Load a training configuration from a file.
        
        Args:
            name: Name of the configuration profile
            
        Returns:
            TrainingConfig or None if loading failed
        """
        try:
            config_file = self.config_dir / f"{name}.json"
            
            if not config_file.exists():
                self.logger.warning(f"Configuration file {config_file} does not exist")
                return None
                
            with open(config_file, 'r') as f:
                config_dict = json.load(f)
                
            # Create TrainingConfig with loaded data
            config = TrainingConfig(**config_dict)
            self.logger.info(f"Configuration loaded from {config_file}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return None
            
    def list_configs(self) -> list[str]:
        """
        List available configuration profiles.
        
        Returns:
            List of configuration profile names
        """
        try:
            config_files = list(self.config_dir.glob("*.json"))
            return [f.stem for f in config_files]
        except Exception as e:
            self.logger.error(f"Failed to list configurations: {e}")
            return []
            
    def delete_config(self, name: str) -> bool:
        """
        Delete a configuration profile.
        
        Args:
            name: Name of the configuration profile to delete
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            config_file = self.config_dir / f"{name}.json"
            
            if config_file.exists():
                config_file.unlink()
                self.logger.info(f"Configuration {name} deleted")
                return True
            else:
                self.logger.warning(f"Configuration {name} does not exist")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to delete configuration: {e}")
            return False
            
    def get_default_config(self) -> TrainingConfig:
        """
        Get a default training configuration with sensible defaults.
        
        Returns:
            TrainingConfig with default values
        """
        return TrainingConfig()
        
    def validate_toolkit_directory(self, toolkit_dir: str) -> tuple[bool, str]:
        """
        Validate that a directory contains the Apple toolkit.
        
        Args:
            toolkit_dir: Path to the toolkit directory
            
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        try:
            toolkit_path = Path(toolkit_dir)
            
            if not toolkit_path.exists():
                return False, "Directory does not exist"
                
            # Check for required components
            required_components = [
                "examples",
                "export", 
                "assets",
                "requirements.txt"
            ]
            
            missing_components = []
            for component in required_components:
                if not (toolkit_path / component).exists():
                    missing_components.append(component)
                    
            if missing_components:
                return False, f"Missing required components: {', '.join(missing_components)}"
                
            # Check for specific files within examples
            examples_dir = toolkit_path / "examples"
            required_examples = ["train_adapter.py", "data.py", "utils.py"]
            
            missing_examples = []
            for example in required_examples:
                if not (examples_dir / example).exists():
                    missing_examples.append(example)
                    
            if missing_examples:
                return False, f"Missing required example files: {', '.join(missing_examples)}"
                
            # Check for export functionality
            export_dir = toolkit_path / "export"
            if not (export_dir / "export_fmadapter.py").exists():
                return False, "Missing export functionality"
                
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
            
    def validate_dataset_file(self, file_path: str) -> tuple[bool, str]:
        """
        Validate a JSONL dataset file format.
        
        Args:
            file_path: Path to the dataset file
            
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        try:
            if not file_path:
                return False, "File path is empty"
                
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return False, "File does not exist"
                
            if file_path_obj.suffix.lower() != ".jsonl":
                return False, "File must have .jsonl extension"
                
            # Check file content (first few lines)
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                line_count = 0
                for line in f:
                    line_count += 1
                    if line_count > 5:  # Check only first 5 lines for performance
                        break
                        
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        data = json.loads(line)
                        
                        # Check if it's a list (expected format)
                        if not isinstance(data, list):
                            return False, f"Line {line_count}: Expected list format, got {type(data).__name__}"
                            
                        # Check for required role-content structure
                        for i, item in enumerate(data):
                            if not isinstance(item, dict):
                                return False, f"Line {line_count}, item {i}: Expected dict, got {type(item).__name__}"
                                
                            if "role" not in item or "content" not in item:
                                return False, f"Line {line_count}, item {i}: Missing 'role' or 'content' field"
                                
                            valid_roles = ["system", "user", "assistant"]
                            if item["role"] not in valid_roles:
                                return False, f"Line {line_count}, item {i}: Invalid role '{item['role']}', must be one of {valid_roles}"
                                
                    except json.JSONDecodeError as e:
                        return False, f"Line {line_count}: Invalid JSON - {str(e)}"
                        
            if line_count == 0:
                return False, "File is empty"
                
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
            
    def create_training_args_dict(self, config: TrainingConfig) -> Dict[str, Any]:
        """
        Convert TrainingConfig to dictionary format expected by Apple's training script.
        
        Args:
            config: Training configuration
            
        Returns:
            Dictionary with training arguments
        """
        args_dict = {
            'train_data': config.train_data,
            'eval_data': config.eval_data if config.eval_data else None,
            'epochs': config.epochs,
            'learning_rate': config.learning_rate,
            'batch_size': config.batch_size,
            'warmup_epochs': config.linear_warmup_epochs,
            'gradient_accumulation_steps': config.gradient_accumulation_steps,
            'weight_decay': config.weight_decay,
            'clip_grad_norm': config.clip_grad_norm,
            'precision': config.precision,
            'activation_checkpointing': config.enable_activation_checkpointing,
            'compile_model': config.compile_model,
            'fixed_sized_sequences': config.fixed_sized_sequences,
            'pack_sequences': config.pack_sequences,
            'max_sequence_length': config.max_sequence_length,
            'loss_update_frequency': config.loss_update_frequency,
        }
        
        return args_dict