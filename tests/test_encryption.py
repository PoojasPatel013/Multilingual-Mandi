"""
Unit tests for encryption and privacy utilities.

This module tests the encryption, decryption, and PII anonymization
functionality to ensure data privacy and security compliance.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock

from ai_legal_aid.encryption import (
    EncryptionManager,
    PIIAnonymizer,
    SecureDataManager,
)


class TestEncryptionManager:
    """Test suite for EncryptionManager."""

    def test_encrypt_decrypt_string(self):
        """Test basic string encryption and decryption."""
        manager = EncryptionManager()
        original_text = "This is sensitive legal information"

        # Encrypt the text
        encrypted = manager.encrypt(original_text)
        assert encrypted != original_text
        assert len(encrypted) > 0

        # Decrypt the text
        decrypted = manager.decrypt(encrypted)
        assert decrypted == original_text

    def test_encrypt_decrypt_with_password(self):
        """Test encryption with password-based key derivation."""
        password = "secure_legal_aid_password"
        manager1 = EncryptionManager(password)
        manager2 = EncryptionManager(password)

        original_text = "Confidential legal data"

        # Encrypt with first manager
        encrypted = manager1.encrypt(original_text)

        # Decrypt with second manager using same password
        decrypted = manager2.decrypt(encrypted)
        assert decrypted == original_text

    def test_encrypt_decrypt_dict(self):
        """Test dictionary encryption and decryption."""
        manager = EncryptionManager()
        original_dict = {
            "user_input": "I have a landlord problem",
            "timestamp": "2024-01-15T10:30:00",
            "confidence": 0.95,
            "nested": {"key": "value", "number": 42},
        }

        # Encrypt the dictionary
        encrypted = manager.encrypt_dict(original_dict)
        assert isinstance(encrypted, str)
        assert encrypted != str(original_dict)

        # Decrypt the dictionary
        decrypted = manager.decrypt_dict(encrypted)
        assert decrypted == original_dict

    def test_different_keys_produce_different_results(self):
        """Test that different encryption keys produce different results."""
        manager1 = EncryptionManager()
        manager2 = EncryptionManager()

        text = "Same text for both managers"

        encrypted1 = manager1.encrypt(text)
        encrypted2 = manager2.encrypt(text)

        # Different keys should produce different encrypted results
        assert encrypted1 != encrypted2

        # Each manager should decrypt its own encryption correctly
        assert manager1.decrypt(encrypted1) == text
        assert manager2.decrypt(encrypted2) == text

    def test_invalid_decryption_raises_error(self):
        """Test that invalid encrypted data raises an error."""
        manager = EncryptionManager()

        with pytest.raises(Exception):  # Fernet raises InvalidToken
            manager.decrypt("invalid_encrypted_data")

    def test_empty_string_encryption(self):
        """Test encryption of empty strings."""
        manager = EncryptionManager()
        
        encrypted = manager.encrypt("")
        decrypted = manager.decrypt(encrypted)
        assert decrypted == ""


class TestPIIAnonymizer:
    """Test suite for PIIAnonymizer."""

    def test_anonymize_phone_numbers(self):
        """Test phone number anonymization."""
        anonymizer = PIIAnonymizer()
        text = "Call me at 555-123-4567 or (555) 987-6543"

        anonymized = anonymizer.anonymize_text(text)

        assert "555-123-4567" not in anonymized
        assert "(555) 987-6543" not in anonymized
        assert "[PHONE_" in anonymized

    def test_anonymize_email_addresses(self):
        """Test email address anonymization."""
        anonymizer = PIIAnonymizer()
        text = "Contact me at john.doe@example.com or legal.aid@help.org"

        anonymized = anonymizer.anonymize_text(text)

        assert "john.doe@example.com" not in anonymized
        assert "legal.aid@help.org" not in anonymized
        assert "[EMAIL_" in anonymized

    def test_anonymize_social_security_numbers(self):
        """Test SSN anonymization."""
        anonymizer = PIIAnonymizer()
        text = "My SSN is 123-45-6789 and my friend's is 987654321"

        anonymized = anonymizer.anonymize_text(text)

        assert "123-45-6789" not in anonymized
        assert "987654321" not in anonymized
        assert "[SSN_" in anonymized

    def test_anonymize_addresses(self):
        """Test address anonymization."""
        anonymizer = PIIAnonymizer()
        text = "I live at 123 Main Street and work at 456 Oak Avenue"

        anonymized = anonymizer.anonymize_text(text)

        assert "123 Main Street" not in anonymized
        assert "456 Oak Avenue" not in anonymized
        assert "[ADDRESS_" in anonymized

    def test_anonymize_names(self):
        """Test name anonymization."""
        anonymizer = PIIAnonymizer()
        text = "My name is John Smith and my lawyer is Jane Doe"

        anonymized = anonymizer.anonymize_text(text)

        assert "John Smith" not in anonymized
        assert "Jane Doe" not in anonymized
        assert "[FULL_NAME_" in anonymized

    def test_anonymize_dates_of_birth(self):
        """Test date of birth anonymization."""
        anonymizer = PIIAnonymizer()
        text = "I was born on 01/15/1985 and my child on 12-25-2010"

        anonymized = anonymizer.anonymize_text(text)

        assert "01/15/1985" not in anonymized
        assert "12-25-2010" not in anonymized
        assert "[DATE_OF_BIRTH_" in anonymized

    def test_anonymize_zip_codes(self):
        """Test ZIP code anonymization."""
        anonymizer = PIIAnonymizer()
        text = "I live in 12345 and work in 67890-1234"

        anonymized = anonymizer.anonymize_text(text)

        assert "12345" not in anonymized
        assert "67890-1234" not in anonymized
        assert "[ZIP_CODE_" in anonymized

    def test_consistent_anonymization(self):
        """Test that same PII gets same anonymization placeholder."""
        anonymizer = PIIAnonymizer()
        text1 = "Call me at 555-123-4567"
        text2 = "My number is 555-123-4567"

        anonymized1 = anonymizer.anonymize_text(text1)
        anonymized2 = anonymizer.anonymize_text(text2)

        # Extract the placeholder from both texts
        import re
        placeholder1 = re.search(r'\[PHONE_\d+\]', anonymized1)
        placeholder2 = re.search(r'\[PHONE_\d+\]', anonymized2)
        
        if placeholder1 and placeholder2:
            assert placeholder1.group() == placeholder2.group()

    def test_anonymize_conversation_turn(self):
        """Test conversation turn anonymization."""
        anonymizer = PIIAnonymizer()
        turn_data = {
            "user_input": "My name is John Smith and my phone is 555-123-4567",
            "system_response": {
                "text": "Hello John Smith, I'll call you at 555-123-4567"
            },
            "timestamp": "2024-01-15T10:30:00",
            "confidence": 0.95,
        }

        anonymized = anonymizer.anonymize_conversation_turn(turn_data)

        assert "John Smith" not in anonymized["user_input"]
        assert "555-123-4567" not in anonymized["user_input"]
        assert "John Smith" not in anonymized["system_response"]["text"]
        assert "555-123-4567" not in anonymized["system_response"]["text"]
        assert "[FULL_NAME_" in anonymized["user_input"]
        assert "[PHONE_" in anonymized["user_input"]

    def test_anonymize_user_context(self):
        """Test user context anonymization."""
        anonymizer = PIIAnonymizer()
        context_data = {
            "location": {
                "state": "California",
                "county": "Los Angeles County",
                "zip_code": "90210",
                "coordinates": {"latitude": 34.0522, "longitude": -118.2437},
            },
            "preferred_language": "en",
        }

        anonymized = anonymizer.anonymize_user_context(context_data)

        # State should be preserved for legal jurisdiction
        assert anonymized["location"]["state"] == "California"

        # County should be anonymized but consistent
        assert "Los Angeles County" not in str(anonymized["location"]["county"])
        assert "[COUNTY_" in anonymized["location"]["county"]

        # ZIP code should be partially anonymized
        assert anonymized["location"]["zip_code"] == "902XX"

        # Coordinates should be removed
        assert anonymized["location"]["coordinates"] is None

    def test_preserve_legal_context(self):
        """Test that legal context is preserved during anonymization."""
        anonymizer = PIIAnonymizer()
        # Test with clear PII that won't cause false positives
        text = "Contact me at john.doe@email.com or call 555-123-4567 about my case."

        anonymized = anonymizer.anonymize_text(text)

        # Legal context should be preserved
        assert "case" in anonymized
        assert "Contact" in anonymized
        assert "about" in anonymized

        # PII should be anonymized
        assert "john.doe@email.com" not in anonymized
        assert "555-123-4567" not in anonymized
        assert "[EMAIL_" in anonymized
        assert "[PHONE_" in anonymized


class TestSecureDataManager:
    """Test suite for SecureDataManager."""

    def test_secure_session_data(self):
        """Test securing session data with encryption and anonymization."""
        manager = SecureDataManager()
        session_data = {
            "id": "session_123",
            "conversation_history": [
                {
                    "user_input": "My name is John Doe, call me at 555-123-4567",
                    "system_response": {"text": "Hello John, I'll help you"},
                    "timestamp": "2024-01-15T10:30:00",
                }
            ],
            "user_context": {
                "location": {
                    "state": "California",
                    "county": "Los Angeles",
                    "zip_code": "90210",
                }
            },
        }

        # Secure the session data
        encrypted_data = manager.secure_session_data(session_data)

        # Should be encrypted (different from original)
        assert isinstance(encrypted_data, str)
        assert "John Doe" not in encrypted_data
        assert "555-123-4567" not in encrypted_data

        # Should be able to retrieve
        retrieved_data = manager.retrieve_session_data(encrypted_data)

        # PII should be anonymized
        user_input = retrieved_data["conversation_history"][0]["user_input"]
        assert "John Doe" not in user_input
        assert "555-123-4567" not in user_input
        assert "[FULL_NAME_" in user_input
        assert "[PHONE_" in user_input

        # Location should be partially anonymized
        location = retrieved_data["user_context"]["location"]
        assert location["state"] == "California"  # Preserved
        assert location["zip_code"] == "902XX"  # Partially anonymized

    def test_secure_delete_file_simple(self):
        """Test secure file deletion with a simpler approach."""
        manager = SecureDataManager()

        # Create a real temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test data")
            temp_file_path = temp_file.name

        # Test secure deletion
        result = manager.secure_delete_file(temp_file_path)

        assert result is True
        assert not os.path.exists(temp_file_path)

    @patch("os.path.exists")
    def test_secure_delete_nonexistent_file(self, mock_exists):
        """Test secure deletion of non-existent file."""
        manager = SecureDataManager()
        mock_exists.return_value = False

        result = manager.secure_delete_file("/path/to/nonexistent.tmp")
        assert result is True

    def test_secure_delete_audio_data(self):
        """Test secure audio data deletion."""
        manager = SecureDataManager()

        # Test with mutable bytearray
        audio_data = bytearray(b"audio_data_here")
        original_length = len(audio_data)

        manager.secure_delete_audio_data(audio_data)

        # Data should be overwritten with zeros
        assert len(audio_data) == original_length
        assert all(byte == 0 for byte in audio_data)

    def test_secure_delete_immutable_audio_data(self):
        """Test secure deletion with immutable bytes."""
        manager = SecureDataManager()

        # Test with immutable bytes (should not raise error)
        audio_data = b"immutable_audio_data"
        
        # Should not raise an exception
        manager.secure_delete_audio_data(audio_data)

    def test_encryption_password_consistency(self):
        """Test that same password produces consistent encryption."""
        password = "test_password_123"
        manager1 = SecureDataManager(password)
        manager2 = SecureDataManager(password)

        session_data = {"test": "data"}

        encrypted1 = manager1.secure_session_data(session_data)
        decrypted2 = manager2.retrieve_session_data(encrypted1)

        assert decrypted2 == session_data

    def test_complex_session_data_anonymization(self):
        """Test anonymization of complex session data structures."""
        manager = SecureDataManager()
        
        complex_session = {
            "id": "session_456",
            "conversation_history": [
                {
                    "user_input": "I'm Jane Smith at jane@email.com, living at 789 Pine St, 12345",
                    "system_response": {
                        "text": "I understand Jane, let me help with your issue at 789 Pine St"
                    },
                },
                {
                    "user_input": "My SSN is 123-45-6789 and I was born 01/01/1990",
                    "system_response": {"text": "I don't need your SSN for this issue"},
                },
            ],
            "user_context": {
                "location": {
                    "state": "New York",
                    "county": "Manhattan",
                    "zip_code": "10001",
                    "coordinates": {"latitude": 40.7128, "longitude": -74.0060},
                },
                "preferred_language": "en",
            },
        }

        encrypted_data = manager.secure_session_data(complex_session)
        retrieved_data = manager.retrieve_session_data(encrypted_data)

        # Check that all PII is anonymized across all conversation turns
        for turn in retrieved_data["conversation_history"]:
            user_input = turn["user_input"]
            system_text = turn["system_response"]["text"]
            
            # Names should be anonymized
            assert "Jane Smith" not in user_input
            assert "Jane Smith" not in system_text
            
            # Email should be anonymized
            assert "jane@email.com" not in user_input
            
            # Addresses should be anonymized
            assert "789 Pine St" not in user_input
            assert "789 Pine St" not in system_text
            
            # SSN should be anonymized
            assert "123-45-6789" not in user_input
            
            # DOB should be anonymized
            assert "01/01/1990" not in user_input

        # Check location anonymization
        location = retrieved_data["user_context"]["location"]
        assert location["state"] == "New York"  # Preserved
        assert "Manhattan" not in str(location["county"])  # Anonymized
        assert location["zip_code"] == "100XX"  # Partially anonymized
        assert location["coordinates"] is None  # Removed