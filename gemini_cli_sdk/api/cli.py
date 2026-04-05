"""
CLI Entry Point for API Server

Provides command-line interface for starting the Gemini CLI SDK API server
"""

import argparse
import sys
import logging
import uvicorn

from . import __version__
from .config import config, update_config


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Gemini CLI SDK API Server - OpenAI-compatible API for Gemini CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Gemini CLI SDK API v{__version__}"
    )

    parser.add_argument(
        "--host",
        type=str,
        default=config.host,
        help="Server host address"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=config.port,
        help="Server port"
    )

    parser.add_argument(
        "--rate-limit",
        type=int,
        default=config.rate_limit,
        help="Maximum requests per minute"
    )

    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=config.max_concurrency,
        help="Maximum concurrent requests"
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=config.timeout,
        help="Request timeout in seconds"
    )

    parser.add_argument(
        "--max-processes",
        type=int,
        default=config.max_processes,
        help="Maximum Gemini CLI processes"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=config.log_level,
        help="Logging level"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (development only)"
    )

    return parser.parse_args()


def main():
    """Main entry point for the API server"""
    args = parse_args()

    # Update configuration from command line arguments
    update_config(
        host=args.host,
        port=args.port,
        rate_limit=args.rate_limit,
        max_concurrency=args.max_concurrency,
        timeout=args.timeout,
        max_processes=args.max_processes,
        log_level=args.log_level,
        debug=args.debug
    )

    # Configure logging
    log_level = logging.DEBUG if args.debug else getattr(logging, args.log_level.upper())
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger('gemini_api')

    # Display startup information
    print(f"\n{'='*60}")
    print(f"  Gemini CLI SDK API Server v{__version__}")
    print(f"{'='*60}")
    print(f"  Host:              {args.host}")
    print(f"  Port:              {args.port}")
    print(f"  Rate Limit:        {args.rate_limit} requests/minute")
    print(f"  Max Concurrency:   {args.max_concurrency}")
    print(f"  Request Timeout:   {args.timeout}s")
    print(f"  Max Processes:     {args.max_processes}")
    print(f"  Log Level:         {args.log_level}")
    print(f"  Debug Mode:        {args.debug}")
    print(f"{'='*60}\n")
    print(f"  API Documentation: http://{args.host}:{args.port}/docs")
    print(f"  Health Check:      http://{args.host}:{args.port}/health")
    print(f"  OpenAPI Spec:      http://{args.host}:{args.port}/openapi.json")
    print(f"{'='*60}\n")

    logger.info("Starting Gemini CLI SDK API Server...")

    try:
        # Start the server
        uvicorn.run(
            "gemini_cli_sdk.api.server:app",
            host=args.host,
            port=args.port,
            log_level=args.log_level.lower(),
            reload=args.reload,
            access_log=args.debug
        )
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
