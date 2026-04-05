"""
API Data Models

Defines OpenAI-compatible request and response models using Pydantic
"""

from typing import List, Optional, Union, Dict, Any, Literal
from pydantic import BaseModel, Field
import time
import uuid


class ChatContentPart(BaseModel):
    """Chat content part for multimodal support"""
    type: Literal["text", "image_url"]
    text: Optional[str] = None
    image_url: Optional[Dict[str, str]] = None


class ChatMessage(BaseModel):
    """Chat message model"""
    role: Literal["system", "user", "assistant"]
    content: Union[str, List[ChatContentPart]]


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request"""
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    stream: Optional[bool] = False
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    stop: Optional[Union[str, List[str]]] = None
    user: Optional[str] = None


class ChatCompletionChoice(BaseModel):
    """Chat completion choice"""
    index: int
    message: ChatMessage
    finish_reason: Literal["stop", "length", "content_filter"] = "stop"


class Usage(BaseModel):
    """Token usage information (estimated)"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response"""
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[Usage] = None


class ChatCompletionStreamChoice(BaseModel):
    """Streaming chat completion choice"""
    index: int
    delta: Dict[str, Any]
    finish_reason: Optional[Literal["stop", "length", "content_filter"]] = None


class ChatCompletionStreamResponse(BaseModel):
    """OpenAI-compatible streaming response"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionStreamChoice]


class ErrorDetail(BaseModel):
    """Error detail information"""
    message: str
    type: str
    param: Optional[str] = None
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: ErrorDetail


class ModelInfo(BaseModel):
    """Model information"""
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "gemini-cli-sdk"


class ModelsResponse(BaseModel):
    """Models list response"""
    object: str = "list"
    data: List[ModelInfo]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str
    timestamp: int = Field(default_factory=lambda: int(time.time()))
    sdk_info: Optional[Dict[str, Any]] = None
