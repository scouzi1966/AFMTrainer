#!/usr/bin/env python3
"""
Test script to verify all imports work correctly.
"""

def test_imports():
    """Test that all modules can be imported."""
    try:
        print("Testing AFM Trainer imports...")
        
        # Test core modules
        from afm_trainer import __version__
        print(f"✓ AFM Trainer version: {__version__}")
        
        from afm_trainer.config_manager import ConfigManager, TrainingConfig
        print("✓ ConfigManager imported successfully")
        
        from afm_trainer.training_controller import TrainingController
        print("✓ TrainingController imported successfully")
        
        from afm_trainer.export_handler import ExportHandler
        print("✓ ExportHandler imported successfully")
        
        from afm_trainer.file_manager import FileManager
        print("✓ FileManager imported successfully")
        
        from afm_trainer.wandb_integration import WandBIntegration
        print("✓ WandBIntegration imported successfully")
        
        from afm_trainer.error_handler import ErrorHandler, get_error_handler
        print("✓ ErrorHandler imported successfully")
        
        # Test GUI (might fail in headless environment)
        try:
            from afm_trainer.afm_trainer_gui import AFMTrainerGUI
            print("✓ GUI module imported successfully")
        except ImportError as e:
            if "DISPLAY" in str(e) or "Tkinter" in str(e):
                print("! GUI module import skipped (no display available)")
            else:
                raise
        
        # Test basic functionality
        config_manager = ConfigManager()
        default_config = config_manager.get_default_config()
        print(f"✓ Default config created with {default_config.epochs} epochs")
        
        file_manager = FileManager()
        print("✓ FileManager functionality working")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)