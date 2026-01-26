"""
Encryption and privacy utilities for the AI Legal Aid System.

This module provides encryption, decryption, and PII anonymization
functionality to ensure data privacy and security compliance.
"""

import hashlib
import re
from typing import Any, Dict, List, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import json


class EncryptionManager:
    """
    Manages encryption and decryption of sensitive data.
    
    Uses Fernet symmetric encryption with PBKDF2 key derivation
    for secure data protection.
    """
    
    def __init__(self, password: Optional[str] = None):
        """
        Initialize encryption manager.
        
        Args:
            password: Password for key derivation. If None, generates a random key.
        """
        if password:
            # Derive key from password
            salt = b'ai_legal_aid_salt'  # In production, use random salt per session
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        else:
            # Generate random key
            key = Fernet.generate_key()
        
        self._fernet = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt string data.
        
        Args:
            data: String to encrypt
            
        Returns:
            Base64-encoded encrypted data
        """
        encrypted_data = self._fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt string data.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Decrypted string
        """
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = self._fernet.decrypt(decoded_data)
        return decrypted_data.decode()
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """
        Encrypt dictionary data as JSON.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Base64-encoded encrypted JSON
        """
        json_data = json.dumps(data, default=str)
        return self.encrypt(json_data)
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt dictionary data from JSON.
        
        Args:
            encrypted_data: Base64-encoded encrypted JSON
            
        Returns:
            Decrypted dictionary
        """
        json_data = self.decrypt(encrypted_data)
        return json.loads(json_data)


class PIIAnonymizer:
    """
    Anonymizes personally identifiable information in text and data structures.
    
    Detects and replaces common PII patterns with anonymized placeholders
    while preserving the structure and meaning of the data for legal guidance.
    """
    
    # PII patterns to detect and anonymize
    PII_PATTERNS = {
        'phone': r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'ssn': r'\b(?:\d{3}-?\d{2}-?\d{4})\b',
        'address': r'\b\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Court|Ct|Place|Pl)\b',
        'full_name': r'\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b',  # Simple first name + last name pattern
        'date_of_birth': r'\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b',
        'zip_code': r'\b\d{5}(?:-\d{4})?\b',
    }
    
    def __init__(self):
        """Initialize the PII anonymizer."""
        self._anonymization_map: Dict[str, str] = {}
        self._counter = 0
    
    def anonymize_text(self, text: str) -> str:
        """
        Anonymize PII in text while preserving legal context.
        
        Args:
            text: Text to anonymize
            
        Returns:
            Text with PII replaced by anonymized placeholders
        """
        anonymized_text = text
        
        # Process patterns in order of specificity (most specific first)
        pattern_order = ['email', 'phone', 'ssn', 'address', 'date_of_birth', 'zip_code', 'full_name']
        
        for pii_type in pattern_order:
            if pii_type not in self.PII_PATTERNS:
                continue
                
            pattern = self.PII_PATTERNS[pii_type]
            matches = list(re.finditer(pattern, anonymized_text, re.IGNORECASE))
            
            # Process matches in reverse order to avoid index shifting
            for match in reversed(matches):
                original = match.group(0)
                if original not in self._anonymization_map:
                    self._counter += 1
                    placeholder = f"[{pii_type.upper()}_{self._counter}]"
                    self._anonymization_map[original] = placeholder
                
                start, end = match.span()
                anonymized_text = (
                    anonymized_text[:start] + 
                    self._anonymization_map[original] + 
                    anonymized_text[end:]
                )
        
        return anonymized_text
    
    def anonymize_conversation_turn(self, turn_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize PII in a conversation turn while preserving structure.
        
        Args:
            turn_data: Conversation turn data dictionary
            
        Returns:
            Anonymized conversation turn data
        """
        anonymized_turn = turn_data.copy()
        
        # Anonymize user input
        if 'user_input' in anonymized_turn:
            anonymized_turn['user_input'] = self.anonymize_text(
                anonymized_turn['user_input']
            )
        
        # Anonymize system response text
        if 'system_response' in anonymized_turn:
            response = anonymized_turn['system_response']
            if isinstance(response, dict) and 'text' in response:
                response['text'] = self.anonymize_text(response['text'])
            elif isinstance(response, str):
                anonymized_turn['system_response'] = self.anonymize_text(response)
        
        return anonymized_turn
    
    def anonymize_user_context(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize PII in user context while preserving legal relevance.
        
        Args:
            context_data: User context data dictionary
            
        Returns:
            Anonymized user context data
        """
        anonymized_context = context_data.copy()
        
        # Anonymize location data but preserve general area for legal jurisdiction
        if 'location' in anonymized_context and anonymized_context['location']:
            location = anonymized_context['location']
            if isinstance(location, dict):
                # Keep state for legal jurisdiction, anonymize specific details
                if 'county' in location and location['county']:
                    location['county'] = f"[COUNTY_{self._get_hash(location['county'])[:8]}]"
                if 'zip_code' in location and location['zip_code']:
                    # Keep first 3 digits for general area, anonymize rest
                    zip_code = location['zip_code']
                    if len(zip_code) >= 3:
                        location['zip_code'] = zip_code[:3] + "XX"
                if 'coordinates' in location and location['coordinates']:
                    # Remove precise coordinates
                    location['coordinates'] = None
        
        return anonymized_context
    
    def _get_hash(self, text: str) -> str:
        """
        Generate a consistent hash for anonymization.
        
        Args:
            text: Text to hash
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(text.encode()).hexdigest()


class SecureDataManager:
    """
    Manages secure data operations including encryption and PII anonymization.
    
    Combines encryption and anonymization to provide comprehensive data protection
    for session data, conversation logs, and temporary files.
    """
    
    def __init__(self, encryption_password: Optional[str] = None):
        """
        Initialize secure data manager.
        
        Args:
            encryption_password: Password for encryption. If None, uses random key.
        """
        self.encryption_manager = EncryptionManager(encryption_password)
        self.pii_anonymizer = PIIAnonymizer()
    
    def secure_session_data(self, session_data: Dict[str, Any]) -> str:
        """
        Secure session data with encryption and PII anonymization.
        
        Args:
            session_data: Session data dictionary
            
        Returns:
            Encrypted session data
        """
        # First anonymize PII in conversation history
        secured_data = session_data.copy()
        
        if 'conversation_history' in secured_data:
            anonymized_history = []
            for turn in secured_data['conversation_history']:
                if isinstance(turn, dict):
                    anonymized_turn = self.pii_anonymizer.anonymize_conversation_turn(turn)
                    anonymized_history.append(anonymized_turn)
                else:
                    anonymized_history.append(turn)
            secured_data['conversation_history'] = anonymized_history
        
        # Anonymize user context
        if 'user_context' in secured_data:
            secured_data['user_context'] = self.pii_anonymizer.anonymize_user_context(
                secured_data['user_context']
            )
        
        # Then encrypt the entire session data
        return self.encryption_manager.encrypt_dict(secured_data)
    
    def retrieve_session_data(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Retrieve and decrypt session data.
        
        Args:
            encrypted_data: Encrypted session data
            
        Returns:
            Decrypted session data dictionary
        """
        return self.encryption_manager.decrypt_dict(encrypted_data)
    
    def secure_delete_file(self, file_path: str) -> bool:
        """
        Securely delete a file by overwriting it before deletion.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                return True
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Overwrite file with random data multiple times
            with open(file_path, 'r+b') as file:
                for _ in range(3):  # 3 passes of overwriting
                    file.seek(0)
                    file.write(os.urandom(file_size))
                    file.flush()
                    os.fsync(file.fileno())
            
            # Finally delete the file
            os.remove(file_path)
            return True
            
        except Exception:
            return False
    
    def secure_delete_audio_data(self, audio_buffer: bytes) -> None:
        """
        Securely clear audio data from memory.
        
        Args:
            audio_buffer: Audio data to clear
        """
        # Overwrite the buffer with zeros
        if hasattr(audio_buffer, '__len__'):
            # For mutable byte arrays, overwrite in place
            try:
                for i in range(len(audio_buffer)):
                    audio_buffer[i] = 0
            except (TypeError, AttributeError):
                # For immutable bytes, we can't overwrite in place
                # The garbage collector will handle cleanup
                pass