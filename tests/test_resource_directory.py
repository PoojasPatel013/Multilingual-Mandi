"""
Tests for the Resource Directory implementation.

This module tests the legal aid organization management,
search functionality, and referral generation.
"""

import pytest

from ai_legal_aid.resource_directory import BasicResourceDirectory, OrganizationNotFoundError
from ai_legal_aid.types import (
    LegalIssueType,
    UrgencyLevel,
    Location,
    SearchCriteria,
)


@pytest.fixture
def resource_directory():
    """Create a resource directory for testing."""
    return BasicResourceDirectory()


@pytest.fixture
def sample_location():
    """Create a sample location for testing."""
    return Location(
        state="CA",
        county="Los Angeles",
        zip_code="90012"
    )


@pytest.fixture
def sample_search_criteria(sample_location):
    """Create sample search criteria for testing."""
    return SearchCriteria(
        location=sample_location,
        issue_type=LegalIssueType.TENANT_RIGHTS,
        language="en",
        urgency=UrgencyLevel.MEDIUM
    )


class TestResourceDirectory:
    """Test basic resource directory functionality."""

    @pytest.mark.asyncio
    async def test_find_organizations_by_issue_type(self, resource_directory, sample_location):
        """Test finding organizations by legal issue type."""
        criteria = SearchCriteria(
            location=sample_location,
            issue_type=LegalIssueType.DOMESTIC_VIOLENCE
        )
        
        organizations = await resource_directory.find_organizations(criteria)
        
        assert len(organizations) > 0
        for org in organizations:
            assert LegalIssueType.DOMESTIC_VIOLENCE in org.specializations

    @pytest.mark.asyncio
    async def test_find_organizations_by_location(self, resource_directory):
        """Test finding organizations by location."""
        criteria = SearchCriteria(
            location=Location(state="CA", county="Los Angeles"),
            issue_type=LegalIssueType.TENANT_RIGHTS
        )
        
        organizations = await resource_directory.find_organizations(criteria)
        
        assert len(organizations) > 0
        for org in organizations:
            # Should serve CA either directly or through national coverage
            assert "CA" in org.service_area.states or "ALL" in org.service_area.states
            assert LegalIssueType.TENANT_RIGHTS in org.specializations

    @pytest.mark.asyncio
    async def test_find_organizations_by_language(self, resource_directory, sample_location):
        """Test finding organizations by language support."""
        criteria = SearchCriteria(
            location=sample_location,
            language="es"
        )
        
        organizations = await resource_directory.find_organizations(criteria)
        
        assert len(organizations) > 0
        for org in organizations:
            assert "es" in org.languages

    @pytest.mark.asyncio
    async def test_get_organization_details(self, resource_directory):
        """Test getting detailed organization information."""
        org_id = "legal_aid_society_la"
        
        org = await resource_directory.get_organization_details(org_id)
        
        assert org.id == org_id
        assert org.name == "Legal Aid Society of Los Angeles"
        assert org.contact_info.phone == "(213) 555-0123"

    @pytest.mark.asyncio
    async def test_get_organization_details_not_found(self, resource_directory):
        """Test getting details for non-existent organization."""
        with pytest.raises(OrganizationNotFoundError):
            await resource_directory.get_organization_details("nonexistent_org")

    @pytest.mark.asyncio
    async def test_update_organization_info(self, resource_directory):
        """Test updating organization information."""
        org_id = "legal_aid_society_la"
        updates = {"name": "Updated Legal Aid Society"}
        
        await resource_directory.update_organization_info(org_id, updates)
        
        org = await resource_directory.get_organization_details(org_id)
        assert org.name == "Updated Legal Aid Society"

    @pytest.mark.asyncio
    async def test_update_organization_info_not_found(self, resource_directory):
        """Test updating non-existent organization."""
        with pytest.raises(OrganizationNotFoundError):
            await resource_directory.update_organization_info("nonexistent_org", {"name": "Test"})

    @pytest.mark.asyncio
    async def test_search_by_specialization(self, resource_directory, sample_location):
        """Test searching by specialization and location."""
        organizations = await resource_directory.search_by_specialization(
            LegalIssueType.WAGE_THEFT, sample_location
        )
        
        assert len(organizations) > 0
        for org in organizations:
            assert LegalIssueType.WAGE_THEFT in org.specializations


