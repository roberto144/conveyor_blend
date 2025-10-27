import json
import os
from typing import Dict, Any, Optional, Union
from .exceptions import ValidationError

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_file: str = "config/default_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration values
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValidationError: If configuration is invalid
        """
        try:
            # Validate required sections
            required_sections = ['simulation', 'ui', 'materials', 'validation']
            for section in required_sections:
                if section not in config:
                    raise ValidationError(f"Missing required configuration section: {section}")
            
            # Validate simulation parameters
            sim_config = config['simulation']
            self._validate_positive_float(sim_config, 'default_total_time')
            self._validate_positive_float(sim_config, 'default_conveyor_length')
            self._validate_positive_float(sim_config, 'default_resolution_size')
            self._validate_positive_float(sim_config, 'default_conveyor_velocity')
            self._validate_positive_float(sim_config, 'max_simulation_time')
            
            # Validate UI parameters
            ui_config = config['ui']
            self._validate_positive_int(ui_config, 'window_width', min_value=800)
            self._validate_positive_int(ui_config, 'window_height', min_value=600)
            self._validate_auto_save_interval(ui_config.get('auto_save_interval', 300))
            
            # Validate materials
            materials = config['materials'].get('default_materials', [])
            if not isinstance(materials, list) or not all(isinstance(m, str) for m in materials):
                raise ValidationError("default_materials must be a list of strings")
                
            # Validate validation parameters
            val_config = config['validation']
            self._validate_positive_float(val_config, 'min_capacity')
            self._validate_positive_float(val_config, 'max_capacity')
            self._validate_positive_float(val_config, 'min_flow_rate')
            self._validate_positive_float(val_config, 'max_flow_rate')
            
            if val_config['min_capacity'] >= val_config['max_capacity']:
                raise ValidationError("min_capacity must be less than max_capacity")
            if val_config['min_flow_rate'] >= val_config['max_flow_rate']:
                raise ValidationError("min_flow_rate must be less than max_flow_rate")
            
            return True
            
        except KeyError as e:
            raise ValidationError(f"Missing required configuration key: {e}")
        except TypeError as e:
            raise ValidationError(f"Invalid configuration type: {e}")
        except ValueError as e:
            raise ValidationError(f"Invalid configuration value: {e}")

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "simulation": {
                "default_total_time": 150.0,
                "default_conveyor_length": 35.0,
                "default_resolution_size": 1.0,
                "default_conveyor_velocity": 2.0,
                "max_simulation_time": 86400.0
            },
            "ui": {
                "window_width": 1400,
                "window_height": 800,
                "theme": "default",
                "auto_save_interval": 300
            },
            "materials": {
                "default_materials": [
                    "Lump Ore", "Sinter", "Pellet", "Nut Coke", "Limestone", "Quartz", "Dolomite"
                ]
            },
            "validation": {
                "min_capacity": 1.0,
                "max_capacity": 999999.0,
                "min_flow_rate": 0.01,
                "max_flow_rate": 1000.0
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                # Merge with defaults
                default_config.update(loaded_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        return default_config
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def _validate_positive_float(self, config: Dict[str, Any], key: str, min_value: float = 0.0) -> None:
        """Validate that a configuration value is a positive float"""
        value = config.get(key)
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{key} must be a number")
        if float(value) <= min_value:
            raise ValidationError(f"{key} must be greater than {min_value}")
    
    def _validate_positive_int(self, config: Dict[str, Any], key: str, min_value: int = 0) -> None:
        """Validate that a configuration value is a positive integer"""
        value = config.get(key)
        if not isinstance(value, int):
            raise ValidationError(f"{key} must be an integer")
        if value < min_value:
            raise ValidationError(f"{key} must be at least {min_value}")
    
    def _validate_auto_save_interval(self, value: int) -> None:
        """Validate auto-save interval"""
        if not isinstance(value, int):
            raise ValidationError("auto_save_interval must be an integer")
        if value < 0:
            raise ValidationError("auto_save_interval must be non-negative")
        if value > 3600:
            raise ValidationError("auto_save_interval must not exceed 3600 seconds")
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config_dict = self.config
        
        for k in keys[:-1]:
            if k not in config_dict:
                config_dict[k] = {}
            config_dict = config_dict[k]
        
        config_dict[keys[-1]] = value