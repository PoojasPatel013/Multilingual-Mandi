"""
Unit tests for the EncryptedSessionManager implementation.

This module tests all aspects of encrypted session management including
data encryption, PII anonymization, secure cleanup, and privacy compliance.
"""

import asyncio
import pytest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from ai_legal_aid.encrypted_session_manager import EncryptedSessionManager
from ai_legal_aid.session_manager import SessionNotFoundError
from ai_legal_aid.types import SessionId, UserContext, LegalIssueType, UrgencyLevel


class TestEncryptedSessionManager:
    """Test suite for EncryptedSessionManager."""

    @pytest.fixture
    def encrypted_session_manager(self):
        """Create an encrypted session manager instance for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = EncryptedSessionManager(
                session_timeout=60,
                cleanup_interval=10,
                encryption_password="test_password_123",
                temp_dir=temp_dir,
            )
            yield manager

    @pytest.mark.asyncio
    async def test_create_encrypted_session(self, encrypted_session_manager):
        """Test creating a new encrypted session."""
        session_id = await encrypted_session_manager.create_session()

        # Verify session ID is valid
        assert isinstance(session_id, str)
        assert len(session_id) > 0

        # Verify session is stored encrypted
        assert session_id in encrypted_session_manager._encrypted_sessions
        assert session_id not in encrypted_session_manager._sessions

        # Verify session can be retrieved and decrypted
        session = await encrypted_session_manager.get_session(session_id)
        assert session.id == session_id
        assert session.language == "en"
        assert session.disclaimer_acknowledged is False

    @pytest.mark.asyncio
    async def test_session_data_encryption(self, encrypted_session_manager):
        """Test that session data is properly encrypted."""
        session_id = await encrypted_session_manager.create_session()

        # Update session with sensitive data
        await encrypted_session_manager.update_session(
            session_id,
            {
                "user_context": {
                    "preferred_language": "es",
                    "legal_issue_type": LegalIssueType.TENANT_RIGHTS,
                }
            },
        )

        # Check that encrypted data doesn't contain plaintext
        encrypted_data = encrypted_session_manager._encrypted_sessions[session_id]
        assert "es" not in encrypted_data
        assert "tenant_rights" not in encrypted_data

        # Verify data can be decrypted correctly
        session = await encrypted_session_manager.get_session(session_id)
        assert session.user_context.preferred_language == "es"
        assert session.user_context.legal_issue_type == LegalIssueType.TENANT_RIGHTS

    @pytest.mark.asyncio
    async def test_pii_anonymization_in_conversation(self, encrypted_session_manager):
        """Test PII anonymization in conversation history."""
        from ai_legal_aid.types import ConversationTurn, SystemResponse, Action

        session_id = await encrypted_session_manager.create_session()

        # Create conversation turn with PII
        turn = ConversationTurn(
            user_input="My name is John Smith and my phone is 555-123-4567",
            system_response=SystemResponse(
                text="Hello John, I'll help with your tenant issue",
                requires_disclaimer=True,
                suggested_actions=[
                    Action(type="clarify", description="Tell me more")
                ],
            ),
            confidence=0.95,
            disclaimer_shown=True,
        )

        # Update session with conversation history
        await encrypted_session_manager.update_session(
            session_id, {"conversation_history": [turn]}
        )

        # Retrieve session and check anonymization
        session = await encrypted_session_manager.get_session(session_id)
        stored_turn = session.conversation_history[0]

        # PII should be anonymized
        assert "John Smith" not in stored_turn.user_input
        assert "555-123-4567" not in stored_turn.user_input
        assert "[FULL_NAME_" in stored_turn.user_input
        assert "[PHONE_" in stored_turn.user_input

    @pytest.mark.asyncio
    async def test_audio_data_storage_and_retrieval(self, encrypted_session_manager):
        """Test secure audio data storage and retrieval."""
        session_id = await encrypted_session_manager.create_session()
        audio_data = b"fake_audio_data_for_testing"

        # Store audio data
        file_path = await encrypted_session_manager.store_audio_data(
            session_id, audio_data, "test_audio"
        )

        # Verify file was created and tracked
        assert os.path.exists(file_path)
        assert file_path in encrypted_session_manager._temp_files[session_id]

        # Retrieve audio data
        retrieved_data = await encrypted_session_manager.retrieve_audio_data(
            session_id, file_path
        )
        assert retrieved_data == audio_data

        # Clean up
        success = await encrypted_session_manager.delete_audio_data(
            session_id, file_path
        )
        assert success is True
        assert not os.path.exists(file_path)

    @pytest.mark.asyncio
    async def test_secure_session_cleanup(self, encrypted_session_manager):
        """Test secure cleanup when ending sessions."""
        session_id = await encrypted_session_manager.create_session()
        audio_data = b"test_audio_for_cleanup"

        # Store some audio data
        file_path = await encrypted_session_manager.store_audio_data(
            session_id, audio_data
        )
        assert os.path.exists(file_path)

        # End session
        await encrypted_session_manager.end_session(session_id)

        # Verify session is removed
        with pytest.raises(SessionNotFoundError):
            await encrypted_session_manager.get_session(session_id)

        # Verify temp files are securely deleted
        assert not os.path.exists(file_path)
        assert session_id not in encrypted_session_manager._temp_files

    @pytest.mark.asyncio
    async def test_privacy_report_generation(self, encrypted_session_manager):
        """Test privacy compliance report generation."""
        from ai_legal_aid.types import ConversationTurn, SystemResponse

        session_id = await encrypted_session_manager.create_session()

        # Add conversation with PII
        turn = ConversationTurn(
            user_input="My name is Jane Doe, email jane@example.com",
            system_response=SystemResponse(
                text="I understand your situation",
                requires_disclaimer=True,
                suggested_actions=[],
            ),
            confidence=0.9,
        )

        await encrypted_session_manager.update_session(
            session_id, {"conversation_history": [turn]}
        )

        # Generate privacy report
        report = await encrypted_session_manager.get_privacy_report(session_id)

        assert report["session_id"] == session_id
        assert report["data_encrypted"] is True
        assert report["pii_anonymized"] is True
        assert report["anonymized_items_count"] > 0
        assert report["total_conversation_turns"] == 1