class TestRelevanceScoring:
    """Test relevance scoring and ranking functionality."""

    @pytest.mark.asyncio
    async def test_organizations_ranked_by_relevance(self, resource_directory):
        """Test that organizations are ranked by relevance."""
        criteria = SearchCriteria(
            location=Location(state="CA", county="Los Angeles"),
            issue_type=LegalIssueType.DOMESTIC_VIOLENCE,
            language="en",
            urgency=UrgencyLevel.EMERGENCY
        )
        
        organizations = await resource_directory.find_organizations(criteria)
        
        assert len(organizations) > 1
        
        # First organization should be most relevant
        first_org = organizations[0]
        assert LegalIssueType.DOMESTIC_VIOLENCE in first_org.specializations

    @pytest.mark.asyncio
    async def test_national_organizations_included(self, resource_directory):
        """Test that national organizations are included in results."""
        criteria = SearchCriteria(
            location=Location(state="TX", county="Harris"),  # Different state
            issue_type=LegalIssueType.DOMESTIC_VIOLENCE
        )
        
        organizations = await resource_directory.find_organizations(criteria)
        
        # Should include national domestic violence hotline
        national_orgs = [org for org in organizations if "National" in org.name]
        assert len(national_orgs) > 0


class TestReferralGeneration:
    """Test referral generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_referrals(self, resource_directory, sample_search_criteria):
        """Test generating resource referrals."""
        referrals = await resource_directory.generate_referrals(sample_search_criteria)
        
        assert len(referrals) > 0
        assert len(referrals) <= 3  # Default max referrals
        
        for referral in referrals:
            assert 0.0 <= referral.relevance_score <= 1.0
            assert len(referral.next_steps) > 0
            assert referral.contact_method is not None

    @pytest.mark.asyncio
    async def test_emergency_referrals(self, resource_directory, sample_location):
        """Test referrals for emergency situations."""
        criteria = SearchCriteria(
            location=sample_location,
            issue_type=LegalIssueType.DOMESTIC_VIOLENCE,
            urgency=UrgencyLevel.EMERGENCY
        )
        
        referrals = await resource_directory.generate_referrals(criteria)
        
        assert len(referrals) > 0
        
        # Emergency referrals should prioritize immediate assistance
        first_referral = referrals[0]
        assert "emergency" in " ".join(first_referral.next_steps).lower() or \
               "immediate" in " ".join(first_referral.next_steps).lower()

    @pytest.mark.asyncio
    async def test_referral_next_steps(self, resource_directory, sample_search_criteria):
        """Test that referrals include appropriate next steps."""
        referrals = await resource_directory.generate_referrals(sample_search_criteria)
        
        assert len(referrals) > 0
        
        first_referral = referrals[0]
        next_steps = first_referral.next_steps
        
        # Should include contact information
        assert any("call" in step.lower() for step in next_steps)
        
        # Should include preparation advice
        assert any("gather" in step.lower() or "document" in step.lower() for step in next_steps)

    @pytest.mark.asyncio
    async def test_wait_time_estimation(self, resource_directory, sample_search_criteria):
        """Test wait time estimation for referrals."""
        referrals = await resource_directory.generate_referrals(sample_search_criteria)
        
        assert len(referrals) > 0
        
        for referral in referrals:
            # Wait time should be provided for most referrals
            if referral.estimated_wait_time:
                assert isinstance(referral.estimated_wait_time, str)
                assert len(referral.estimated_wait_time) > 0


class TestGeographicMatching:
    """Test geographic matching functionality."""

    def test_serves_location_state_match(self, resource_directory):
        """Test location matching by state."""
        # Get a known organization
        org = resource_directory._organizations["legal_aid_society_la"]
        location = Location(state="CA", county="Los Angeles")
        
        assert resource_directory._serves_location(org, location) is True

    def test_serves_location_state_mismatch(self, resource_directory):
        """Test location matching with wrong state."""
        org = resource_directory._organizations["legal_aid_society_la"]
        location = Location(state="NY", county="New York")
        
        assert resource_directory._serves_location(org, location) is False

    def test_serves_location_national_coverage(self, resource_directory):
        """Test location matching for national organizations."""
        org = resource_directory._organizations["national_domestic_violence_hotline"]
        location = Location(state="TX", county="Harris")
        
        assert resource_directory._serves_location(org, location) is True

    def test_calculate_relevance_score(self, resource_directory):
        """Test relevance score calculation."""
        org = resource_directory._organizations["legal_aid_society_la"]
        criteria = SearchCriteria(
            location=Location(state="CA", county="Los Angeles"),
            issue_type=LegalIssueType.TENANT_RIGHTS,
            language="en"
        )
        
        score = resource_directory._calculate_relevance_score(org, criteria)
        
        assert score > 0
        assert isinstance(score, float)

    def test_24_hour_availability_detection(self, resource_directory):
        """Test detection of 24-hour availability."""
        # Domestic violence organizations should have 24-hour availability
        dv_org = resource_directory._organizations["domestic_violence_center_ca"]
        assert resource_directory._has_24_hour_availability(dv_org) is True
        
        # Regular legal aid should not have 24-hour availability
        regular_org = resource_directory._organizations["legal_aid_society_la"]
        assert resource_directory._has_24_hour_availability(regular_org) is False


class TestFallbackResourceHandling:
    """Test fallback resource handling functionality."""

    @pytest.mark.asyncio
    async def test_fallback_when_no_local_resources(self, resource_directory):
        """Test that national resources are provided when no local resources exist."""
        # Use a location with no local resources
        remote_criteria = SearchCriteria(
            location=Location(state="WY", county="Teton"),
            issue_type=LegalIssueType.WAGE_THEFT,
            language="en"
        )
        
        organizations = await resource_directory.find_organizations(remote_criteria)
        
        assert len(organizations) > 0
        # All returned organizations should be national resources
        for org in organizations:
            assert "ALL" in org.service_area.states
            assert LegalIssueType.WAGE_THEFT in org.specializations

    @pytest.mark.asyncio
    async def test_fallback_referrals_include_context(self, resource_directory):
        """Test that fallback referrals include appropriate context messaging."""
        remote_criteria = SearchCriteria(
            location=Location(state="MT", county="Glacier"),
            issue_type=LegalIssueType.TENANT_RIGHTS,
            language="en"
        )
        
        referrals = await resource_directory.generate_referrals(remote_criteria)
        
        assert len(referrals) > 0
        
        # Check that fallback messaging is included
        first_referral = referrals[0]
        next_steps_text = " ".join(first_referral.next_steps).lower()
        
        assert "no local legal aid organizations found" in next_steps_text
        assert "national resource" in next_steps_text

    @pytest.mark.asyncio
    async def test_local_resources_prioritized_over_national(self, resource_directory):
        """Test that local resources are prioritized when available."""
        # Use Los Angeles which has local resources
        local_criteria = SearchCriteria(
            location=Location(state="CA", county="Los Angeles"),
            issue_type=LegalIssueType.DOMESTIC_VIOLENCE,
            language="en"
        )
        
        organizations = await resource_directory.find_organizations(local_criteria)
        
        assert len(organizations) > 1  # Should have both local and national
        
        # First organization should be local (higher relevance score)
        first_org = organizations[0]
        assert "CA" in first_org.service_area.states
        assert "ALL" not in first_org.service_area.states

    @pytest.mark.asyncio
    async def test_resource_availability_validation(self, resource_directory):
        """Test resource availability validation."""
        # Test with a known organization
        org = resource_directory._organizations["legal_aid_society_la"]
        
        # Should pass validation
        assert resource_directory._validate_resource_availability(org) is True
        assert resource_directory._validate_contact_info(org) is True

    @pytest.mark.asyncio
    async def test_national_resource_identification(self, resource_directory):
        """Test identification of national vs local resources."""
        # Test national resource
        national_org = resource_directory._organizations["national_domestic_violence_hotline"]
        assert resource_directory._is_national_resource(national_org) is True
        
        # Test local resource
        local_org = resource_directory._organizations["legal_aid_society_la"]
        assert resource_directory._is_national_resource(local_org) is False

    @pytest.mark.asyncio
    async def test_all_issue_types_have_fallback_resources(self, resource_directory):
        """Test that all legal issue types have national fallback resources."""
        remote_location = Location(state="WY", county="Teton")
        
        for issue_type in LegalIssueType:
            criteria = SearchCriteria(
                location=remote_location,
                issue_type=issue_type,
                language="en"
            )
            
            organizations = await resource_directory.find_organizations(criteria)
            
            # Should find at least one national resource for each issue type
            assert len(organizations) > 0, f"No fallback resources found for {issue_type.value}"
            
            # All should be national resources
            for org in organizations:
                assert "ALL" in org.service_area.states
                assert issue_type in org.specializations or LegalIssueType.OTHER in org.specializations

    @pytest.mark.asyncio
    async def test_contact_info_validation(self, resource_directory):
        """Test contact information validation logic."""
        # Create a test organization with valid contact info
        from ai_legal_aid.types import ContactInfo, Address, OperatingHours
        
        valid_contact = ContactInfo(
            phone="(555) 123-4567",
            email="test@example.org",
            address=Address(
                street="123 Test St",
                city="Test City",
                state="CA",
                zip_code="90210"
            ),
            website="https://example.org",
            intake_hours=OperatingHours(
                monday={"open": "9:00 AM", "close": "5:00 PM"}
            )
        )
        
        # Create a mock organization for testing
        from ai_legal_aid.types import LegalAidOrganization, GeographicArea
        
        test_org = LegalAidOrganization(
            id="test_org",
            name="Test Organization",
            contact_info=valid_contact,
            specializations=[LegalIssueType.OTHER],
            service_area=GeographicArea(states=["CA"]),
            languages=["en"],
            availability=OperatingHours(
                monday={"open": "9:00 AM", "close": "5:00 PM"}
            ),
            eligibility_requirements=[]
        )
        
        assert resource_directory._validate_contact_info(test_org) is True