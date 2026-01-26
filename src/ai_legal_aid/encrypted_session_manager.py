"""
Encrypted Session Manager implementation for the AI Legal Aid System.

This module provides an encrypted implementation of the SessionManager protocol
that builds upon the InMemorySessionManager to add data encryption, PII
anonymization, and secure cleanup functionality for privacy compliance.
"""

import asyncio
import tempfile
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from pathlib import Path

from ai_legal_aid.session_manager import InMemorySessionManager, SessionNotFoundError
from ai_legal_aid.encryption import SecureDataManager
from ai_legal_aid.types import SessionId, Session


class EncryptedSessionManager(InMemorySessionManager):
    """
    Encrypted implementation of the SessionManager protocol.

    This implementation extends InMemorySessionManager to add:
    - Data encryption for all session data at rest
    - PII anonymization for conversation logs
    - Secure cleanup of temporary files and audio data
    - Enhanced privacy compliance features

    All session data is encrypted before storage and decrypted on retrieval.
    Conversation history is anonymized to remove PII while preserving
    legal context for guidance purposes.
    """

    def __init__(
        self,
        session_timeout: int = 60,
        cleanup_interval: int = 10,
        encryption_password: Optional[str] = None,
        temp_dir: Optional[str] = None,
    ):
        """
        Initialize the encrypted session manager.

        Args:
            session_timeout: Session timeout in minutes
            cleanup_interval: Cleanup interval in minutes
            encryption_password: Password for encryption (None for random key)
            temp_dir: Directory for temporary files (None for system temp)
        """
        super().__init__(session_timeout, cleanup_interval)
        
        # Initialize secure data manager
        self.secure_data_manager = SecureDataManager(encryption_password)
        
        # Set up temporary directory for audio files
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir())
        self.temp_dir = self.temp_dir / "ai_legal_aid_temp"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Track temporary files for cleanup
        self._temp_files: Dict[SessionId, Set[str]] = {}
        
        # Override storage to use encrypted data
        self._encrypted_sessions: Dict[SessionId, str] = {}

    async def create_session(self) -> SessionId:
        """
        Create a new user session with encryption.

        Returns:
            Unique session identifier
        """
        session_id = await super().create_session()
        
        # Move session data to encrypted storage
        session = self._sessions[session_id]
        encrypted_data = self.secure_data_manager.secure_session_data(
            session.model_dump()
        )
        self._encrypted_sessions[session_id] = encrypted_data
        
        # Remove from unencrypted storage
        del self._sessions[session_id]
        
        # Initialize temp file tracking
        self._temp_files[session_id] = set()
        
        return session_id

    async def get_session(self, session_id: SessionId) -> Session:
        """
        Retrieve session information with decryption.

        Args:
            session_id: Unique session identifier

        Returns:
            Decrypted session information

        Raises:
            SessionNotFoundError: If session doesn't exist or has expired
        """
        if session_id not in self._encrypted_sessions:
            raise SessionNotFoundError(session_id)

        # Decrypt session data
        encrypted_data = self._encrypted_sessions[session_id]
        session_data = self.secure_data_manager.retrieve_session_data(encrypted_data)
        session = Session(**session_data)

        # Check if session has expired
        if self._is_session_expired(session):
            await self._remove_session(session_id)
            raise SessionNotFoundError(session_id)

        return session

    async def update_session(self, session_id: SessionId, updates: dict) -> None:
        """
        Update session information with encryption.

        Args:
            session_id: Unique session identifier
            updates: Dictionary of fields to update

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        # Get current session data
        session = await self.get_session(session_id)

        # Update last activity time
        updates["last_activity"] = datetime.now()

        # Create updated session with new data
        session_data = session.model_dump()
        session_data.update(updates)

        # Handle nested updates for user_context
        if "user_context" in updates and isinstance(updates["user_context"], dict):
            from ai_legal_aid.types import UserContext
            current_context = session_data.get("user_context", {})
            if isinstance(current_context, UserContext):
                current_context = current_context.model_dump()
            current_context.update(updates["user_context"])
            session_data["user_context"] = UserContext(**current_context)

        # Validate updated session
        updated_session = Session(**session_data)

        # Encrypt and store updated session
        encrypted_data = self.secure_data_manager.secure_session_data(
            updated_session.model_dump()
        )
        self._encrypted_sessions[session_id] = encrypted_data

    async def end_session(self, session_id: SessionId) -> None:
        """
        End a session and perform secure cleanup.

        Args:
            session_id: Unique session identifier

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        # Verify session exists
        await self.get_session(session_id)

        # Perform secure cleanup
        await self._secure_cleanup_session(session_id)

        # Remove session from storage
        await self._remove_session(session_id)

    async def cleanup_expired_sessions(self) -> None:
        """
        Clean up expired sessions with secure data deletion.

        This method removes all sessions that have exceeded the timeout
        period and securely deletes associated temporary files.
        """
        async with self._cleanup_lock:
            expired_sessions = []

            for session_id in list(self._encrypted_sessions.keys()):
                try:
                    # Decrypt to check expiration
                    encrypted_data = self._encrypted_sessions[session_id]
                    session_data = self.secure_data_manager.retrieve_session_data(
                        encrypted_data
                    )
                    session = Session(**session_data)

                    if self._is_session_expired(session):
                        expired_sessions.append(session_id)
                except Exception:
                    # If we can't decrypt, consider it expired
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                await self._secure_cleanup_session(session_id)
                await self._remove_session(session_id)

            self._last_cleanup = datetime.now()

    async def store_audio_data(
        self, session_id: SessionId, audio_data: bytes, file_prefix: str = "audio"
    ) -> str:
        """
        Store audio data temporarily with secure handling.

        Args:
            session_id: Session identifier
            audio_data: Audio data to store
            file_prefix: Prefix for temporary file name

        Returns:
            Path to temporary audio file

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        # Verify session exists
        await self.get_session(session_id)

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            prefix=f"{file_prefix}_",
            suffix=".tmp",
            dir=self.temp_dir,
            delete=False,
        )

        try:
            # Write encrypted audio data
            encrypted_audio = self.secure_data_manager.encryption_manager.encrypt(
                audio_data.hex()
            )
            temp_file.write(encrypted_audio.encode())
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_file.close()

            # Track temporary file for cleanup
            if session_id not in self._temp_files:
                self._temp_files[session_id] = set()
            self._temp_files[session_id].add(temp_file.name)

            return temp_file.name

        except Exception:
            # Clean up on error
            temp_file.close()
            if os.path.exists(temp_file.name):
                self.secure_data_manager.secure_delete_file(temp_file.name)
            raise

    async def retrieve_audio_data(self, session_id: SessionId, file_path: str) -> bytes:
        """
        Retrieve and decrypt audio data from temporary storage.

        Args:
            session_id: Session identifier
            file_path: Path to temporary audio file

        Returns:
            Decrypted audio data

        Raises:
            SessionNotFoundError: If session doesn't exist
            FileNotFoundError: If audio file doesn't exist
        """
        # Verify session exists
        await self.get_session(session_id)

        # Verify file is tracked for this session
        if (
            session_id not in self._temp_files
            or file_path not in self._temp_files[session_id]
        ):
            raise FileNotFoundError(f"Audio file not found for session: {file_path}")

        # Read and decrypt audio data
        with open(file_path, "r") as f:
            encrypted_audio = f.read()

        decrypted_hex = self.secure_data_manager.encryption_manager.decrypt(
            encrypted_audio
        )
        return bytes.fromhex(decrypted_hex)

    async def delete_audio_data(self, session_id: SessionId, file_path: str) -> bool:
        """
        Securely delete audio data file.

        Args:
            session_id: Session identifier
            file_path: Path to temporary audio file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify session exists
            await self.get_session(session_id)

            # Remove from tracking
            if (
                session_id in self._temp_files
                and file_path in self._temp_files[session_id]
            ):
                self._temp_files[session_id].remove(file_path)

            # Securely delete file
            return self.secure_data_manager.secure_delete_file(file_path)

        except Exception:
            return False

    async def _secure_cleanup_session(self, session_id: SessionId) -> None:
        """
        Perform secure cleanup for a session.

        Args:
            session_id: Session to clean up
        """
        # Clean up temporary files
        if session_id in self._temp_files:
            for file_path in self._temp_files[session_id].copy():
                self.secure_data_manager.secure_delete_file(file_path)
            del self._temp_files[session_id]

    async def _remove_session(self, session_id: SessionId) -> None:
        """
        Remove a session from encrypted storage.

        Args:
            session_id: Session to remove
        """
        if session_id in self._encrypted_sessions:
            del self._encrypted_sessions[session_id]

        # Also clean up any remaining temp files
        if session_id in self._temp_files:
            del self._temp_files[session_id]

    # Override utility methods to work with encrypted storage

    def get_active_session_count(self) -> int:
        """
        Get the number of currently active sessions.

        Returns:
            Number of active sessions
        """
        return len(self._encrypted_sessions)

    def get_session_ids(self) -> list[SessionId]:
        """
        Get all active session IDs.

        Returns:
            List of active session IDs
        """
        return list(self._encrypted_sessions.keys())

    async def clear_all_sessions(self) -> None:
        """
        Clear all sessions with secure cleanup.
        """
        # Perform secure cleanup for all sessions
        for session_id in list(self._encrypted_sessions.keys()):
            await self._secure_cleanup_session(session_id)

        # Clear all storage
        self._encrypted_sessions.clear()
        self._temp_files.clear()

    async def get_privacy_report(self, session_id: SessionId) -> Dict[str, any]:
        """
        Generate a privacy compliance report for a session.

        Args:
            session_id: Session identifier

        Returns:
            Privacy compliance report

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        session = await self.get_session(session_id)

        # Count anonymized items in conversation history
        anonymized_count = 0
        total_turns = len(session.conversation_history)

        for turn in session.conversation_history:
            turn_dict = turn.model_dump() if hasattr(turn, 'model_dump') else turn
            user_input = turn_dict.get('user_input', '')
            if '[' in user_input and ']' in user_input:
                # Count anonymization placeholders
                import re
                anonymized_count += len(re.findall(r'\[[A-Z_0-9]+\]', user_input))

        return {
            "session_id": session_id,
            "data_encrypted": True,
            "pii_anonymized": anonymized_count > 0,
            "anonymized_items_count": anonymized_count,
            "total_conversation_turns": total_turns,
            "temp_files_count": len(self._temp_files.get(session_id, set())),
            "session_duration_minutes": (
                datetime.now() - session.start_time
            ).total_seconds() / 60,
        }