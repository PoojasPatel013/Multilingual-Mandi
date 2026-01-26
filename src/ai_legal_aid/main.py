"""
Main entry point for the AI Legal Aid System.

This module provides the main application entry point and basic
system initialization. The full system will be wired together
in later implementation tasks.
"""

import asyncio
import logging
import sys
from typing import Optional

import structlog
from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings and configuration."""

    # Application settings
    app_name: str = "AI Legal Aid System"
    version: str = "0.1.0"
    debug: bool = False

    # Voice interface settings
    default_language: str = "en"
    speech_timeout: int = 30  # seconds

    # Session settings
    session_timeout: int = 1800  # 30 minutes
    max_conversation_turns: int = 50

    # Database settings
    database_url: Optional[str] = None
    redis_url: Optional[str] = None

    # Security settings
    encryption_key: Optional[str] = None


def setup_logging(debug: bool = False) -> None:
    """
    Set up structured logging for the application.

    Args:
        debug: Whether to enable debug logging
    """
    log_level = logging.DEBUG if debug else logging.INFO

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )


async def initialize_system(settings: Settings) -> None:
    """
    Initialize the AI Legal Aid System components.

    Args:
        settings: Application settings
    """
    logger = structlog.get_logger(__name__)

    logger.info(
        "Initializing AI Legal Aid System",
        version=settings.version,
        debug=settings.debug,
    )

    # TODO: Initialize system components in later tasks
    # - Session manager
    # - Legal guidance engine
    # - Resource directory
    # - Voice interface components
    # - Disclaimer service

    logger.info("System initialization complete")


async def main_async() -> None:
    """
    Main async application entry point.
    """
    # Load settings
    settings = Settings()

    # Set up logging
    setup_logging(settings.debug)

    logger = structlog.get_logger(__name__)

    try:
        # Initialize the system
        await initialize_system(settings)

        logger.info(
            "AI Legal Aid System started successfully",
            app_name=settings.app_name,
            version=settings.version,
        )

        # TODO: Start the main application loop in later tasks
        # For now, just demonstrate that the system can start
        print(f"{settings.app_name} v{settings.version}")
        print("System initialized successfully!")
        print("Core interfaces and types are ready for implementation.")

    except Exception as e:
        logger.error("Failed to start AI Legal Aid System", error=str(e), exc_info=True)
        sys.exit(1)


def main() -> None:
    """
    Main application entry point.
    """
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nShutting down AI Legal Aid System...")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
