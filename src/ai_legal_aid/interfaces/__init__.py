"""
Interface definitions for the AI Legal Aid System.

This module contains Protocol definitions that specify the contracts
for all major system components. These interfaces ensure loose coupling
and enable dependency injection and testing.
"""

from ai_legal_aid.interfaces.voice import (
    SpeechToTextService,
    TextToSpeechService,
)

from ai_legal_aid.interfaces.session import (
    SessionManager,
)

from ai_legal_aid.interfaces.legal import (
    LegalGuidanceEngine,
    ConversationEngine,
)

from ai_legal_aid.interfaces.resources import (
    ResourceDirectory,
)

from ai_legal_aid.interfaces.compliance import (
    DisclaimerService,
)

__all__ = [
    # Voice interfaces
    "SpeechToTextService",
    "TextToSpeechService",
    # Session management
    "SessionManager",
    # Legal processing
    "LegalGuidanceEngine",
    "ConversationEngine",
    # Resource management
    "ResourceDirectory",
    # Compliance
    "DisclaimerService",
]
