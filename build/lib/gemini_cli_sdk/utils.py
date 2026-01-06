"""Utility functions for Gemini CLI SDK."""

import os
import time
import asyncio
from typing import Optional, Dict, Any, List
from .exceptions import GeminiValidationError


def validate_session_id(session_id: str) -> bool:
    """Validate session ID format.
    
    Args:
        session_id: Session ID to validate
        
    Returns:
        bool: True if valid
    """
    if not session_id or not isinstance(session_id, str):
        return False
    
    # Basic UUID format check
    parts = session_id.split('-')
    if len(parts) != 5:
        return False
    
    expected_lengths = [8, 4, 4, 4, 12]
    for part, expected_length in zip(parts, expected_lengths):
        if len(part) != expected_length or not all(c.isalnum() for c in part):
            return False
    
    return True


def format_timestamp(timestamp: float) -> str:
    """Format timestamp for display.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        str: Formatted timestamp
    """
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))


def sanitize_message(message: str) -> str:
    """Sanitize message content.
    
    Args:
        message: Raw message content
        
    Returns:
        str: Sanitized message
    """
    if not message:
        return ""
    
    # Remove control characters except newlines and tabs
    sanitized = ''.join(char for char in message 
                       if ord(char) >= 32 or char in '\n\t')
    
    # Limit message length
    max_length = 10000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "... [truncated]"
    
    return sanitized.strip()


def parse_gemini_args(args_string: str) -> List[str]:
    """Parse Gemini CLI arguments from string.
    
    Args:
        args_string: Space-separated arguments string
        
    Returns:
        List[str]: List of arguments
    """
    if not args_string:
        return []
    
    # Simple split for now - could be enhanced for quoted arguments
    return [arg.strip() for arg in args_string.split() if arg.strip()]


def merge_metadata(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Merge metadata dictionaries.
    
    Args:
        base: Base metadata dictionary
        update: Update metadata dictionary
        
    Returns:
        Dict: Merged metadata
    """
    result = base.copy()
    result.update(update)
    return result


def calculate_context_size(messages: List) -> int:
    """Calculate approximate size of context in characters.
    
    Args:
        messages: List of message objects
        
    Returns:
        int: Approximate character count
    """
    total_size = 0
    for message in messages:
        if hasattr(message, 'content'):
            total_size += len(str(message.content))
    return total_size


def truncate_context(messages: List, max_size: int = 50000) -> List:
    """Truncate context to fit within size limit.
    
    Args:
        messages: List of message objects
        max_size: Maximum size in characters
        
    Returns:
        List: Truncated message list
    """
    if not messages:
        return messages
    
    current_size = calculate_context_size(messages)
    if current_size <= max_size:
        return messages
    
    # Remove oldest messages until under limit
    truncated = messages[:]
    while truncated and calculate_context_size(truncated) > max_size:
        truncated.pop(0)
    
    return truncated


def is_valid_config_key(key: str) -> bool:
    """Check if a configuration key is valid.
    
    Args:
        key: Configuration key to check
        
    Returns:
        bool: True if valid
    """
    valid_keys = {
        'max_processes', 'idle_timeout', 'max_context_length',
        'gemini_command', 'gemini_args', 'enable_logging',
        'log_level', 'response_timeout', 'cleanup_interval'
    }
    return key in valid_keys


def validate_config_value(key: str, value: Any) -> bool:
    """Validate a configuration value.
    
    Args:
        key: Configuration key
        value: Value to validate
        
    Returns:
        bool: True if valid
        
    Raises:
        GeminiValidationError: If validation fails
    """
    if key == 'max_processes':
        if not isinstance(value, int) or value < 1 or value > 20:
            raise GeminiValidationError("max_processes must be an integer between 1 and 20")
    
    elif key == 'idle_timeout':
        if not isinstance(value, int) or value < 60:
            raise GeminiValidationError("idle_timeout must be an integer >= 60 seconds")
    
    elif key == 'max_context_length':
        if not isinstance(value, int) or value < 1 or value > 1000:
            raise GeminiValidationError("max_context_length must be an integer between 1 and 1000")
    
    elif key == 'gemini_command':
        if not isinstance(value, str) or not value.strip():
            raise GeminiValidationError("gemini_command must be a non-empty string")
    
    elif key == 'gemini_args':
        if not isinstance(value, list) or not all(isinstance(arg, str) for arg in value):
            raise GeminiValidationError("gemini_args must be a list of strings")
    
    elif key == 'enable_logging':
        if not isinstance(value, bool):
            raise GeminiValidationError("enable_logging must be a boolean")
    
    elif key == 'log_level':
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if not isinstance(value, str) or value.upper() not in valid_levels:
            raise GeminiValidationError(f"log_level must be one of: {', '.join(valid_levels)}")
    
    elif key == 'response_timeout':
        if not isinstance(value, (int, float)) or value <= 0:
            raise GeminiValidationError("response_timeout must be a positive number")
    
    elif key == 'cleanup_interval':
        if not isinstance(value, int) or value < 10:
            raise GeminiValidationError("cleanup_interval must be an integer >= 10 seconds")
    
    return True


async def wait_for_condition(condition_func, timeout: float = 30.0, 
                           interval: float = 0.1) -> bool:
    """Wait for a condition to become true.
    
    Args:
        condition_func: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        interval: Check interval in seconds
        
    Returns:
        bool: True if condition was met, False if timeout
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        await asyncio.sleep(interval)
    
    return False


def get_env_config() -> Dict[str, Any]:
    """Get configuration from environment variables.
    
    Returns:
        Dict: Configuration from environment
    """
    config = {}
    
    # Integer values
    for key in ['GEMINI_MAX_PROCESSES', 'GEMINI_IDLE_TIMEOUT', 
                'GEMINI_MAX_CONTEXT_LENGTH', 'GEMINI_CLEANUP_INTERVAL']:
        value = os.getenv(key)
        if value:
            try:
                config[key.lower().replace('gemini_', '')] = int(value)
            except ValueError:
                pass
    
    # Float values
    for key in ['GEMINI_RESPONSE_TIMEOUT']:
        value = os.getenv(key)
        if value:
            try:
                config[key.lower().replace('gemini_', '')] = float(value)
            except ValueError:
                pass
    
    # String values
    for key in ['GEMINI_COMMAND', 'GEMINI_LOG_LEVEL']:
        value = os.getenv(key)
        if value:
            config[key.lower().replace('gemini_', '')] = value
    
    # Boolean values
    for key in ['GEMINI_ENABLE_LOGGING']:
        value = os.getenv(key)
        if value:
            config[key.lower().replace('gemini_', '')] = value.lower() in ('true', '1', 'yes', 'on')
    
    # List values
    gemini_args = os.getenv('GEMINI_ARGS')
    if gemini_args:
        config['gemini_args'] = parse_gemini_args(gemini_args)
    
    return config


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def safe_filename(filename: str) -> str:
    """Create a safe filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Safe filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    safe_name = filename
    
    for char in invalid_chars:
        safe_name = safe_name.replace(char, '_')
    
    # Remove leading/trailing dots and spaces
    safe_name = safe_name.strip('. ')
    
    # Ensure not empty
    if not safe_name:
        safe_name = 'unnamed'
    
    return safe_name
