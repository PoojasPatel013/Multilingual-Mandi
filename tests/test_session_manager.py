"""
Unit tests for the InMemorySessionManager implementation.

This module tests all aspects of session management including CRUD operations,
session lifecycle, conversation history tracking, and cleanup functionality.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from ai_legal_aid.session_manager import InMemorySessionManager, SessionNotFoundError
from ai_legal_aid.types import SessionId, UserContext, LegalIssueType, UrgencyLevel


class TestInMemorySessionManager:
    """Test suite for InMemorySessionManager."""

    @pytest.fixture
    def session_manager(self):
        """Create a session manager instance for testing."""
        return InMemorySessionManager(session_timeout=60, cleanup_interval=10)

    @pytest.mark.asyncio
    async def test_create_session(self, session_manager):
        """Test creating a new session."""
        session_id = await session_manager.create_session()

        # Verify session ID is valid
        assert isinstance(session_id, str)
        assert len(session_id) > 0

        # Verify session can be retrieved
        session = await session_manager.get_session(session_id)
        assert session.id == session_id
        assert session.language == "en"
        assert session.disclaimer_acknowledged is False
        assert len(session.conversation_history) == 0
        assert isinstance(session.user_context, UserContext)

    @pytest.mark.asyncio
    async def test_create_multiple_sessions(self, session_manager):
        """Test creating multiple sessions generates unique IDs."""
        session_id1 = await session_manager.create_session()
        session_id2 = await session_manager.create_session()

        assert session_id1 != session_id2
        assert session_manager.get_active_session_count() == 2

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_manager):
        """Test getting a non-existent session raises error."""
        fake_id = SessionId("non-existent-id")

        with pytest.raises(SessionNotFoundError) as exc_info:
            await session_manager.get_session(fake_id)

        assert exc_info.value.session_id == fake_id

    @pytest.mark.asyncio
    async def test_update_session_basic_fields(self, session_manager):
        """Test updating basic session fields."""
        session_id = await session_manager.create_session()

        # Update language and disclaimer acknowledgment
        await session_manager.update_session(
            session_id, {"language": "es", "disclaimer_acknowledged": True}
        )

        # Verify updates
        session = await session_manager.get_session(session_id)
        assert session.language == "es"
        assert session.disclaimer_acknowledged is True

        # Verify last_activity was updated
        assert session.last_activity > session.start_time

    @pytest.mark.asyncio
    async def test_update_session_user_context(self, session_manager):
        """Test updating user context within a session."""
        session_id = await session_manager.create_session()

        # Update user context
        await session_manager.update_session(
            session_id,
            {
                "user_context": {
                    "preferred_language": "es",
                    "legal_issue_type": LegalIssueType.TENANT_RIGHTS,
                    "urgency_level": UrgencyLevel.HIGH,
                    "has_minor_children": True,
                }
            },
        )

        # Verify user context updates
        session = await session_manager.get_session(session_id)
        assert session.user_context.preferred_language == "es"
        assert session.user_context.legal_issue_type == LegalIssueType.TENANT_RIGHTS
        assert session.user_context.urgency_level == UrgencyLevel.HIGH
        assert session.user_context.has_minor_children is True

    @pytest.mark.asyncio
    async def test_update_session_not_found(self, session_manager):
        """Test updating a non-existent session raises error."""
        fake_id = SessionId("non-existent-id")

        with pytest.raises(SessionNotFoundError):
            await session_manager.update_session(fake_id, {"language": "es"})

    @pytest.mark.asyncio
    async def test_end_session(self, session_manager):
        """Test ending a session removes it from storage."""
        session_id = await session_manager.create_session()

        # Verify session exists
        await session_manager.get_session(session_id)
        assert session_manager.get_active_session_count() == 1

        # End session
        await session_manager.end_session(session_id)

        # Verify session is removed
        assert session_manager.get_active_session_count() == 0

        with pytest.raises(SessionNotFoundError):
            await session_manager.get_session(session_id)

    @pytest.mark.asyncio
    async def test_end_session_not_found(self, session_manager):
        """Test ending a non-existent session raises error."""
        fake_id = SessionId("non-existent-id")

        with pytest.raises(SessionNotFoundError):
            await session_manager.end_session(fake_id)

    @pytest.mark.asyncio
    async def test_session_expiration(self, session_manager):
        """Test that expired sessions are automatically removed."""
        # Create session manager with very short timeout
        short_timeout_manager = InMemorySessionManager(
            session_timeout=0
        )  # 0 minutes = immediate expiration

        session_id = await short_timeout_manager.create_session()

        # Wait a moment to ensure expiration
        await asyncio.sleep(0.1)

        # Trying to get expired session should raise error
        with pytest.raises(SessionNotFoundError):
            await short_timeout_manager.get_session(session_id)

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, session_manager):
        """Test manual cleanup of expired sessions."""
        # Create sessions with mocked timestamps
        session_id1 = await session_manager.create_session()
        session_id2 = await session_manager.create_session()

        # Mock one session as expired
        session1 = await session_manager.get_session(session_id1)
        expired_time = datetime.now() - timedelta(hours=2)

        # Directly modify the session to simulate expiration
        session_manager._sessions[session_id1] = session1.model_copy(
            update={"last_activity": expired_time}
        )

        assert session_manager.get_active_session_count() == 2

        # Run cleanup
        await session_manager.cleanup_expired_sessions()

        # Verify expired session was removed
        assert session_manager.get_active_session_count() == 1

        # Verify non-expired session still exists
        await session_manager.get_session(session_id2)

        # Verify expired session is gone
        with pytest.raises(SessionNotFoundError):
            await session_manager.get_session(session_id1)

    @pytest.mark.asyncio
    async def test_automatic_cleanup_trigger(self, session_manager):
        """Test that cleanup is automatically triggered during operations."""
        # Create session manager with very short cleanup interval
        quick_cleanup_manager = InMemorySessionManager(
            session_timeout=60, cleanup_interval=0  # Immediate cleanup
        )

        # Create a session
        session_id = await quick_cleanup_manager.create_session()

        # Mock the session as expired
        session = await quick_cleanup_manager.get_session(session_id)
        expired_time = datetime.now() - timedelta(hours=2)
        quick_cleanup_manager._sessions[session_id] = session.model_copy(
            update={"last_activity": expired_time}
        )

        # Mock last cleanup time to trigger cleanup
        quick_cleanup_manager._last_cleanup = datetime.now() - timedelta(hours=1)

        # Creating a new session should trigger cleanup
        new_session_id = await quick_cleanup_manager.create_session()

        # Expired session should be gone
        assert quick_cleanup_manager.get_active_session_count() == 1

        # Only new session should exist
        await quick_cleanup_manager.get_session(new_session_id)
        with pytest.raises(SessionNotFoundError):
            await quick_cleanup_manager.get_session(session_id)

    @pytest.mark.asyncio
    async def test_conversation_history_tracking(self, session_manager):
        """Test that conversation history can be tracked in sessions."""
        from ai_legal_aid.types import ConversationTurn, SystemResponse, Action

        session_id = await session_manager.create_session()

        # Create a conversation turn
        turn = ConversationTurn(
            user_input="I have a landlord problem",
            system_response=SystemResponse(
                text="I can help with tenant rights issues.",
                requires_disclaimer=True,
                suggested_actions=[
                    Action(type="clarify", description="Tell me more about the issue")
                ],
            ),
            confidence=0.95,
            disclaimer_shown=True,
        )

        # Update session with conversation history
        await session_manager.update_session(
            session_id, {"conversation_history": [turn]}
        )

        # Verify conversation history is stored
        session = await session_manager.get_session(session_id)
        assert len(session.conversation_history) == 1
        assert session.conversation_history[0].user_input == "I have a landlord problem"
        assert session.conversation_history[0].confidence == 0.95
        assert session.conversation_history[0].disclaimer_shown is True

    @pytest.mark.asyncio
    async def test_utility_methods(self, session_manager):
        """Test utility methods for monitoring and testing."""
        # Initially no sessions
        assert session_manager.get_active_session_count() == 0
        assert session_manager.get_session_ids() == []

        # Create some sessions
        session_id1 = await session_manager.create_session()
        session_id2 = await session_manager.create_session()

        # Test utility methods
        assert session_manager.get_active_session_count() == 2
        session_ids = session_manager.get_session_ids()
        assert len(session_ids) == 2
        assert session_id1 in session_ids
        assert session_id2 in session_ids

        # Test clear all sessions
        await session_manager.clear_all_sessions()
        assert session_manager.get_active_session_count() == 0
        assert session_manager.get_session_ids() == []

    @pytest.mark.asyncio
    async def test_concurrent_session_operations(self, session_manager):
        """Test concurrent session operations for thread safety."""
        # Create multiple sessions concurrently
        tasks = [session_manager.create_session() for _ in range(10)]
        session_ids = await asyncio.gather(*tasks)

        # Verify all sessions were created
        assert len(set(session_ids)) == 10  # All unique
        assert session_manager.get_active_session_count() == 10

        # Update sessions concurrently
        update_tasks = [
            session_manager.update_session(session_id, {"language": f"lang_{i}"})
            for i, session_id in enumerate(session_ids)
        ]
        await asyncio.gather(*update_tasks)

        # Verify all updates succeeded
        for i, session_id in enumerate(session_ids):
            session = await session_manager.get_session(session_id)
            assert session.language == f"lang_{i}"

    @pytest.mark.asyncio
    async def test_session_data_validation(self, session_manager):
        """Test that session data is properly validated."""
        session_id = await session_manager.create_session()

        # Test invalid user context update
        with pytest.raises(Exception):  # Should raise validation error
            await session_manager.update_session(
                session_id,
                {
                    "user_context": {
                        "legal_issue_type": "invalid_issue_type"  # Invalid enum value
                    }
                },
            )

        # Test valid user context update
        await session_manager.update_session(
            session_id,
            {"user_context": {"legal_issue_type": LegalIssueType.WAGE_THEFT}},
        )

        session = await session_manager.get_session(session_id)
        assert session.user_context.legal_issue_type == LegalIssueType.WAGE_THEFT

    @pytest.mark.asyncio
    async def test_session_timeout_configuration(self):
        """Test different session timeout configurations."""
        # Test with custom timeout
        custom_manager = InMemorySessionManager(session_timeout=30, cleanup_interval=5)

        session_id = await custom_manager.create_session()
        session = await custom_manager.get_session(session_id)

        # Verify session exists
        assert session.id == session_id

        # Mock session as expired based on custom timeout
        expired_time = datetime.now() - timedelta(
            minutes=31
        )  # Beyond 30 minute timeout
        custom_manager._sessions[session_id] = session.model_copy(
            update={"last_activity": expired_time}
        )

        # Session should now be expired
        with pytest.raises(SessionNotFoundError):
            await custom_manager.get_session(session_id)
 