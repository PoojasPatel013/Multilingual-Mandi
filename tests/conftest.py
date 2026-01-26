"""
Pytest configuration and shared fixtures for the AI Legal Aid System tests.

This module provides common test fixtures, configuration, and utilities
used across all test modules.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock

from hypothesis import settings, Verbosity
from hypothesis.strategies import SearchStrategy

from ai_legal_aid.types import (
    SessionId,
    Session,
    UserContext,
    Location,
    LegalIssue,
    LegalIssueType,
    UrgencyLevel,
    ComplexityLevel,
    LegalAidOrganization,
    ContactInfo,
    Address,
    OperatingHours,
    GeographicArea,
)

# Configure Hypothesis for property-based testing
settings.register_profile("default", max_examples=100, deadline=5000)
settings.register_profile("ci", max_examples=1000, deadline=10000)
settings.register_profile("debug", max_examples=10, verbosity=Verbosity.verbose)

# Load the appropriate profile
settings.load_profile("default")


@pytest.fixture
def sample_location() -> Location:
    """Sample location for testing."""
    return Location(
        state="CA",
        county="Los Angeles",
        zip_code="90210",
        coordinates={"latitude": 34.0522, "longitude": -118.2437},
    )


@pytest.fixture
def sample_user_context(sample_location: Location) -> UserContext:
    """Sample user context for testing."""
    return UserContext(
        location=sample_location,
        preferred_language="en",
        legal_issue_type=LegalIssueType.TENANT_RIGHTS,
        urgency_level=UrgencyLevel.MEDIUM,
        has_minor_children=False,
        household_income=None,
    )


@pytest.fixture
def sample_legal_issue() -> LegalIssue:
    """Sample legal issue for testing."""
    return LegalIssue(
        type=LegalIssueType.TENANT_RIGHTS,
        description="Landlord is refusing to fix broken heating system",
        urgency=UrgencyLevel.HIGH,
        complexity=ComplexityLevel.MODERATE,
        involved_parties=["landlord", "tenant"],
        timeframe="last week",
        documents=[],
    )


@pytest.fixture
def sample_session_id() -> SessionId:
    """Sample session ID for testing."""
    return SessionId("test-session-123")


@pytest.fixture
def sample_session(
    sample_session_id: SessionId, sample_user_context: UserContext
) -> Session:
    """Sample session for testing."""
    return Session(
        id=sample_session_id,
        start_time=datetime.now(),
        last_activity=datetime.now(),
        language="en",
        conversation_history=[],
        user_context=sample_user_context,
        disclaimer_acknowledged=False,
    )


@pytest.fixture
def sample_address() -> Address:
    """Sample address for testing."""
    return Address(
        street="123 Legal Aid St",
        city="Los Angeles",
        state="CA",
        zip_code="90210",
        country="US",
    )


@pytest.fixture
def sample_operating_hours() -> OperatingHours:
    """Sample operating hours for testing."""
    return OperatingHours(
        monday={"open": "09:00", "close": "17:00"},
        tuesday={"open": "09:00", "close": "17:00"},
        wednesday={"open": "09:00", "close": "17:00"},
        thursday={"open": "09:00", "close": "17:00"},
        friday={"open": "09:00", "close": "17:00"},
        notes="Closed on weekends",
    )


@pytest.fixture
def sample_contact_info(
    sample_address: Address, sample_operating_hours: OperatingHours
) -> ContactInfo:
    """Sample contact info for testing."""
    return ContactInfo(
        phone="(555) 123-4567",
        email="help@legalaid.org",
        address=sample_address,
        website="https://www.legalaid.org",
        intake_hours=sample_operating_hours,
    )


@pytest.fixture
def sample_legal_aid_org(
    sample_contact_info: ContactInfo, sample_operating_hours: OperatingHours
) -> LegalAidOrganization:
    """Sample legal aid organization for testing."""
    return LegalAidOrganization(
        id="org-123",
        name="Los Angeles Legal Aid",
        contact_info=sample_contact_info,
        specializations=[LegalIssueType.TENANT_RIGHTS, LegalIssueType.WAGE_THEFT],
        service_area=GeographicArea(
            states=["CA"],
            counties=["Los Angeles"],
            zip_codes=["90210", "90211", "90212"],
        ),
        languages=["en", "es"],
        availability=sample_operating_hours,
        eligibility_requirements=["Income below 200% of federal poverty level"],
    )


@pytest.fixture
def mock_session_manager() -> Mock:
    """Mock session manager for testing."""
    return Mock()


@pytest.fixture
def mock_legal_guidance_engine() -> Mock:
    """Mock legal guidance engine for testing."""
    return Mock()


@pytest.fixture
def mock_resource_directory() -> Mock:
    """Mock resource directory for testing."""
    return Mock()


@pytest.fixture
def mock_disclaimer_service() -> Mock:
    """Mock disclaimer service for testing."""
    return Mock()


@pytest.fixture
def mock_speech_to_text_service() -> Mock:
    """Mock speech-to-text service for testing."""
    return Mock()


@pytest.fixture
def mock_text_to_speech_service() -> Mock:
    """Mock text-to-speech service for testing."""
    return Mock()


# Test utilities
def create_test_session(
    session_id: str = "test-session", language: str = "en", **kwargs: Any
) -> Session:
    """Create a test session with default values."""
    defaults = {
        "id": SessionId(session_id),
        "start_time": datetime.now(),
        "last_activity": datetime.now(),
        "language": language,
        "conversation_history": [],
        "user_context": UserContext(preferred_language=language),
        "disclaimer_acknowledged": False,
    }
    defaults.update(kwargs)
    return Session(**defaults)


def create_test_legal_issue(
    issue_type: LegalIssueType = LegalIssueType.OTHER, **kwargs: Any
) -> LegalIssue:
    """Create a test legal issue with default values."""
    defaults = {
        "type": issue_type,
        "description": "Test legal issue",
        "urgency": UrgencyLevel.MEDIUM,
        "complexity": ComplexityLevel.SIMPLE,
        "involved_parties": [],
        "timeframe": None,
        "documents": [],
    }
    defaults.update(kwargs)
    return LegalIssue(**defaults)
