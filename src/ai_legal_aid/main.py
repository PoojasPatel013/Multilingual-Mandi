"""
Main application entry point for the AI Legal Aid System.

This module wires together all system components and provides
a complete functional legal aid application with text-based interaction.
"""

import asyncio
import sys
from typing import Optional

from ai_legal_aid.session_manager import InMemorySessionManager
from ai_legal_aid.legal_guidance_engine import BasicLegalGuidanceEngine
from ai_legal_aid.resource_directory import BasicResourceDirectory
from ai_legal_aid.disclaimer_service import BasicDisclaimerService
from ai_legal_aid.conversation_engine import BasicConversationEngine
from ai_legal_aid.types import SessionId


class AILegalAidApplication:
    """
    Main AI Legal Aid Application.
    
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
