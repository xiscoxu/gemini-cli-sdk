"""
API Configuration Module

Manages configuration for the Gemini CLI SDK API server
"""

import os
from typing import List
from pydantic import BaseModel, Field


class APIConfig(BaseModel):
    """API Server Configuration"""

    # Server settings
    host: str = Field(default="127.0.0.1", description="Server host address")
    port: int = Field(default=8765, description="Server port")

    # Rate limiting
    rate_limit: int = Field(default=60, description="Max requests per minute")
    max_concurrency: int = Field(default=4, description="Max concurrent requests")

    # Timeouts
    timeout: float = Field(default=30.0, description="Request timeout in seconds")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Supported models
    supported_models: List[str] = Field(
        default=[
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ],
        description="List of supported Gemini models"
    )

    # SDK settings
    max_processes: int = Field(default=5, description="Max Gemini CLI processes")
    max_context_length: int = Field(default=10, description="Max conversation context length")

    class Config:
        env_prefix = "GEMINI_API_"


# Global configuration instance
config = APIConfig()


def update_config(**kwargs):
    """Update configuration from keyword arguments"""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)


def load_config_from_env():
    """Load configuration from environment variables"""
    global config
    config = APIConfig()
    return config
