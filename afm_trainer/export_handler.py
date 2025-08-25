"""
Export handler for AFM Trainer.
Handles exporting trained adapters to .fmadapter format.
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import logging
import json


class ExportHandler:
    """Handles adapter export functionality."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def export_adapter(self, config: Dict[str, Any], log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Export a trained adapter to .fmadapter format.
        
        Args:
            config: Export configuration containing:
                - output_dir: Directory containing training checkpoints
                - adapter_name: Name for the exported adapter
                - author: Author name
                - description: Adapter description
                - license: License information
            log_callback: Optional callback for log messages
                
        Returns:
            bool: True if export successful
        """
        def _log(message: str):
            """Helper function for logging."""
            self.logger.info(message)
            if log_callback:
                log_callback(message)
        
        try:
            _log("🚀 Starting adapter export...")
            
            # Find the latest adapter checkpoint
            output_dir = Path(config['output_dir'])
            _log(f"Searching for checkpoints in: {output_dir}")
            
            adapter_checkpoint = self._find_latest_checkpoint(output_dir, "adapter")
            
            if not adapter_checkpoint:
                raise Exception("No adapter checkpoint found")
                
            _log(f"✓ Found adapter checkpoint: {adapter_checkpoint.name}")
                
            # Find draft model checkpoint if exists
            draft_checkpoint = self._find_latest_checkpoint(output_dir, "draft-model")
            if draft_checkpoint:
                _log(f"✓ Found draft model checkpoint: {draft_checkpoint.name}")
            else:
                _log("ℹ No draft model checkpoint found (optional)")
            
            # Determine toolkit directory
            toolkit_dir = self._find_toolkit_directory(config.get('toolkit_dir'))
            if not toolkit_dir:
                raise Exception("Could not find toolkit directory")
                
            _log(f"✓ Using toolkit directory: {toolkit_dir}")
                
            # Build export command
            export_cmd = self._build_export_command(
                config, 
                adapter_checkpoint, 
                draft_checkpoint,
                toolkit_dir
            )
            
            _log(f"📝 Export command: {' '.join(export_cmd)}")
            _log("🔄 Running export process...")
            
            # Run export process with real-time output
            process = subprocess.Popen(
                export_cmd,
                cwd=toolkit_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Stream output in real-time
            output_lines = []
            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                if line:
                    output_lines.append(line)
                    _log(f"[Export] {line}")
                    
            # Wait for process completion
            return_code = process.wait()
            
            if return_code != 0:
                raise subprocess.CalledProcessError(return_code, export_cmd, output='\n'.join(output_lines))
                
            # Verify export success
            adapter_path = output_dir / f"{config['adapter_name']}.fmadapter"
            if adapter_path.exists():
                _log(f"✅ Adapter exported successfully to: {adapter_path}")
                _log(f"📦 Export size: {self._get_directory_size(adapter_path)}")
                
                # List contents of the exported adapter
                _log("📋 Exported adapter contents:")
                for item in sorted(adapter_path.iterdir()):
                    if item.is_file():
                        size = item.stat().st_size
                        _log(f"   📄 {item.name} ({self._format_size(size)})")
                    elif item.is_dir():
                        _log(f"   📁 {item.name}/")
                        
                return True
            else:
                raise Exception("Export completed but .fmadapter file not found")
                
        except subprocess.CalledProcessError as e:
            error_msg = f"Export command failed with return code {e.returncode}"
            _log(f"❌ {error_msg}")
            if hasattr(e, 'output') and e.output:
                _log(f"Command output: {e.output}")
            self.logger.error(f"Export command failed: {e}")
            return False
        except Exception as e:
            _log(f"❌ Export failed: {str(e)}")
            self.logger.error(f"Export failed: {e}")
            return False
            
    def _find_latest_checkpoint(self, output_dir: Path, checkpoint_type: str) -> Optional[Path]:
        """
        Find the latest checkpoint of the specified type.
        
        Args:
            output_dir: Directory to search for checkpoints
            checkpoint_type: Type of checkpoint ("adapter" or "draft-model")
            
        Returns:
            Path to the latest checkpoint or None
        """
        try:
            pattern = f"{checkpoint_type}-*.pt"
            checkpoints = list(output_dir.glob(pattern))
            
            if not checkpoints:
                return None
                
            # Find the latest checkpoint (assuming final checkpoint is preferred)
            final_checkpoint = output_dir / f"{checkpoint_type}-final.pt"
            if final_checkpoint.exists():
                return final_checkpoint
                
            # Otherwise, find the highest epoch number
            latest_checkpoint = max(checkpoints, key=lambda x: x.stat().st_mtime)
            return latest_checkpoint
            
        except Exception as e:
            self.logger.error(f"Error finding {checkpoint_type} checkpoint: {e}")
            return None
            
    def _find_toolkit_directory(self, toolkit_dir: Optional[str] = None) -> Optional[Path]:
        """
        Find the toolkit directory.
        
        Args:
            toolkit_dir: Explicit toolkit directory path
            
        Returns:
            Path to toolkit directory or None
        """
        if toolkit_dir:
            toolkit_path = Path(toolkit_dir)
            if toolkit_path.exists() and (toolkit_path / "export").exists():
                return toolkit_path
                
        # Search for default toolkit directories
        search_paths = [
            Path.cwd() / ".adapter_training_toolkit_v26_0_0",
            Path.cwd() / "adapter_training_toolkit_v26_0_0",
        ]
        
        # Also search for any directory matching the pattern
        for pattern in [".adapter_training_toolkit_v*", "adapter_training_toolkit_v*"]:
            search_paths.extend(Path.cwd().glob(pattern))
            
        for path in search_paths:
            if path.exists() and (path / "export").exists():
                return path
                
        return None
        
    def _build_export_command(
        self, 
        config: Dict[str, Any],
        adapter_checkpoint: Path,
        draft_checkpoint: Optional[Path],
        toolkit_dir: Path
    ) -> list[str]:
        """
        Build the export command.
        
        Args:
            config: Export configuration
            adapter_checkpoint: Path to adapter checkpoint
            draft_checkpoint: Path to draft checkpoint (optional)
            toolkit_dir: Path to toolkit directory
            
        Returns:
            List of command arguments
        """
        cmd = [
            sys.executable, "-m", "export.export_fmadapter",
            "--output-dir", str(config['output_dir']),
            "--adapter-name", config['adapter_name'],
            "--checkpoint", str(adapter_checkpoint),
            "--author", config.get('author', '3P developer')
        ]
        
        # Add description if provided
        description = config.get('description', '').strip()
        if description:
            cmd.extend(["--description", description])
            
        # Add draft checkpoint if available
        if draft_checkpoint:
            cmd.extend(["--draft-checkpoint", str(draft_checkpoint)])
            
        return cmd
        
    def create_asset_pack(self, fmadapter_path: str, output_path: str) -> bool:
        """
        Create an asset pack from an .fmadapter file.
        
        Args:
            fmadapter_path: Path to the .fmadapter directory
            output_path: Output path for the asset pack
            
        Returns:
            bool: True if asset pack creation successful
        """
        try:
            # Check if Xcode is available (required for asset pack creation)
            xcode_check = subprocess.run(
                ["xcode-select", "-p"],
                capture_output=True,
                text=True
            )
            
            if xcode_check.returncode != 0:
                self.logger.error("Xcode is required for asset pack creation")
                return False
                
            # Find toolkit directory
            toolkit_dir = self._find_toolkit_directory()
            if not toolkit_dir:
                raise Exception("Could not find toolkit directory")
                
            # Build asset pack creation command
            asset_cmd = [
                sys.executable, "-m", "export.produce_asset_pack",
                "--fmadapter-path", fmadapter_path,
                "--output-path", output_path,
                "--platforms", "iOS,macOS",
                "--download-policy", "PREFETCH",
                "--installation-event-type", "FIRST_INSTALLTION"
            ]
            
            self.logger.info(f"Asset pack command: {' '.join(asset_cmd)}")
            
            # Run asset pack creation
            result = subprocess.run(
                asset_cmd,
                cwd=toolkit_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.logger.info(f"Asset pack creation successful: {result.stdout}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Asset pack creation failed: {e}")
            self.logger.error(f"Asset pack stderr: {e.stderr}")
            return False
        except Exception as e:
            self.logger.error(f"Asset pack creation failed: {e}")
            return False
            
    def validate_export_config(self, config: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate export configuration.
        
        Args:
            config: Export configuration
            
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        try:
            # Check required fields
            required_fields = ['output_dir', 'adapter_name']
            for field in required_fields:
                if not config.get(field):
                    return False, f"Missing required field: {field}"
                    
            # Check output directory exists
            output_dir = Path(config['output_dir'])
            if not output_dir.exists():
                return False, "Output directory does not exist"
                
            # Check for adapter checkpoint
            adapter_checkpoint = self._find_latest_checkpoint(output_dir, "adapter")
            if not adapter_checkpoint:
                return False, "No adapter checkpoint found in output directory"
                
            # Validate adapter name (basic validation)
            adapter_name = config['adapter_name'].strip()
            if not adapter_name:
                return False, "Adapter name cannot be empty"
                
            if any(char in adapter_name for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
                return False, "Adapter name contains invalid characters"
                
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
            
    def get_export_info(self, output_dir: str) -> Dict[str, Any]:
        """
        Get information about available exports.
        
        Args:
            output_dir: Output directory to check
            
        Returns:
            Dictionary with export information
        """
        try:
            output_path = Path(output_dir)
            
            info = {
                'adapter_checkpoint': None,
                'draft_checkpoint': None,
                'fmadapter_files': [],
                'has_xcode': False
            }
            
            # Find checkpoints
            info['adapter_checkpoint'] = self._find_latest_checkpoint(output_path, "adapter")
            info['draft_checkpoint'] = self._find_latest_checkpoint(output_path, "draft-model")
            
            # Find existing .fmadapter files
            fmadapter_dirs = list(output_path.glob("*.fmadapter"))
            info['fmadapter_files'] = [f.name for f in fmadapter_dirs]
            
            # Check for Xcode availability
            try:
                result = subprocess.run(
                    ["xcode-select", "-p"],
                    capture_output=True,
                    text=True
                )
                info['has_xcode'] = result.returncode == 0
            except FileNotFoundError:
                info['has_xcode'] = False
                
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting export info: {e}")
            return {
                'adapter_checkpoint': None,
                'draft_checkpoint': None,
                'fmadapter_files': [],
                'has_xcode': False
            }
            
    def _get_directory_size(self, directory: Path) -> str:
        """Get the total size of a directory formatted as string."""
        try:
            total_size = 0
            for item in directory.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
            return self._format_size(total_size)
        except Exception:
            return "Unknown"
            
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f} MB"
        else:
            return f"{size_bytes/(1024**3):.1f} GB"