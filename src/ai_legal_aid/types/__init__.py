"""
Core type definitions for the AI Legal Aid System.

This module contains all the data models, enums, and type definitions
used throughout the system, converted from the TypeScript design document
to Python with proper type hints and Pydantic models.
"""

from ai_legal_aid.types.base import (
    SessionId,
    LegalIssueType,
    UrgencyLevel,
    ComplexityLevel,
    ContactMethod,
    DocumentType,
    IncomeRange,
)

from ai_legal_aid.types.models import (
    Location,
    GeographicArea,
    UserContext,
    LegalIssue,
    LegalGuidance,
    LegalCitation,
    OperatingHours,
    Address,
    ContactInfo,
    LegalAidOrganization,
    ResourceReferral,
    SearchCriteria,
    ConversationTurn,
    Session,
    ConversationContext,
    ConversationSummary,
    Action,
    SystemResponse,
    SpeechError,
    AudioBuffer,
    AuditRecord,
    SystemError,
)

__all__ = [
    # Base types and enums
    "SessionId",
    "LegalIssueType",
    "UrgencyLevel",
    "ComplexityLevel",
    "ContactMethod",
    "DocumentType",
    "IncomeRange",
    # Data models
    "Location",
    "GeographicArea",
    "UserContext",
    "LegalIssue",
    "LegalGuidance",
    "LegalCitation",
    "OperatingHours",
    "Address",
    "ContactInfo",
    "LegalAidOrganization",
    "ResourceReferral",
    "SearchCriteria",
    "ConversationTurn",
    "Session",
    "ConversationContext",
    "ConversationSummary",
    "Action",
    "SystemResponse",
    "SpeechError",
    "AudioBuffer",
    "AuditRecord",
    "SystemError",
]
