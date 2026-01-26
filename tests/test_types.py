"""
Unit tests for AI Legal Aid System types and data models.

This module tests the core data types, validation logic, and
serialization/deserialization of Pydantic models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from ai_legal_aid.types import (
    SessionId,
    LegalIssueType,
    UrgencyLevel,
    ComplexityLevel,
    Location,
    UserContext,
    LegalIssue,
    Session,
    LegalAidOrganization,
)


class TestLocation:
    """Test Location model validation and functionality."""

    def test_valid_location_creation(self):
        """Test creating a valid location."""
        location = Location(
            state="CA",
            county="Los Angeles",
            zip_code="90210",
            coordinates={"latitude": 34.0522, "longitude": -118.2437},
        )

        assert location.state == "CA"
        assert location.county == "Los Angeles"
        assert location.zip_code == "90210"
        assert location.coordinates["latitude"] == 34.0522
        assert location.coordinates["longitude"] == -118.2437

    def test_location_with_minimal_data(self):
        """Test creating location with only required fields."""
        location = Location(state="NY")

        assert location.state == "NY"
        assert location.county is None
        assert location.zip_code is None
        assert location.coordinates is None

    def test_invalid_coordinates_validation(self):
        """Test validation of invalid coordinates."""
        with pytest.raises(ValidationError) as exc_info:
            Location(
                state="CA",
                coordinates={
                    "latitude": 100.0,
                    "longitude": -118.2437,
                },  # Invalid latitude
            )

        assert "Latitude must be between -90 and 90" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            Location(
                state="CA",
                coordinates={
                    "latitude": 34.0522,
                    "longitude": 200.0,
                },  # Invalid longitude
            )

        assert "Longitude must be between -180 and 180" in str(exc_info.value)

    def test_incomplete_coordinates_validation(self):
        """Test validation when coordinates are incomplete."""
        with pytest.raises(ValidationError) as exc_info:
            Location(state="CA", coordinates={"latitude": 34.0522})  # Missing longitude

        assert "Coordinates must include latitude and longitude" in str(exc_info.value)


class TestUserContext:
    """Test UserContext model validation and functionality."""

    def test_valid_user_context_creation(self, sample_location):
        """Test creating a valid user context."""
        context = UserContext(
            location=sample_location,
            preferred_language="en",
            legal_issue_type=LegalIssueType.TENANT_RIGHTS,
            urgency_level=UrgencyLevel.HIGH,
            has_minor_children=True,
            household_income=None,
        )

        assert context.location == sample_location
        assert context.preferred_language == "en"
        assert context.legal_issue_type == LegalIssueType.TENANT_RIGHTS
        assert context.urgency_level == UrgencyLevel.HIGH
        assert context.has_minor_children is True
        assert context.household_income is None

    def test_user_context_defaults(self):
        """Test user context with default values."""
        context = UserContext()

        assert context.location is None
        assert context.preferred_language == "en"
        assert context.legal_issue_type is None
        assert context.urgency_level is None
        assert context.has_minor_children is None
        assert context.household_income is None


class TestLegalIssue:
    """Test LegalIssue model validation and functionality."""

    def test_valid_legal_issue_creation(self):
        """Test creating a valid legal issue."""
        issue = LegalIssue(
            type=LegalIssueType.WAGE_THEFT,
            description="Employer hasn't paid overtime wages",
            urgency=UrgencyLevel.HIGH,
            complexity=ComplexityLevel.MODERATE,
            involved_parties=["employer", "employee"],
            timeframe="last month",
            documents=[],
        )

        assert issue.type == LegalIssueType.WAGE_THEFT
        assert issue.description == "Employer hasn't paid overtime wages"
        assert issue.urgency == UrgencyLevel.HIGH
        assert issue.complexity == ComplexityLevel.MODERATE
        assert issue.involved_parties == ["employer", "employee"]
        assert issue.timeframe == "last month"
        assert issue.documents == []

    def test_legal_issue_with_minimal_data(self):
        """Test creating legal issue with minimal required data."""
        issue = LegalIssue(
            type=LegalIssueType.OTHER,
            description="General legal question",
            urgency=UrgencyLevel.LOW,
            complexity=ComplexityLevel.SIMPLE,
        )

        assert issue.type == LegalIssueType.OTHER
        assert issue.description == "General legal question"
        assert issue.urgency == UrgencyLevel.LOW
        assert issue.complexity == ComplexityLevel.SIMPLE
        assert issue.involved_parties == []
        assert issue.timeframe is None
        assert issue.documents == []


class TestSession:
    """Test Session model validation and functionality."""

    def test_valid_session_creation(self, sample_session_id, sample_user_context):
        """Test creating a valid session."""
        session = Session(
            id=sample_session_id,
            start_time=datetime.now(),
            last_activity=datetime.now(),
            language="en",
            conversation_history=[],
            user_context=sample_user_context,
            disclaimer_acknowledged=False,
        )

        assert session.id == sample_session_id
        assert session.language == "en"
        assert session.user_context == sample_user_context
        assert session.disclaimer_acknowledged is False
        assert len(session.conversation_history) == 0

    def test_session_with_defaults(self, sample_session_id):
        """Test session creation with default values."""
        session = Session(id=sample_session_id)

        assert session.id == sample_session_id
        assert session.language == "en"
        assert isinstance(session.user_context, UserContext)
        assert session.disclaimer_acknowledged is False
        assert len(session.conversation_history) == 0
        assert isinstance(session.start_time, datetime)
        assert isinstance(session.last_activity, datetime)


class TestLegalAidOrganization:
    """Test LegalAidOrganization model validation and functionality."""

    def test_valid_organization_creation(self, sample_legal_aid_org):
        """Test creating a valid legal aid organization."""
        org = sample_legal_aid_org

        assert org.id == "org-123"
        assert org.name == "Los Angeles Legal Aid"
        assert LegalIssueType.TENANT_RIGHTS in org.specializations
        assert LegalIssueType.WAGE_THEFT in org.specializations
        assert "en" in org.languages
        assert "es" in org.languages
        assert len(org.eligibility_requirements) > 0

    def test_organization_serialization(self, sample_legal_aid_org):
        """Test organization serialization to dict."""
        org = sample_legal_aid_org
        org_dict = org.model_dump()

        assert org_dict["id"] == "org-123"
        assert org_dict["name"] == "Los Angeles Legal Aid"
        assert "contact_info" in org_dict
        assert "specializations" in org_dict
        assert "service_area" in org_dict

    def test_organization_json_serialization(self, sample_legal_aid_org):
        """Test organization JSON serialization."""
        org = sample_legal_aid_org
        json_str = org.model_dump_json()

        assert isinstance(json_str, str)
        assert "org-123" in json_str
        assert "Los Angeles Legal Aid" in json_str


class TestEnums:
    """Test enum values and functionality."""

    def test_legal_issue_type_values(self):
        """Test LegalIssueType enum values."""
        assert LegalIssueType.LAND_DISPUTE == "land_dispute"
        assert LegalIssueType.DOMESTIC_VIOLENCE == "domestic_violence"
        assert LegalIssueType.WAGE_THEFT == "wage_theft"
        assert LegalIssueType.TENANT_RIGHTS == "tenant_rights"
        assert LegalIssueType.OTHER == "other"

    def test_urgency_level_values(self):
        """Test UrgencyLevel enum values."""
        assert UrgencyLevel.LOW == "low"
        assert UrgencyLevel.MEDIUM == "medium"
        assert UrgencyLevel.HIGH == "high"
        assert UrgencyLevel.EMERGENCY == "emergency"

    def test_complexity_level_values(self):
        """Test ComplexityLevel enum values."""
        assert ComplexityLevel.SIMPLE == "simple"
        assert ComplexityLevel.MODERATE == "moderate"
        assert ComplexityLevel.COMPLEX == "complex"

    def test_enum_iteration(self):
        """Test that enums can be iterated."""
        issue_types = list(LegalIssueType)
        assert len(issue_types) == 5
        assert LegalIssueType.TENANT_RIGHTS in issue_types

        urgency_levels = list(UrgencyLevel)
        assert len(urgency_levels) == 4
        assert UrgencyLevel.EMERGENCY in urgency_levels
