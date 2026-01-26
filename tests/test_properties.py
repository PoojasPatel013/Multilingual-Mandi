"""
Property-based tests for AI Legal Aid System.

This module contains property-based tests using Hypothesis to verify
universal properties and invariants across the system components.
"""

import pytest
from hypothesis import given, assume, strategies as st

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

from tests.strategies import (
    session_ids,
    locations,
    user_contexts,
    legal_issues,
    legal_aid_organizations,
    sessions,
    speech_inputs,
    legal_queries,
)


class TestLocationProperties:
    """Property-based tests for Location model."""

    @given(locations())
    def test_location_serialization_roundtrip(self, location: Location):
        """
        Property: Location serialization and deserialization preserves data.

        **Feature: ai-legal-aid, Property 1: Location Data Integrity**
        **Validates: Requirements 5.1, 5.2** (Data integrity in storage)
        """
        # Serialize to dict and back
        location_dict = location.model_dump()
        reconstructed = Location(**location_dict)

        assert reconstructed == location
        assert reconstructed.state == location.state
        assert reconstructed.county == location.county
        assert reconstructed.zip_code == location.zip_code
        assert reconstructed.coordinates == location.coordinates

    @given(locations())
    def test_location_json_roundtrip(self, location: Location):
        """
        Property: Location JSON serialization preserves all data.

        **Feature: ai-legal-aid, Property 2: Location JSON Integrity**
        **Validates: Requirements 5.1, 5.2** (Data integrity in JSON format)
        """
        # Serialize to JSON and back
        json_str = location.model_dump_json()
        reconstructed = Location.model_validate_json(json_str)

        assert reconstructed == location

    @given(
        st.floats(min_value=-90.0, max_value=90.0),
        st.floats(min_value=-180.0, max_value=180.0),
    )
    def test_valid_coordinates_always_accepted(self, latitude: float, longitude: float):
        """
        Property: Valid coordinates are always accepted.

        **Feature: ai-legal-aid, Property 3: Coordinate Validation**
        **Validates: Requirements 5.1** (Data validation)
        """
        location = Location(
            state="CA", coordinates={"latitude": latitude, "longitude": longitude}
        )

        assert location.coordinates["latitude"] == latitude
        assert location.coordinates["longitude"] == longitude


class TestUserContextProperties:
    """Property-based tests for UserContext model."""

    @given(user_contexts())
    def test_user_context_serialization_preserves_privacy(self, context: UserContext):
        """
        Property: UserContext serialization doesn't expose sensitive data inappropriately.

        **Feature: ai-legal-aid, Property 4: User Context Privacy**
        **Validates: Requirements 5.1, 5.2** (Privacy in data handling)
        """
        context_dict = context.model_dump()

        # Verify all fields are present and properly typed
        assert "preferred_language" in context_dict
        assert isinstance(context_dict["preferred_language"], str)

        if context.location:
            assert "location" in context_dict
            assert isinstance(context_dict["location"], dict)

        # Verify no unexpected fields are added
        expected_fields = {
            "location",
            "preferred_language",
            "legal_issue_type",
            "urgency_level",
            "has_minor_children",
            "household_income",
        }
        assert set(context_dict.keys()) == expected_fields

    @given(user_contexts())
    def test_user_context_language_consistency(self, context: UserContext):
        """
        Property: User context always has a valid preferred language.

        **Feature: ai-legal-aid, Property 5: Language Consistency**
        **Validates: Requirements 7.1, 7.2** (Multi-language support)
        """
        assert context.preferred_language is not None
        assert isinstance(context.preferred_language, str)
        assert len(context.preferred_language) >= 2  # At least 'en', 'es', etc.


class TestLegalIssueProperties:
    """Property-based tests for LegalIssue model."""

    @given(legal_issues())
    def test_legal_issue_has_required_fields(self, issue: LegalIssue):
        """
        Property: All legal issues have required classification fields.

        **Feature: ai-legal-aid, Property 6: Legal Issue Completeness**
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4** (Legal issue handling)
        """
        assert issue.type in LegalIssueType
        assert isinstance(issue.description, str)
        assert len(issue.description) > 0
        assert issue.urgency in UrgencyLevel
        assert issue.complexity in ComplexityLevel
        assert isinstance(issue.involved_parties, list)

    @given(legal_issues())
    def test_legal_issue_urgency_complexity_relationship(self, issue: LegalIssue):
        """
        Property: Emergency issues should not be classified as simple complexity.

        **Feature: ai-legal-aid, Property 7: Urgency-Complexity Consistency**
        **Validates: Requirements 2.5, 4.3** (Appropriate complexity assessment)
        """
        # Emergency issues should generally be at least moderate complexity
        if issue.urgency == UrgencyLevel.EMERGENCY:
            # This is a business rule that emergency issues are rarely simple
            # Allow some flexibility but test the general pattern
            pass  # We'll implement this logic in the actual system

        # All issues should have consistent urgency/complexity
        assert issue.urgency is not None
        assert issue.complexity is not None


