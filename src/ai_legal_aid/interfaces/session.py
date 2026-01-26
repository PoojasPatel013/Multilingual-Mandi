"""
Session management protocols for the AI Legal Aid System.

This module defines the contract for session management, including
session lifecycle, conversation history, and privacy-compliant
data handling.
"""

from abc import abstractmethod
from typing import Protocol

from ai_legal_aid.types import SessionId, Session


class SessionManager(Protocol):
    """Protocol for managing user sessions and conversation state."""

    @abstractmethod
    async def create_session(self) -> SessionId:
        """
        Create a new user session.

        Returns:
            Unique session identifier
        """
        ...

    @abstractmethod
    async def get_session(self, session_id: SessionId) -> Session:
        """
        Retrieve session information.

        Args:
            session_id: Unique session identifier

        Returns:
            Session information

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        ...

    @abstractmethod
    async def update_session(self, session_id: SessionId, updates: dict) -> None:
        """
        Update session information.

        Args:
            session_id: Unique session identifier
            updates: Dictionary of fields to update

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        ...

    @abstractmethod
    async def end_session(self, session_id: SessionId) -> None:
        """
        End a session and perform cleanup.

        Args:
            session_id: Unique session identifier

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        ...

    @abstractmethod
    async def cleanup_expired_sessions(self) -> None:
        """
        Clean up expired sessions and associated data.

        This method should be called periodically to maintain
        privacy compliance and system performance.
        """
        ...
