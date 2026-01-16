"""Gemini CLI SDK - A Python SDK for interacting with Gemini CLI.

This SDK provides a high-level interface for managing Gemini CLI processes,
maintaining conversation sessions, and handling concurrent interactions.

Example usage:
    import asyncio
    from gemini_cli_sdk import GeminiClient
    
    async def main():
        async with GeminiClient() as client:
            # Simple one-shot query
            response = await client.one_shot("What is Python?")
            print(f"One-shot response: {response.content}")
            
            # Create a session for contextual conversation
            session_id = client.create_session()
            
            # Chat with context
            response1 = await client.chat("Hello, I'm learning programming", session_id)
            print(f"AI (session 1): {response1.content}")
            
            response2 = await client.chat("Can you give me some tips?", session_id)
            print(f"AI (session 2): {response2.content}")

            # Streamed response
            print("\n--- Streaming Response Example ---")
            print("AI (streamed): ", end="")
            async for chunk in await client.chat("Tell me a short story.", stream=True):
                print(chunk, end="", flush=True)
            print("\n----------------------------------")
            
    asyncio.run(main())
"""

__version__ = "1.0.5"
__author__ = "Gemini CLI SDK Team"
__email__ = "support@example.com"
__description__ = "A Python SDK for interacting with Gemini CLI"
__url__ = "https://github.com/example/gemini-cli-sdk"

# Core client
from .client import GeminiClient

# Session management
from .session import SessionManager

# Data models
from .models import (
    GeminiResponse,
    GeminiConfig,
    SessionInfo,
    Message,
    MessageRole,
    ProcessStatus,
    ProcessInfo
)

# Exceptions
from .exceptions import (
    GeminiSDKError,
    GeminiProcessError,
    GeminiSessionError,
    GeminiConfigError,
    GeminiTimeoutError,
    GeminiNotFoundError,
    GeminiConnectionError,
    GeminiValidationError
)

# Configuration management
from .config import ConfigManager

# Utility functions
from .utils import (
    validate_session_id,
    format_timestamp,
    sanitize_message,
    format_duration,
    get_env_config
)

# Public API
__all__ = [
    # Core client
    'GeminiClient',
    
    # Session management
    'SessionManager',
    
    # Data models
    'GeminiResponse',
    'GeminiConfig',
    'SessionInfo',
    'Message',
    'MessageRole',
    'ProcessStatus',
    'ProcessInfo',
    
    # Exceptions
    'GeminiSDKError',
    'GeminiProcessError',
    'GeminiSessionError',
    'GeminiConfigError',
    'GeminiTimeoutError',
    'GeminiNotFoundError',
    'GeminiConnectionError',
    'GeminiValidationError',
    
    # Configuration
    'ConfigManager',
    
    # Utilities
    'validate_session_id',
    'format_timestamp',
    'sanitize_message',
    'format_duration',
    'get_env_config',
]

# Version info
version_info = tuple(map(int, __version__.split('.')))

def get_version() -> str:
    """Get the SDK version.
    
    Returns:
        str: Version string
    """
    return __version__

def get_version_info() -> tuple:
    """Get the SDK version as a tuple.
    
    Returns:
        tuple: Version tuple (major, minor, patch)
    """
    return version_info
