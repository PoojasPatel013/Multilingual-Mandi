"""
Base types and enums for the AI Legal Aid System.

This module defines the fundamental types and enumerations used throughout
the system, providing type safety and clear categorization of legal issues,
urgency levels, and other core concepts.
"""

from enum import Enum
from typing import NewType

# Type aliases
SessionId = NewType("SessionId", str)


class LegalIssueType(str, Enum):
    """Categories of legal issues the system can handle."""

    LAND_DISPUTE = "land_dispute"
    DOMESTIC_VIOLENCE = "domestic_violence"
    WAGE_THEFT = "wage_theft"
    TENANT_RIGHTS = "tenant_rights"
    OTHER = "other"


class UrgencyLevel(str, Enum):
    """Urgency levels for legal issues."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class ComplexityLevel(str, Enum):
    """Complexity levels for legal issues."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class ContactMethod(str, Enum):
    """Methods for contacting legal aid organizations."""

    PHONE = "phone"
    EMAIL = "email"
    WALK_IN = "walk_in"
    ONLINE = "online"


class DocumentType(str, Enum):
    """Types of legal documents users might have."""

    CONTRACT = "contract"
    LEASE = "lease"
    EMPLOYMENT_RECORD = "employment_record"
    COURT_DOCUMENT = "court_document"
    IDENTIFICATION = "identification"
    OTHER = "other"


class IncomeRange(str, Enum):
    """Income ranges for eligibility determination."""

    VERY_LOW = "very_low"  # Below 30% AMI
    LOW = "low"  # 30-50% AMI
    MODERATE = "moderate"  # 50-80% AMI
    ABOVE_MODERATE = "above_moderate"  # Above 80% AMI
