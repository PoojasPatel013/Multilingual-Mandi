"""
Integration tests for encryption and privacy features.

This module tests the complete integration of encryption, PII anonymization,
and secure cleanup functionality in the AI Legal Aid system.
"""

import asyncio
import pytest
import tempfile
import os
from datetime import datetime

from ai_legal_aid.encrypted_session_manager import EncryptedSessionManager
from ai_legal_aid.types import ConversationTurn, SystemResponse, Action, LegalIssueType


class TestEncryptionPrivacyIntegration:
    """Integration tests for encryption and privacy features."""

    @pytest.mark.asyncio
    async def test_complete_privacy_workflow(self):
        """Test complete privacy workflow from session creation to secure cleanup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create encrypted session manager
            manager = EncryptedSessionManager(
                session_timeout=60,
                encryption_password="integration_test_password",
                temp_dir=temp_dir,
            )

            # Step 1: Create session
            session_id = await manager.create_session()
            assert session_id is not None

            # Step 2: Update session with PII-containing conversation
            sensitive_turn = ConversationTurn(
                user_input="Hi, I'm Sarah Johnson at sarah.j@email.com. I live at 123 Oak Street, 90210. My phone is 555-987-6543. I have a tenant rights issue.",
                system_response=SystemResponse(
                    text="Hello Sarah, I understand you're having tenant issues at 123 Oak Street. I'll help you with your rights.",
                    requires_disclaimer=True,
                    suggested_actions=[
                        Action(type="gather_info", description="Tell me more about the issue")
                    ],
                ),
                confidence=0.92,
                disclaimer_shown=True,
            )

            await manager.update_session(
                session_id,
                {
                    "conversation_history": [sensitive_turn],
                    "user_context": {
                        "legal_issue_type": LegalIssueType.TENANT_RIGHTS,
                        "location": {
                            "state": "California",
                            "county": "Los Angeles County",
                            "zip_code": "90210",
                            "coordinates": {"latitude": 34.0522, "longitude": -118.2437},
                        },
                    },
                },
            )

            # Step 3: Store sensitive audio data
            audio_data = b"This is sensitive audio recording containing PII"
            audio_file_path = await manager.store_audio_data(
                session_id, audio_data, "sensitive_recording"
            )
            assert os.path.exists(audio_file_path)

            # Step 4: Verify data is encrypted and anonymized
            session = await manager.get_session(session_id)

            # Check conversation anonymization
            stored_turn = session.conversation_history[0]
            user_input = stored_turn.user_input
            system_text = stored_turn.system_response.text

            # Original PII should be anonymized
            assert "Sarah Johnson" not in user_input
            assert "sarah.j@email.com" not in user_input
            assert "123 Oak Street" not in user_input
            assert "555-987-6543" not in user_input

            # But legal context should be preserved
            assert "issue" in user_input  # This should remain

            # System response should also be anonymized
            assert "Sarah" not in system_text
            assert "123 Oak Street" not in system_text

            # Check user context anonymization
            location = session.user_context.location
            assert location.state == "California"  # Preserved for legal jurisdiction
            assert "Los Angeles County" not in str(location.county)  # Anonymized
            assert location.zip_code == "902XX"  # Partially anonymized
            assert location.coordinates is None  # Removed

            # Step 5: Verify encrypted storage
            encrypted_data = manager._encrypted_sessions[session_id]
            assert "Sarah Johnson" not in encrypted_data
            assert "sarah.j@email.com" not in encrypted_data
            assert "123 Oak Street" not in encrypted_data
            assert "555-987-6543" not in encrypted_data

            # Step 6: Verify audio data encryption
            with open(audio_file_path, "r") as f:
                encrypted_audio_content = f.read()
            assert "sensitive audio recording" not in encrypted_audio_content

            # But should be retrievable
            retrieved_audio = await manager.retrieve_audio_data(session_id, audio_file_path)
            assert retrieved_audio == audio_data

            # Step 7: Generate privacy report
            privacy_report = await manager.get_privacy_report(session_id)
            assert privacy_report["data_encrypted"] is True
            assert privacy_report["pii_anonymized"] is True
            assert privacy_report["anonymized_items_count"] > 0
            assert privacy_report["temp_files_count"] == 1

            # Step 8: Secure session cleanup
            await manager.end_session(session_id)

            # Verify complete cleanup
            assert session_id not in manager._encrypted_sessions
            assert session_id not in manager._temp_files
            assert not os.path.exists(audio_file_path)

    @pytest.mark.asyncio
    async def test_privacy_compliance_across_sessions(self):
        """Test privacy compliance across multiple concurrent sessions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = EncryptedSessionManager(
                encryption_password="multi_session_test",
                temp_dir=temp_dir,
            )

            # Create multiple sessions with different PII
            sessions_data = [
                {
                    "user_input": "I'm John Smith, email john@test.com, phone 555-111-1111",
                    "expected_anonymized": ["John Smith", "john@test.com", "555-111-1111"],
                },
                {
                    "user_input": "My name is Jane Doe, contact jane@example.org, call 555-222-2222",
                    "expected_anonymized": ["Jane Doe", "jane@example.org", "555-222-2222"],
                },
                {
                    "user_input": "I live at 456 Pine Avenue, ZIP 12345, SSN 123-45-6789",
                    "expected_anonymized": ["456 Pine Avenue", "12345", "123-45-6789"],
                },
            ]

            session_ids = []
            for i, data in enumerate(sessions_data):
                session_id = await manager.create_session()
                session_ids.append(session_id)

                turn = ConversationTurn(
                    user_input=data["user_input"],
                    system_response=SystemResponse(
                        text=f"I understand your situation {i+1}",
                        requires_disclaimer=True,
                        suggested_actions=[],
                    ),
                    confidence=0.9,
                )

                await manager.update_session(session_id, {"conversation_history": [turn]})

                # Store audio for each session
                audio_data = f"Audio recording {i+1} with PII".encode()
                await manager.store_audio_data(session_id, audio_data, f"recording_{i+1}")

            # Verify each session has proper anonymization
            for i, session_id in enumerate(session_ids):
                session = await manager.get_session(session_id)
                stored_input = session.conversation_history[0].user_input

                # Check that all expected PII is anonymized
                for pii_item in sessions_data[i]["expected_anonymized"]:
                    assert pii_item not in stored_input

                # Check that anonymization placeholders are present
                assert any(
                    placeholder in stored_input
                    for placeholder in ["[FULL_NAME_", "[EMAIL_", "[PHONE_", "[ADDRESS_", "[ZIP_CODE_", "[SSN_"]
                )

            # Generate privacy reports for all sessions
            for session_id in session_ids:
                report = await manager.get_privacy_report(session_id)
                assert report["data_encrypted"] is True
                assert report["pii_anonymized"] is True

            # Clean up all sessions
            await manager.clear_all_sessions()

            # Verify complete cleanup
            assert len(manager._encrypted_sessions) == 0
            assert len(manager._temp_files) == 0

    @pytest.mark.asyncio
    async def test_encryption_key_consistency(self):
        """Test that encryption keys work consistently across manager instances."""
        password = "consistency_test_password"

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create first manager and session
            manager1 = EncryptedSessionManager(
                encryption_password=password,
                temp_dir=temp_dir,
            )

            session_id = await manager1.create_session()
            await manager1.update_session(
                session_id,
                {
                    "language": "es",
                    "disclaimer_acknowledged": True,
                    "user_context": {"preferred_language": "es"},
                },
            )

            # Get encrypted data
            encrypted_data = manager1._encrypted_sessions[session_id]

            # Create second manager with same password
            manager2 = EncryptedSessionManager(
                encryption_password=password,
                temp_dir=temp_dir,
            )

            # Transfer encrypted data
            manager2._encrypted_sessions[session_id] = encrypted_data

            # Second manager should be able to decrypt
            session = await manager2.get_session(session_id)
            assert session.language == "es"
            assert session.disclaimer_acknowledged is True
            assert session.user_context.preferred_language == "es"

    @pytest.mark.asyncio
    async def test_secure_cleanup_on_expiration(self):
        """Test secure cleanup when sessions expire."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create manager with very short timeout
            manager = EncryptedSessionManager(
                session_timeout=1,  # 1 minute timeout
                encryption_password="expiration_test",
                temp_dir=temp_dir,
            )

            # Create session with sensitive data
            session_id = await manager.create_session()
            
            # Add PII data
            turn = ConversationTurn(
                user_input="My SSN is 987-65-4321 and I live at 789 Elm Street",
                system_response=SystemResponse(
                    text="I understand your concern",
                    requires_disclaimer=True,
                    suggested_actions=[],
                ),
                confidence=0.85,
            )

            await manager.update_session(session_id, {"conversation_history": [turn]})

            # Store audio file
            audio_data = b"Expired session audio with PII"
            audio_file_path = await manager.store_audio_data(session_id, audio_data)

            # Verify files exist
            assert os.path.exists(audio_file_path)
            assert session_id in manager._encrypted_sessions

            # Manually expire the session by modifying its timestamp
            encrypted_data = manager._encrypted_sessions[session_id]
            session_data = manager.secure_data_manager.retrieve_session_data(encrypted_data)
            
            # Set last activity to 2 minutes ago (beyond 1 minute timeout)
            from datetime import datetime, timedelta
            session_data["last_activity"] = (datetime.now() - timedelta(minutes=2)).isoformat()
            
            # Re-encrypt and store
            updated_encrypted_data = manager.secure_data_manager.secure_session_data(session_data)
            manager._encrypted_sessions[session_id] = updated_encrypted_data

            # Trigger cleanup
            await manager.cleanup_expired_sessions()

            # Verify secure cleanup occurred
            assert session_id not in manager._encrypted_sessions
            assert session_id not in manager._temp_files
            assert not os.path.exists(audio_file_path)