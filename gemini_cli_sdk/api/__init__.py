"""
Gemini CLI SDK API Module

Provides OpenAI-compatible REST API for Gemini CLI SDK
"""

__version__ = "1.0.0"
__author__ = "Gemini CLI SDK Team"
__description__ = "OpenAI-compatible API wrapper for Gemini CLI SDK"

from .server import app

__all__ = ['app']
