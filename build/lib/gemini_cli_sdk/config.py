"""Configuration management for Gemini CLI SDK."""

import os
import json
import logging
from typing import Optional, Dict, Any
from .models import GeminiConfig
from .exceptions import GeminiConfigError


class ConfigManager:
    """Manages configuration for Gemini CLI SDK."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file. Defaults to ~/.gemini_cli_sdk.json
        """
        self.config_file = config_file or os.path.expanduser("~/.gemini_cli_sdk.json")
        self._config: Optional[GeminiConfig] = None
        self._logger = logging.getLogger(__name__)
    
    def load_config(self) -> GeminiConfig:
        """Load configuration from file and environment variables.
        
        Returns:
            GeminiConfig: Loaded configuration
            
        Raises:
            GeminiConfigError: If configuration loading fails
        """
        if self._config is not None:
            return self._config
        
        # Start with default configuration
        config_dict = {}
        
        # Load from file if it exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    config_dict.update(file_config)
                    self._logger.info(f"Loaded configuration from {self.config_file}")
            except (json.JSONDecodeError, IOError) as e:
                raise GeminiConfigError(f"Failed to load config file {self.config_file}: {e}")
        
        # Override with environment variables
        env_overrides = {
            'max_processes': self._get_env_int('GEMINI_MAX_PROCESSES'),
            'idle_timeout': self._get_env_int('GEMINI_IDLE_TIMEOUT'),
            'max_context_length': self._get_env_int('GEMINI_MAX_CONTEXT_LENGTH'),
            'gemini_command': os.getenv('GEMINI_COMMAND'),
            'log_level': os.getenv('GEMINI_LOG_LEVEL'),
            'response_timeout': self._get_env_float('GEMINI_RESPONSE_TIMEOUT'),
            'cleanup_interval': self._get_env_int('GEMINI_CLEANUP_INTERVAL'),
            'enable_logging': self._get_env_bool('GEMINI_ENABLE_LOGGING'),
        }
        
        # Apply non-None environment overrides
        for key, value in env_overrides.items():
            if value is not None:
                config_dict[key] = value
        
        # Handle gemini_args from environment
        gemini_args_env = os.getenv('GEMINI_ARGS')
        if gemini_args_env:
            config_dict['gemini_args'] = gemini_args_env.split()
        
        try:
            self._config = GeminiConfig(**config_dict)
            self._setup_logging()
            return self._config
        except TypeError as e:
            raise GeminiConfigError(f"Invalid configuration parameters: {e}")
    
    def save_config(self, config: GeminiConfig):
        """Save configuration to file.
        
        Args:
            config: Configuration to save
            
        Raises:
            GeminiConfigError: If saving fails
        """
        config_dict = {
            'max_processes': config.max_processes,
            'idle_timeout': config.idle_timeout,
            'max_context_length': config.max_context_length,
            'gemini_command': config.gemini_command,
            'gemini_args': config.gemini_args,
            'enable_logging': config.enable_logging,
            'log_level': config.log_level,
            'response_timeout': config.response_timeout,
            'cleanup_interval': config.cleanup_interval,
        }
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2)
            
            self._logger.info(f"Configuration saved to {self.config_file}")
            
        except IOError as e:
            raise GeminiConfigError(f"Failed to save config file {self.config_file}: {e}")
    
    def _get_env_int(self, key: str) -> Optional[int]:
        """Get integer value from environment variable."""
        value = os.getenv(key)
        if value is not None:
            try:
                return int(value)
            except ValueError:
                self._logger.warning(f"Invalid integer value for {key}: {value}")
        return None
    
    def _get_env_float(self, key: str) -> Optional[float]:
        """Get float value from environment variable."""
        value = os.getenv(key)
        if value is not None:
            try:
                return float(value)
            except ValueError:
                self._logger.warning(f"Invalid float value for {key}: {value}")
        return None
    
    def _get_env_bool(self, key: str) -> Optional[bool]:
        """Get boolean value from environment variable."""
        value = os.getenv(key)
        if value is not None:
            return value.lower() in ('true', '1', 'yes', 'on')
        return None
    
    def _setup_logging(self):
        """Setup logging based on configuration."""
        if not self._config or not self._config.enable_logging:
            return
        
        # Configure root logger for the SDK
        logger = logging.getLogger('gemini_cli_sdk')
        logger.setLevel(getattr(logging, self._config.log_level.upper(), logging.INFO))
        
        # Add console handler if not already present
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary.
        
        Returns:
            Dict containing current configuration
        """
        config = self.load_config()
        return {
            'max_processes': config.max_processes,
            'idle_timeout': config.idle_timeout,
            'max_context_length': config.max_context_length,
            'gemini_command': config.gemini_command,
            'gemini_args': config.gemini_args,
            'enable_logging': config.enable_logging,
            'log_level': config.log_level,
            'response_timeout': config.response_timeout,
            'cleanup_interval': config.cleanup_interval,
        }
