"""
FastAPI Server Module

Implements OpenAI-compatible REST API endpoints for Gemini CLI SDK
"""

import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .. import __version__ as sdk_version
from . import __version__ as api_version
from .config import config
from .models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ErrorResponse,
    ErrorDetail,
    HealthResponse,
    ModelsResponse,
    ModelInfo
)
from .openai_adapter import openai_adapter

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gemini_api')

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info(f"Starting Gemini CLI SDK API Server v{api_version}")
    logger.info(f"SDK Version: {sdk_version}")
    logger.info(
        f"Config: host={config.host}:{config.port}, "
        f"rate_limit={config.rate_limit}/min, "
        f"max_concurrency={config.max_concurrency}"
    )

    # Start the adapter (which starts the Gemini client)
    await openai_adapter.start()
    logger.info("OpenAI adapter started")

    yield

    # Cleanup
    await openai_adapter.stop()
    logger.info("Gemini CLI SDK API Server stopped")


# Create FastAPI application
app = FastAPI(
    title="Gemini CLI SDK API",
    description="OpenAI-compatible API for Gemini CLI SDK with advanced session management",
    version=api_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    error_response = ErrorResponse(
        error=ErrorDetail(
            message="Internal server error",
            type="internal_error",
            code="500"
        )
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Gemini CLI SDK API",
        "version": api_version,
        "sdk_version": sdk_version,
        "status": "running",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    stats = openai_adapter.get_stats()
    return HealthResponse(
        status="healthy",
        version=api_version,
        sdk_info={
            "version": sdk_version,
            "adapter_stats": stats
        }
    )


@app.get("/v1/models", response_model=ModelsResponse)
async def list_models():
    """List available models (OpenAI-compatible endpoint)"""
    models = [
        ModelInfo(id=model_id)
        for model_id in config.supported_models
    ]
    return ModelsResponse(data=models)


@app.post("/v1/chat/completions")
@limiter.limit(f"{config.rate_limit}/minute")
async def chat_completions(
    chat_request: ChatCompletionRequest,
    request: Request
):
    """
    Chat completion endpoint (OpenAI-compatible)

    Supports both streaming and non-streaming requests.
    """
    logger.info(
        f"Received chat completion request: model={chat_request.model}, "
        f"stream={chat_request.stream}, messages={len(chat_request.messages)}"
    )

    try:
        # Validate model
        if chat_request.model not in config.supported_models:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        message=f"Unsupported model: {chat_request.model}. "
                                f"Supported models: {', '.join(config.supported_models)}",
                        type="invalid_request_error",
                        param="model"
                    )
                ).model_dump()
            )

        # Validate messages
        if not chat_request.messages:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        message="Messages list cannot be empty",
                        type="invalid_request_error",
                        param="messages"
                    )
                ).model_dump()
            )

        # Handle streaming request
        if chat_request.stream:
            return await openai_adapter.chat_completion_stream(chat_request)

        # Handle non-streaming request
        response = await openai_adapter.chat_completion(chat_request)
        return response

    except HTTPException:
        raise
    except asyncio.TimeoutError:
        logger.error("Request timeout")
        raise HTTPException(
            status_code=504,
            detail=ErrorResponse(
                error=ErrorDetail(
                    message="Request timeout. Please try again.",
                    type="timeout_error",
                    code="504"
                )
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=ErrorDetail(
                    message=str(e),
                    type="internal_error",
                    code="500"
                )
            ).model_dump()
        )


@app.get("/stats")
async def get_stats():
    """Get server and adapter statistics"""
    return {
        "api_version": api_version,
        "sdk_version": sdk_version,
        "config": {
            "max_concurrency": config.max_concurrency,
            "rate_limit": config.rate_limit,
            "timeout": config.timeout,
            "max_processes": config.max_processes
        },
        "adapter": openai_adapter.get_stats()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower()
    )
