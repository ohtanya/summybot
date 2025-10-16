"""
Configuration management for SummyBot
"""

import os
import json
from typing import Dict, List, Optional
from pathlib import Path

class Config:
    """Configuration manager for the bot"""
    
    # Bot settings
    COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
    SUMMARY_TIME_HOUR = int(os.getenv('SUMMARY_TIME_HOUR', '23'))
    SUMMARY_TIME_MINUTE = int(os.getenv('SUMMARY_TIME_MINUTE', '0'))
    
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Paths
    DATA_DIR = Path('data')
    CONFIG_FILE = DATA_DIR / 'guild_configs.json'
    
    def __init__(self):
        # Ensure data directory exists
        self.DATA_DIR.mkdir(exist_ok=True)
        
        # Load guild configurations
        self._guild_configs = self._load_guild_configs()
    
    def _load_guild_configs(self) -> Dict:
        """Load guild configurations from file"""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading guild configs: {e}")
        
        return {}
    
    def _save_guild_configs(self):
        """Save guild configurations to file"""
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self._guild_configs, f, indent=2)
        except Exception as e:
            print(f"Error saving guild configs: {e}")
    
    @classmethod
    def get_guild_config(cls, guild_id: int) -> Optional[Dict]:
        """Get configuration for a specific guild"""
        instance = cls()
        return instance._guild_configs.get(str(guild_id))
    
    @classmethod
    def set_guild_config(cls, guild_id: int, config: Dict):
        """Set configuration for a specific guild"""
        instance = cls()
        instance._guild_configs[str(guild_id)] = config
        instance._save_guild_configs()
    
    @classmethod
    def add_monitored_channel(cls, guild_id: int, channel_id: int):
        """Add a channel to the monitored channels list"""
        config = cls.get_guild_config(guild_id) or {
            'monitored_channels': [],
            'summary_channel_id': None
        }
        
        if channel_id not in config['monitored_channels']:
            config['monitored_channels'].append(channel_id)
            cls.set_guild_config(guild_id, config)
    
    @classmethod
    def remove_monitored_channel(cls, guild_id: int, channel_id: int):
        """Remove a channel from the monitored channels list"""
        config = cls.get_guild_config(guild_id)
        if config and channel_id in config['monitored_channels']:
            config['monitored_channels'].remove(channel_id)
            cls.set_guild_config(guild_id, config)
    
    @classmethod
    def set_summary_channel(cls, guild_id: int, channel_id: int):
        """Set the summary channel for a guild"""
        config = cls.get_guild_config(guild_id) or {
            'monitored_channels': [],
            'summary_channel_id': None
        }
        
        config['summary_channel_id'] = channel_id
        cls.set_guild_config(guild_id, config)
    
    @classmethod
    def get_monitored_channels(cls, guild_id: int) -> List[int]:
        """Get list of monitored channels for a guild"""
        config = cls.get_guild_config(guild_id)
        return config['monitored_channels'] if config else []
    
    @classmethod
    def get_summary_channel(cls, guild_id: int) -> Optional[int]:
        """Get the summary channel for a guild"""
        config = cls.get_guild_config(guild_id)
        return config['summary_channel_id'] if config else None
