"""Data models for Gemini CLI SDK."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import time


class ProcessStatus(Enum):
    """Status of a Gemini process."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"


class MessageRole(Enum):
    """Role of a message in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """A message in a conversation."""
    role: MessageRole
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeminiResponse:
    """Response from Gemini CLI."""
    content: str
    session_id: Optional[str] = None
    process_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionInfo:
    """Information about a conversation session."""
    session_id: str
    created_at: float
    last_activity: float
    message_count: int
    process_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeminiConfig:
    """Configuration for Gemini CLI SDK."""
    max_processes: int = 5
    idle_timeout: int = 300
    max_context_length: int = 50
    gemini_command: str = "gemini"
    gemini_args: List[str] = field(default_factory=lambda: ["--interactive", "--json-output"])
    enable_logging: bool = True
    log_level: str = "INFO"
    response_timeout: float = 30.0
    cleanup_interval: int = 60


@dataclass
class ProcessInfo:
    """Information about a Gemini process."""
    process_id: str
    status: ProcessStatus
    created_at: float
    last_used: float
    message_count: int
    session_id: Optional[str] = None
