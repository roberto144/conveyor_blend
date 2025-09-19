import json
import os
from typing import Dict, Any, Optional

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_file: str = "config/default_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "simulation": {
                "default_total_time": 100.0,
                "default_conveyor_length": 100.0,
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
                    "Steel", "Aluminum", "Concrete", "Sand", "Gravel", "Coal"
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
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config_dict = self.config
        
        for k in keys[:-1]:
            if k not in config_dict:
                config_dict[k] = {}
            config_dict = config_dict[k]
        
        config_dict[keys[-1]] = value