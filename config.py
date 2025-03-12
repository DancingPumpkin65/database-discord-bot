import json
import os
from typing import Dict, Any, Optional

class GuildConfig:
    """Configuration manager for guild-specific settings"""
    
    def __init__(self, data_file: str = "guild_config.json"):
        """Initialize the configuration manager"""
        self.data_file = data_file
        self.config: Dict[str, Dict[str, Any]] = {}
        self.load_config()
        
        # Default configuration
        self.defaults = {
            "prefix": "!",
            "welcome_enabled": True,
            "welcome_message": "Welcome {user} to {server}!",
            "welcome_channel": None,
            "log_enabled": False,
            "log_channel": None,
            "automod_enabled": False,
            "automod_banned_words": [],
            "automod_warn_threshold": 3,
            "automod_mute_minutes": 10,
        }
    
    def load_config(self) -> None:
        """Load configuration from the data file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"Error loading configuration: {str(e)}")
                self.config = {}
    
    def save_config(self) -> None:
        """Save configuration to the data file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving configuration: {str(e)}")
    
    def get(self, guild_id: str, key: str) -> Any:
        """Get a configuration value for a guild"""
        # Convert guild_id to string for JSON compatibility
        guild_id = str(guild_id)
        
        if guild_id not in self.config:
            # Initialize with defaults if guild has no config
            return self.defaults.get(key)
            
        return self.config[guild_id].get(key, self.defaults.get(key))
    
    def set(self, guild_id: str, key: str, value: Any) -> None:
        """Set a configuration value for a guild"""
        # Convert guild_id to string for JSON compatibility
        guild_id = str(guild_id)
        
        if guild_id not in self.config:
            self.config[guild_id] = {}
            
        self.config[guild_id][key] = value
        self.save_config()
    
    def get_all(self, guild_id: str) -> Dict[str, Any]:
        """Get all configuration values for a guild"""
        # Convert guild_id to string for JSON compatibility
        guild_id = str(guild_id)
        
        result = self.defaults.copy()
        if guild_id in self.config:
            # Override defaults with guild-specific settings
            result.update(self.config[guild_id])
            
        return result
        
    def reset(self, guild_id: str, key: Optional[str] = None) -> None:
        """Reset configuration for a guild"""
        # Convert guild_id to string for JSON compatibility
        guild_id = str(guild_id)
        
        if guild_id not in self.config:
            return
            
        if key:
            # Reset only the specified key
            if key in self.config[guild_id]:
                del self.config[guild_id][key]
        else:
            # Reset all configuration for the guild
            del self.config[guild_id]
            
        self.save_config()
