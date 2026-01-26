"""
AI Legal Aid System

A voice-enabled legal guidance system for underserved populations.
Provides first-level legal guidance, resource referrals, and clear
limitations about professional legal counsel requirements.
"""

__version__ = "0.1.0"
__author__ = "AI Legal Aid Team"
__email__ = "team@ai-legal-aid.org"

from ai_legal_aid.types import (
    # Core types
    SessionId,
    LegalIssueType,
    UrgencyLevel,
    ComplexityLevel,
    ContactMethod,
    DocumentType,
    IncomeRange,
    # Data models
    Location,
    UserContext,
    LegalIssue,
    LegalGuidance,
    LegalAidOrganization,
    Session,
    SystemResponse,
)

# Import implementations
from ai_legal_aid.session_manager import InMemorySessionManager, SessionNotFoundError

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    # Core types
    "SessionId",
    "LegalIssueType",
    "UrgencyLevel",
    "ComplexityLevel",
    "ContactMethod",
    "DocumentType",
    "IncomeRange",
    # Data models
    "Location",
    "UserContext",
    "LegalIssue",
    "LegalGuidance",
    "LegalAidOrganization",
    "Session",
    "SystemResponse",
    # Implementations
    "InMemorySessionManager",
    "SessionNotFoundError",
]
