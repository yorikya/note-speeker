import json
import os
from kivy.utils import platform


class ConfigService:
    """Service to handle user configuration persistence"""
    
    def __init__(self):
        self.config_file = self._get_config_file_path()
        self.default_config = {
            'language': 'en-US',
            'silence_timeout': 5,
            'recording_timeout': 600,  # 10 minutes in seconds
            'theme': 'default'
        }
        self.config = self.load_config()
    
    def _get_config_file_path(self):
        """Get the appropriate config file path based on platform"""
        if platform == 'android':
            # On Android, use app's private storage
            from android.storage import primary_external_storage_path
            config_dir = primary_external_storage_path()
        else:
            # On desktop, use current directory or user home
            config_dir = os.path.expanduser('~')
        
        # Create config directory if it doesn't exist
        config_path = os.path.join(config_dir, '.note_speaker')
        if not os.path.exists(config_path):
            try:
                os.makedirs(config_path)
            except:
                # Fallback to current directory if we can't create in home
                config_path = '.'
        
        return os.path.join(config_path, 'config.json')
    
    def load_config(self):
        """Load configuration from file, return defaults if file doesn't exist"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    merged_config = self.default_config.copy()
                    merged_config.update(config)
                    return merged_config
        except Exception as e:
            print(f"Error loading config: {e}")
        
        return self.default_config.copy()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"Config saved to: {self.config_file}")
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key, default=None):
        """Get a configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value (no autosave)"""
        self.config[key] = value
    
    def get_language(self):
        """Get the current language setting"""
        return self.get('language', 'en-US')
    
    def set_language(self, language_code):
        """Set the language (no autosave)"""
        self.set('language', language_code)
    
    def get_silence_timeout(self):
        """Get the silence timeout setting"""
        return self.get('silence_timeout', 5)
    
    def set_silence_timeout(self, timeout):
        """Set the silence timeout (no autosave)"""
        self.set('silence_timeout', timeout)
    
    def get_recording_timeout(self):
        """Get the recording timeout setting"""
        return self.get('recording_timeout', 600)
    
    def set_recording_timeout(self, timeout):
        """Set the recording timeout (no autosave)"""
        self.set('recording_timeout', timeout) 