"""
File management utilities for AFM Trainer.
Handles file operations, validation, and .gitignore management.
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
import re


class FileManager:
    """Manages file operations for AFM Trainer."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def validate_jsonl_file(self, file_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate a JSONL file format and content.
        
        Args:
            file_path: Path to the JSONL file
            
        Returns:
            tuple[bool, str, dict]: (is_valid, error_message, stats)
        """
        try:
            if not file_path:
                return False, "File path is empty", {}
                
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return False, "File does not exist", {}
                
            if file_path_obj.suffix.lower() != ".jsonl":
                return False, "File must have .jsonl extension", {}
                
            stats = {
                'total_lines': 0,
                'valid_samples': 0,
                'invalid_samples': 0,
                'has_system_messages': 0,
                'has_multi_turn': 0,
                'average_tokens_per_sample': 0,
                'roles_found': set()
            }
            
            total_tokens = 0
            
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    stats['total_lines'] += 1
                    
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        data = json.loads(line)
                        
                        # Handle wrapped format {"messages": [...]}
                        if isinstance(data, dict) and "messages" in data:
                            data = data["messages"]
                            
                        # Check if it's a list (expected format)
                        if not isinstance(data, list):
                            stats['invalid_samples'] += 1
                            if line_num <= 5:  # Only report first few errors
                                return False, f"Line {line_num}: Expected list format, got {type(data).__name__}", stats
                            continue
                            
                        # Validate message structure
                        valid_sample = True
                        has_system = False
                        turn_count = 0
                        sample_tokens = 0
                        
                        for i, item in enumerate(data):
                            if not isinstance(item, dict):
                                valid_sample = False
                                if line_num <= 5:
                                    return False, f"Line {line_num}, item {i}: Expected dict, got {type(item).__name__}", stats
                                break
                                
                            if "role" not in item or "content" not in item:
                                valid_sample = False
                                if line_num <= 5:
                                    return False, f"Line {line_num}, item {i}: Missing 'role' or 'content' field", stats
                                break
                                
                            role = item["role"]
                            content = item["content"]
                            
                            valid_roles = ["system", "user", "assistant"]
                            if role not in valid_roles:
                                valid_sample = False
                                if line_num <= 5:
                                    return False, f"Line {line_num}, item {i}: Invalid role '{role}', must be one of {valid_roles}", stats
                                break
                                
                            stats['roles_found'].add(role)
                            
                            if role == "system":
                                has_system = True
                                
                            if role in ["user", "assistant"]:
                                turn_count += 1
                                
                            # Rough token count (words * 1.3)
                            sample_tokens += len(content.split()) * 1.3
                            
                        if valid_sample:
                            stats['valid_samples'] += 1
                            if has_system:
                                stats['has_system_messages'] += 1
                            if turn_count > 2:  # More than one user-assistant exchange
                                stats['has_multi_turn'] += 1
                            total_tokens += sample_tokens
                        else:
                            stats['invalid_samples'] += 1
                            
                    except json.JSONDecodeError as e:
                        stats['invalid_samples'] += 1
                        if line_num <= 5:
                            return False, f"Line {line_num}: Invalid JSON - {str(e)}", stats
                        continue
                        
            if stats['total_lines'] == 0:
                return False, "File is empty", stats
                
            if stats['valid_samples'] == 0:
                return False, "No valid samples found", stats
                
            # Calculate average tokens
            if stats['valid_samples'] > 0:
                stats['average_tokens_per_sample'] = int(total_tokens / stats['valid_samples'])
                
            # Convert set to list for JSON serialization
            stats['roles_found'] = list(stats['roles_found'])
            
            return True, "", stats
            
        except Exception as e:
            return False, f"Validation error: {str(e)}", {}
            
    def preview_dataset(self, file_path: str, num_samples: int = 3) -> List[Dict[str, Any]]:
        """
        Preview a few samples from a JSONL dataset.
        
        Args:
            file_path: Path to the JSONL file
            num_samples: Number of samples to preview
            
        Returns:
            List of sample dictionaries
        """
        try:
            samples = []
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return samples
                
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    if len(samples) >= num_samples:
                        break
                        
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        data = json.loads(line)
                        
                        # Handle wrapped format
                        if isinstance(data, dict) and "messages" in data:
                            data = data["messages"]
                            
                        if isinstance(data, list):
                            samples.append({
                                'line_number': line_num + 1,
                                'data': data,
                                'formatted': self._format_sample_for_display(data)
                            })
                            
                    except json.JSONDecodeError:
                        continue
                        
            return samples
            
        except Exception as e:
            self.logger.error(f"Error previewing dataset: {e}")
            return []
            
    def _format_sample_for_display(self, data: List[Dict[str, Any]]) -> str:
        """
        Format a sample for human-readable display.
        
        Args:
            data: List of message dictionaries
            
        Returns:
            Formatted string
        """
        formatted_parts = []
        
        for item in data:
            role = item.get('role', 'unknown')
            content = item.get('content', '')
            
            # Truncate long content
            if len(content) > 100:
                content = content[:97] + "..."
                
            formatted_parts.append(f"{role.upper()}: {content}")
            
        return " → ".join(formatted_parts)
        
    def update_gitignore(self, project_root: str, toolkit_dir: str):
        """
        Update .gitignore to exclude the toolkit directory.
        
        Args:
            project_root: Root directory of the project
            toolkit_dir: Path to the toolkit directory
        """
        try:
            project_path = Path(project_root)
            gitignore_path = project_path / ".gitignore"
            
            # Get relative path of toolkit directory
            toolkit_path = Path(toolkit_dir)
            try:
                relative_toolkit = toolkit_path.relative_to(project_path)
                ignore_pattern = str(relative_toolkit) + "/"
            except ValueError:
                # If not relative to project, use absolute pattern
                ignore_pattern = str(toolkit_path) + "/"
                
            # Read existing .gitignore
            existing_lines = []
            if gitignore_path.exists():
                with open(gitignore_path, 'r') as f:
                    existing_lines = [line.rstrip() for line in f.readlines()]
                    
            # Check if pattern already exists
            pattern_exists = any(
                line.strip() == ignore_pattern.strip() or 
                line.strip() == toolkit_path.name + "/" or
                line.strip().endswith("adapter_training_toolkit*/")
                for line in existing_lines
            )
            
            if not pattern_exists:
                # Add our pattern
                if existing_lines and not existing_lines[-1].startswith("#"):
                    existing_lines.append("")
                    
                existing_lines.extend([
                    "# Apple Foundation Models Adapter Training Toolkit",
                    ignore_pattern,
                ])
                
                # Write updated .gitignore
                with open(gitignore_path, 'w') as f:
                    f.write("\n".join(existing_lines) + "\n")
                    
                self.logger.info(f"Updated .gitignore to exclude {ignore_pattern}")
            else:
                self.logger.info("Toolkit directory already in .gitignore")
                
        except Exception as e:
            self.logger.error(f"Error updating .gitignore: {e}")
            
    def create_output_directory(self, output_dir: str) -> bool:
        """
        Create output directory structure.
        
        Args:
            output_dir: Path to output directory
            
        Returns:
            bool: True if successful
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            subdirs = ['checkpoints', 'logs', 'exports']
            for subdir in subdirs:
                (output_path / subdir).mkdir(exist_ok=True)
                
            self.logger.info(f"Created output directory structure at {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating output directory: {e}")
            return False
            
    def clean_output_directory(self, output_dir: str, keep_exports: bool = True) -> bool:
        """
        Clean output directory, optionally keeping exports.
        
        Args:
            output_dir: Path to output directory
            keep_exports: Whether to keep exported .fmadapter files
            
        Returns:
            bool: True if successful
        """
        try:
            output_path = Path(output_dir)
            
            if not output_path.exists():
                return True
                
            for item in output_path.iterdir():
                if item.is_file():
                    if keep_exports and item.suffix == ".fmadapter":
                        continue
                    if item.name.endswith(('.pt', '.log')):
                        item.unlink()
                elif item.is_dir():
                    if keep_exports and item.suffix == ".fmadapter":
                        continue
                    if item.name in ['checkpoints', 'logs']:
                        shutil.rmtree(item)
                        item.mkdir()
                        
            self.logger.info(f"Cleaned output directory {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning output directory: {e}")
            return False
            
    def get_directory_size(self, directory: str) -> int:
        """
        Get the total size of a directory in bytes.
        
        Args:
            directory: Path to directory
            
        Returns:
            Size in bytes
        """
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        continue
            return total_size
        except Exception:
            return 0
            
    def format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f} MB"
        else:
            return f"{size_bytes/(1024**3):.1f} GB"
            
    def backup_config(self, config: Dict[str, Any], backup_dir: str) -> bool:
        """
        Backup training configuration.
        
        Args:
            config: Configuration dictionary
            backup_dir: Directory to save backup
            
        Returns:
            bool: True if successful
        """
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Create timestamp-based filename
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_path / f"config_backup_{timestamp}.json"
            
            with open(backup_file, 'w') as f:
                json.dump(config, f, indent=2, default=str)
                
            self.logger.info(f"Configuration backed up to {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error backing up configuration: {e}")
            return False