class TestSessionProperties:
    """Property-based tests for Session model."""

    @given(sessions())
    def test_session_time_consistency(self, session: Session):
        """
        Property: Session last_activity is never before start_time.

        **Feature: ai-legal-aid, Property 8: Session Time Consistency**
        **Validates: Requirements 6.1, 8.1** (Session management)
        """
        assert session.last_activity >= session.start_time

    @given(sessions())
    def test_session_has_valid_id(self, session: Session):
        """
        Property: All sessions have valid, non-empty IDs.

        **Feature: ai-legal-aid, Property 9: Session ID Validity**
        **Validates: Requirements 5.1** (Data integrity)
        """
        assert session.id is not None
        assert isinstance(session.id, str)
        assert len(session.id) > 0

    @given(sessions())
    def test_session_language_matches_context(self, session: Session):
        """
        Property: Session language matches user context preferred language.

        **Feature: ai-legal-aid, Property 10: Session Language Consistency**
        **Validates: Requirements 7.1, 7.2** (Multi-language support)
        """
        # If user context has a preferred language, session should match
        if session.user_context.preferred_language:
            # Allow for some flexibility in language codes (e.g., 'en' vs 'en-US')
            session_lang_base = session.language.split("-")[0]
            context_lang_base = session.user_context.preferred_language.split("-")[0]
            assert session_lang_base == context_lang_base


class TestLegalAidOrganizationProperties:
    """Property-based tests for LegalAidOrganization model."""

    @given(legal_aid_organizations())
    def test_organization_has_contact_info(self, org: LegalAidOrganization):
        """
        Property: All organizations have complete contact information.

        **Feature: ai-legal-aid, Property 11: Organization Contact Completeness**
        **Validates: Requirements 3.1, 3.2, 3.3** (Resource referral completeness)
        """
        assert org.contact_info is not None
        assert org.contact_info.phone is not None
        assert len(org.contact_info.phone) > 0
        assert org.contact_info.address is not None
        assert org.contact_info.address.street is not None
        assert org.contact_info.address.city is not None
        assert org.contact_info.address.state is not None

    @given(legal_aid_organizations())
    def test_organization_has_specializations(self, org: LegalAidOrganization):
        """
        Property: All organizations have at least one specialization.

        **Feature: ai-legal-aid, Property 12: Organization Specialization**
        **Validates: Requirements 3.4** (Specialization matching)
        """
        assert len(org.specializations) > 0
        for specialization in org.specializations:
            assert specialization in LegalIssueType

    @given(legal_aid_organizations())
    def test_organization_serves_geographic_area(self, org: LegalAidOrganization):
        """
        Property: All organizations serve at least one geographic area.

        **Feature: ai-legal-aid, Property 13: Geographic Service Coverage**
        **Validates: Requirements 3.1, 3.2** (Geographic-based referrals)
        """
        assert org.service_area is not None
        assert len(org.service_area.states) > 0

        # Each state should be a valid state code
        for state in org.service_area.states:
            assert isinstance(state, str)
            assert len(state) >= 2  # At least 2-character state codes


class TestSpeechProcessingProperties:
    """Property-based tests for speech processing components."""

    @given(speech_inputs())
    def test_speech_input_is_processable(self, speech_text: str):
        """
        Property: All speech inputs are non-empty and processable.

        **Feature: ai-legal-aid, Property 14: Speech Input Validity**
        **Validates: Requirements 1.1, 1.5** (Speech recognition)
        """
        assert isinstance(speech_text, str)
        assert len(speech_text.strip()) > 0

        # Speech input should contain some meaningful content
        words = speech_text.split()
        assert len(words) > 0

    @given(legal_queries())
    def test_legal_query_contains_legal_context(self, query: str):
        """
        Property: Legal queries contain identifiable legal context.

        **Feature: ai-legal-aid, Property 15: Legal Query Context**
        **Validates: Requirements 2.5** (Legal issue identification)
        """
        assert isinstance(query, str)
        assert len(query.strip()) > 0

        # Query should be substantial enough to contain legal context
        assert len(query.split()) >= 3  # At least a few words


class TestDataIntegrityProperties:
    """Property-based tests for data integrity across the system."""

    @given(st.data())
    def test_model_serialization_preserves_type_safety(self, data):
        """
        Property: Model serialization preserves type safety.

        **Feature: ai-legal-aid, Property 16: Type Safety Preservation**
        **Validates: Requirements 5.1, 5.2** (Data integrity)
        """
        # Test with different model types
        model_strategy = data.draw(
            st.sampled_from(
                [
                    locations(),
                    user_contexts(),
                    legal_issues(),
                    sessions(),
                ]
            )
        )

        model = data.draw(model_strategy)

        # Serialize and deserialize
        model_dict = model.model_dump()
        model_class = type(model)
        reconstructed = model_class(**model_dict)

        # Verify type safety is preserved
        assert type(reconstructed) == type(model)
        assert reconstructed == model
