"""
In-memory Session Manager implementation for the AI Legal Aid System.

This module provides a concrete implementation of the SessionManager protocol
using in-memory storage. It includes session lifecycle management, conversation
history tracking, and basic cleanup functionality.

This implementation is designed for development and testing. Production
deployments should use the encrypted persistent storage implementation.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

from ai_legal_aid.interfaces.session import SessionManager
from ai_legal_aid.types import SessionId, Session, UserContext


class SessionNotFoundError(Exception):
    """Raised when a session is not found."""

    def __init__(self, session_id: SessionId):
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


class InMemorySessionManager(SessionManager):
    """
    In-memory implementation of the SessionManager protocol.

    This implementation stores all session data in memory and provides
    basic CRUD operations for session management. Sessions are automatically
    expired after a configurable timeout period.

    Attributes:
        session_timeout: Time in minutes after which sessions expire
        cleanup_interval: Interval in minutes for automatic cleanup
    """

    def __init__(
        self,
        session_timeout: int = 60,  # 60 minutes default
        cleanup_interval: int = 10,  # 10 minutes default
    ):
        """
        Initialize the session manager.

        Args:
            session_timeout: Session timeout in minutes
            cleanup_interval: Cleanup interval in minutes
        """
        self._sessions: Dict[SessionId, Session] = {}
        self._session_timeout = timedelta(minutes=session_timeout)
        self._cleanup_interval = timedelta(minutes=cleanup_interval)
        self._last_cleanup = datetime.now()
        self._cleanup_lock = asyncio.Lock()

    async def create_session(self) -> SessionId:
        """
        Create a new user session with default settings.

        Returns:
            Unique session identifier
        """
        session_id = SessionId(str(uuid.uuid4()))
        now = datetime.now()

        session = Session(
            id=session_id,
            start_time=now,
            last_activity=now,
            language="en",
            conversation_history=[],
            user_context=UserContext(),
            disclaimer_acknowledged=False,
        )

        self._sessions[session_id] = session

        # Trigger cleanup if needed
        await self._maybe_cleanup()

        return session_id

    async def get_session(self, session_id: SessionId) -> Session:
        """
        Retrieve session information.

        Args:
            session_id: Unique session identifier

        Returns:
            Session information

        Raises:
            SessionNotFoundError: If session doesn't exist or has expired
        """
        if session_id not in self._sessions:
            raise SessionNotFoundError(session_id)

        session = self._sessions[session_id]

        # Check if session has expired
        if self._is_session_expired(session):
            await self._remove_session(session_id)
            raise SessionNotFoundError(session_id)

        return session

    async def update_session(self, session_id: SessionId, updates: dict) -> None:
        """
        Update session information.

        Args:
            session_id: Unique session identifier
            updates: Dictionary of fields to update

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        session = await self.get_session(session_id)

        # Update last activity time
        updates["last_activity"] = datetime.now()

        # Create updated session with new data
        session_data = session.model_dump()
        session_data.update(updates)

        # Handle nested updates for user_context
        if "user_context" in updates and isinstance(updates["user_context"], dict):
            current_context = session_data.get("user_context", {})
            if isinstance(current_context, UserContext):
                current_context = current_context.model_dump()
            current_context.update(updates["user_context"])
            session_data["user_context"] = UserContext(**current_context)

        # Validate and store updated session
        updated_session = Session(**session_data)
        self._sessions[session_id] = updated_session

    async def end_session(self, session_id: SessionId) -> None:
        """
        End a session and perform cleanup.

        Args:
            session_id: Unique session identifier

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        # Verify session exists
        await self.get_session(session_id)

        # Remove session from storage
        await self._remove_session(session_id)

    async def cleanup_expired_sessions(self) -> None:
        """
        Clean up expired sessions and associated data.

        This method removes all sessions that have exceeded the timeout
        period based on their last activity time.
        """
        async with self._cleanup_lock:
            expired_sessions = []

            for session_id, session in self._sessions.items():
                if self._is_session_expired(session):
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                await self._remove_session(session_id)

            self._last_cleanup = datetime.now()

    def _is_session_expired(self, session: Session) -> bool:
        """
        Check if a session has expired based on last activity.

        Args:
            session: Session to check

        Returns:
            True if session has expired, False otherwise
        """
        return datetime.now() - session.last_activity > self._session_timeout

    async def _remove_session(self, session_id: SessionId) -> None:
        """
        Remove a session from storage.

        Args:
            session_id: Session to remove
        """
        if session_id in self._sessions:
            del self._sessions[session_id]

    async def _maybe_cleanup(self) -> None:
        """
        Trigger cleanup if enough time has passed since last cleanup.
        """
        if datetime.now() - self._last_cleanup > self._cleanup_interval:
            await self.cleanup_expired_sessions()

    # Additional utility methods for testing and monitoring

    def get_active_session_count(self) -> int:
        """
        Get the number of currently active sessions.

        Returns:
            Number of active sessions
        """
        return len(self._sessions)

    def get_session_ids(self) -> list[SessionId]:
        """
        Get all active session IDs.

        Returns:
            List of active session IDs
        """
        return list(self._sessions.keys())

    async def clear_all_sessions(self) -> None:
        """
        Clear all sessions. Useful for testing.
        """
        self._sessions.clear()
