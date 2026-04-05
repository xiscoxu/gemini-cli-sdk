"""
OpenAI Adapter Module

Converts between OpenAI API format and Gemini CLI SDK format
"""

import logging
import time
import uuid
from typing import AsyncGenerator
from fastapi.responses import StreamingResponse

from ..client import GeminiClient
from ..models import GeminiConfig
from .models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionStreamResponse,
    ChatCompletionStreamChoice,
    ChatMessage as APIChatMessage,
    Usage
)
from .config import config

logger = logging.getLogger('gemini_api')


class OpenAIAdapter:
    """Adapter for OpenAI-compatible API format"""

    def __init__(self):
        """Initialize adapter with Gemini client"""
        sdk_config = GeminiConfig(
            max_processes=config.max_processes,
            max_context_length=config.max_context_length,
            response_timeout=config.timeout
        )
        self.client = GeminiClient(config=sdk_config)
        self._started = False
        self._sessions = {}  # Track sessions per user

    async def start(self):
        """Start the Gemini client"""
        if not self._started:
            await self.client.start()
            self._started = True
            logger.info("OpenAI Adapter started")

    async def stop(self):
        """Stop the Gemini client"""
        if self._started:
            await self.client.stop()
            self._started = False
            logger.info("OpenAI Adapter stopped")

    def _get_or_create_session(self, user_id: str = None) -> str:
        """Get or create a session for a user"""
        user_key = user_id or "default"
        if user_key not in self._sessions:
            self._sessions[user_key] = self.client.create_session(
                user_id=user_key,
                metadata={"created_via": "api"}
            )
        return self._sessions[user_key]

    def _convert_messages_to_text(self, messages: list) -> tuple[str, str]:
        """Convert OpenAI message format to text prompt"""
        system_instruction = None
        user_messages = []

        for msg in messages:
            content = msg.content
            if isinstance(content, list):
                # Handle multimodal content
                text_parts = [part.text for part in content if part.type == "text" and part.text]
                content = " ".join(text_parts)

            if msg.role == "system":
                system_instruction = content
            elif msg.role == "user":
                user_messages.append(f"User: {content}")
            elif msg.role == "assistant":
                user_messages.append(f"Assistant: {content}")

        prompt = "\n".join(user_messages)
        return prompt, system_instruction

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough estimate: ~4 characters per token
        return max(1, len(text) // 4)

    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Handle non-streaming chat completion request"""
        logger.info(
            f"Processing chat completion: model={request.model}, "
            f"messages={len(request.messages)}, stream=False"
        )

        try:
            # Ensure client is started
            if not self._started:
                await self.start()

            # Get or create session for the user
            session_id = self._get_or_create_session(request.user)

            # Convert last message to prompt
            last_message = request.messages[-1]
            if isinstance(last_message.content, list):
                text_parts = [
                    part.text for part in last_message.content
                    if part.type == "text" and part.text
                ]
                prompt = " ".join(text_parts)
            else:
                prompt = last_message.content

            # Extract system instruction if present
            system_instruction = None
            for msg in request.messages:
                if msg.role == "system":
                    system_instruction = msg.content
                    break

            # Send message through SDK
            response = await self.client.send_message(
                message=prompt,
                session_id=session_id,
                system_instruction=system_instruction,
                maintain_context=True,
                stream=False
            )

            # Estimate token usage
            prompt_tokens = sum(
                self._estimate_tokens(
                    msg.content if isinstance(msg.content, str) else str(msg.content)
                )
                for msg in request.messages
            )
            completion_tokens = self._estimate_tokens(response.content)

            # Build OpenAI-compatible response
            api_response = ChatCompletionResponse(
                model=request.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=APIChatMessage(
                            role="assistant",
                            content=response.content
                        ),
                        finish_reason="stop"
                    )
                ],
                usage=Usage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens
                )
            )

            logger.info(
                f"Chat completion successful: response_length={len(response.content)}, "
                f"tokens={api_response.usage.total_tokens}"
            )
            return api_response

        except Exception as e:
            logger.error(f"Error in chat completion: {e}", exc_info=True)
            raise

    async def chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> StreamingResponse:
        """Handle streaming chat completion request"""
        logger.info(
            f"Processing streaming chat completion: model={request.model}, "
            f"messages={len(request.messages)}"
        )

        async def generate_stream():
            """Generate SSE streaming response"""
            completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
            created_time = int(time.time())

            try:
                # Ensure client is started
                if not self._started:
                    await self.start()

                # Get or create session
                session_id = self._get_or_create_session(request.user)

                # Convert last message to prompt
                last_message = request.messages[-1]
                if isinstance(last_message.content, list):
                    text_parts = [
                        part.text for part in last_message.content
                        if part.type == "text" and part.text
                    ]
                    prompt = " ".join(text_parts)
                else:
                    prompt = last_message.content

                # Extract system instruction
                system_instruction = None
                for msg in request.messages:
                    if msg.role == "system":
                        system_instruction = msg.content
                        break

                # Get streaming response from SDK
                stream_response = await self.client.send_message(
                    message=prompt,
                    session_id=session_id,
                    system_instruction=system_instruction,
                    maintain_context=True,
                    stream=True
                )

                # Stream chunks to client
                async for chunk in stream_response:
                    stream_chunk = ChatCompletionStreamResponse(
                        id=completion_id,
                        created=created_time,
                        model=request.model,
                        choices=[
                            ChatCompletionStreamChoice(
                                index=0,
                                delta={"content": chunk},
                                finish_reason=None
                            )
                        ]
                    )
                    yield f"data: {stream_chunk.model_dump_json()}\n\n"

                # Send final chunk with finish_reason
                final_chunk = ChatCompletionStreamResponse(
                    id=completion_id,
                    created=created_time,
                    model=request.model,
                    choices=[
                        ChatCompletionStreamChoice(
                            index=0,
                            delta={},
                            finish_reason="stop"
                        )
                    ]
                )
                yield f"data: {final_chunk.model_dump_json()}\n\n"
                yield "data: [DONE]\n\n"

                logger.info("Streaming chat completion successful")

            except Exception as e:
                logger.error(f"Error in streaming completion: {e}", exc_info=True)
                # Send error in SSE format
                error_data = {
                    "error": {
                        "message": str(e),
                        "type": "internal_error"
                    }
                }
                yield f"data: {error_data}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    def get_stats(self) -> dict:
        """Get adapter statistics"""
        return {
            "started": self._started,
            "active_sessions": len(self._sessions),
            "sdk_stats": self.client.get_stats() if self._started else {}
        }


# Global adapter instance
openai_adapter = OpenAIAdapter()
