"""Custom exceptions for Gemini CLI SDK."""


class GeminiSDKError(Exception):
    """Base exception for Gemini SDK."""
    pass


class GeminiProcessError(GeminiSDKError):
    """Exception raised when Gemini process fails."""
    pass


class GeminiSessionError(GeminiSDKError):
    """Exception raised for session-related errors."""
    pass


class GeminiConfigError(GeminiSDKError):
    """Exception raised for configuration errors."""
    pass


class GeminiTimeoutError(GeminiSDKError):
    """Exception raised when operations timeout."""
    pass


class GeminiNotFoundError(GeminiSDKError):
    """Exception raised when Gemini CLI is not found."""
    pass


class GeminiConnectionError(GeminiSDKError):
    """Exception raised when connection to Gemini process fails."""
    pass


class GeminiValidationError(GeminiSDKError):
    """Exception raised when input validation fails."""
    pass
