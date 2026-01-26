"""
Tests for the Legal Guidance Engine implementation.

This module tests the legal issue classification, guidance generation,
complexity assessment, and citation retrieval functionality.
"""

import pytest

from ai_legal_aid.legal_guidance_engine import BasicLegalGuidanceEngine
from ai_legal_aid.types import (
    LegalIssueType,
    ComplexityLevel,
    UrgencyLevel,
    LegalIssue,
    UserContext,
    Location,
)


@pytest.fixture
def legal_engine():
    """Create a legal guidance engine for testing."""
    return BasicLegalGuidanceEngine()


@pytest.fixture
def sample_user_context():
    """Create a sample user context for testing."""
    return UserContext(
        location=Location(state="CA", county="Los Angeles"),
        preferred_language="en",
        legal_issue_type=LegalIssueType.TENANT_RIGHTS,
        urgency_level=UrgencyLevel.MEDIUM
    )


class TestLegalIssueClassification:
    """Test legal issue classification functionality."""

    @pytest.mark.asyncio
    async def test_classify_land_dispute(self, legal_engine):
        """Test classification of land dispute queries."""
        query = "My neighbor built a fence on my property and I have the deed showing the boundary"
        result = await legal_engine.classify_legal_issue(query)
        assert result == LegalIssueType.LAND_DISPUTE

    @pytest.mark.asyncio
    async def test_classify_domestic_violence(self, legal_engine):
        """Test classification of domestic violence queries."""
        query = "My boyfriend has been threatening me and I need a restraining order"
        result = await legal_engine.classify_legal_issue(query)
        assert result == LegalIssueType.DOMESTIC_VIOLENCE

    @pytest.mark.asyncio
    async def test_classify_wage_theft(self, legal_engine):
        """Test classification of wage theft queries."""
        query = "My employer hasn't paid me overtime for the extra hours I worked last month"
        result = await legal_engine.classify_legal_issue(query)
        assert result == LegalIssueType.WAGE_THEFT

    @pytest.mark.asyncio
    async def test_classify_tenant_rights(self, legal_engine):
        """Test classification of tenant rights queries."""
        query = "My landlord is trying to evict me but hasn't followed proper procedures"
        result = await legal_engine.classify_legal_issue(query)
        assert result == LegalIssueType.TENANT_RIGHTS

    @pytest.mark.asyncio
    async def test_classify_unknown_issue(self, legal_engine):
        """Test classification of unrecognized queries."""
        query = "I have a question about my tax return and deductions"
        result = await legal_engine.classify_legal_issue(query)
        assert result == LegalIssueType.OTHER


class TestGuidanceGeneration:
    """Test legal guidance generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_guidance_land_dispute(self, legal_engine, sample_user_context):
        """Test guidance generation for land disputes."""
        issue = LegalIssue(
            type=LegalIssueType.LAND_DISPUTE,
            description="Property boundary dispute with neighbor",
            urgency=UrgencyLevel.MEDIUM,
            complexity=ComplexityLevel.MODERATE,
            involved_parties=["neighbor"]
        )
        
        guidance = await legal_engine.generate_guidance(issue, sample_user_context)
        
        assert "property" in guidance.summary.lower()
        assert len(guidance.detailed_steps) > 0
        assert guidance.urgency_level == UrgencyLevel.MEDIUM
        assert len(guidance.applicable_laws) > 0
        assert "Property Law" in str(guidance.applicable_laws)

    @pytest.mark.asyncio
    async def test_generate_guidance_domestic_violence(self, legal_engine, sample_user_context):
        """Test guidance generation for domestic violence."""
        issue = LegalIssue(
            type=LegalIssueType.DOMESTIC_VIOLENCE,
            description="Intimate partner violence and threats",
            urgency=UrgencyLevel.EMERGENCY,
            complexity=ComplexityLevel.COMPLEX,
            involved_parties=["partner"]
        )
        
        guidance = await legal_engine.generate_guidance(issue, sample_user_context)
        
        assert "domestic violence" in guidance.summary.lower()
        assert guidance.recommends_professional_help is True
        assert "911" in guidance.detailed_steps[0]
        assert "Violence Against Women Act" in str(guidance.applicable_laws)

    @pytest.mark.asyncio
    async def test_generate_guidance_unknown_issue(self, legal_engine, sample_user_context):
        """Test guidance generation for unknown issues."""
        issue = LegalIssue(
            type=LegalIssueType.OTHER,
            description="Some unknown legal issue",
            urgency=UrgencyLevel.MEDIUM,
            complexity=ComplexityLevel.SIMPLE,
            involved_parties=[]
        )
        
        guidance = await legal_engine.generate_guidance(issue, sample_user_context)
        
        assert "professional consultation" in guidance.summary.lower()
        assert guidance.recommends_professional_help is True
        assert len(guidance.detailed_steps) > 0


class TestComplexityAssessment:
    """Test complexity assessment functionality."""

    @pytest.mark.asyncio
    async def test_assess_simple_complexity(self, legal_engine):
        """Test assessment of simple legal issues."""
        issue = LegalIssue(
            type=LegalIssueType.TENANT_RIGHTS,
            description="I have a question about my lease agreement",
            urgency=UrgencyLevel.LOW,
            complexity=ComplexityLevel.SIMPLE,
            involved_parties=["landlord"]
        )
        
        complexity = await legal_engine.assess_complexity(issue)
        assert complexity == ComplexityLevel.SIMPLE

    @pytest.mark.asyncio
    async def test_assess_moderate_complexity(self, legal_engine):
        """Test assessment of moderate complexity issues."""
        issue = LegalIssue(
            type=LegalIssueType.WAGE_THEFT,
            description="I have a contract dispute with my employer about overtime pay",
            urgency=UrgencyLevel.MEDIUM,
            complexity=ComplexityLevel.MODERATE,
            involved_parties=["employer", "union"]
        )
        
        complexity = await legal_engine.assess_complexity(issue)
        assert complexity == ComplexityLevel.MODERATE

    @pytest.mark.asyncio
    async def test_assess_complex_issue(self, legal_engine):
        """Test assessment of complex legal issues."""
        issue = LegalIssue(
            type=LegalIssueType.LAND_DISPUTE,
            description="I need to file a lawsuit against my neighbor for property damage",
            urgency=UrgencyLevel.HIGH,
            complexity=ComplexityLevel.COMPLEX,
            involved_parties=["neighbor", "insurance_company"]
        )
        
        complexity = await legal_engine.assess_complexity(issue)
        assert complexity == ComplexityLevel.COMPLEX

    @pytest.mark.asyncio
    async def test_assess_domestic_violence_complexity(self, legal_engine):
        """Test that domestic violence cases are assessed as at least moderate complexity."""
        issue = LegalIssue(
            type=LegalIssueType.DOMESTIC_VIOLENCE,
            description="I need help with a simple restraining order",
            urgency=UrgencyLevel.HIGH,
            complexity=ComplexityLevel.SIMPLE,
            involved_parties=["partner"]
        )
        
        complexity = await legal_engine.assess_complexity(issue)
        assert complexity in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX]


class TestLegalCitations:
    """Test legal citation retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_citations_land_dispute(self, legal_engine):
        """Test citation retrieval for land disputes."""
        issue = LegalIssue(
            type=LegalIssueType.LAND_DISPUTE,
            description="Property boundary issue",
            urgency=UrgencyLevel.MEDIUM,
            complexity=ComplexityLevel.MODERATE,
            involved_parties=["neighbor"]
        )
        
        citations = await legal_engine.get_citations(issue)
        
        assert len(citations) > 0
        assert any("Property Law" in citation.title for citation in citations)
        assert any("Zoning" in citation.title for citation in citations)

    @pytest.mark.asyncio
    async def test_get_citations_domestic_violence(self, legal_engine):
        """Test citation retrieval for domestic violence."""
        issue = LegalIssue(
            type=LegalIssueType.DOMESTIC_VIOLENCE,
            description="Need protection order",
            urgency=UrgencyLevel.EMERGENCY,
            complexity=ComplexityLevel.COMPLEX,
            involved_parties=["partner"]
        )
        
        citations = await legal_engine.get_citations(issue)
        
        assert len(citations) > 0
        assert any("Violence Against Women Act" in citation.title for citation in citations)
        assert any(citation.jurisdiction == "Federal" for citation in citations)

    @pytest.mark.asyncio
    async def test_get_citations_wage_theft(self, legal_engine):
        """Test citation retrieval for wage theft."""
        issue = LegalIssue(
            type=LegalIssueType.WAGE_THEFT,
            description="Unpaid overtime wages",
            urgency=UrgencyLevel.MEDIUM,
            complexity=ComplexityLevel.MODERATE,
            involved_parties=["employer"]
        )
        
        citations = await legal_engine.get_citations(issue)
        
        assert len(citations) > 0
        assert any("Fair Labor Standards Act" in citation.title for citation in citations)
        assert any("FLSA" in citation.title for citation in citations)

    @pytest.mark.asyncio
    async def test_get_citations_tenant_rights(self, legal_engine):
        """Test citation retrieval for tenant rights."""
        issue = LegalIssue(
            type=LegalIssueType.TENANT_RIGHTS,
            description="Landlord not making repairs",
            urgency=UrgencyLevel.MEDIUM,
            complexity=ComplexityLevel.SIMPLE,
            involved_parties=["landlord"]
        )
        
        citations = await legal_engine.get_citations(issue)
        
        assert len(citations) > 0
        assert any("Landlord-Tenant" in citation.title for citation in citations)
        assert any("Fair Housing Act" in citation.title for citation in citations)


class TestEnhancedComplexityAndReferral:
    """Test enhanced complexity assessment and referral logic."""

    @pytest.mark.asyncio
    async def test_professional_help_recommendation_complex_case(self, legal_engine, sample_user_context):
        """Test that complex cases recommend professional help."""
        issue = LegalIssue(
            type=LegalIssueType.LAND_DISPUTE,
            description="I need to file a lawsuit against my neighbor for property damage and trespassing",
            urgency=UrgencyLevel.HIGH,
            complexity=ComplexityLevel.COMPLEX,
            involved_parties=["neighbor", "insurance_company"],
            documents=["contract", "court_document", "identification"]
        )
        
        guidance = await legal_engine.generate_guidance(issue, sample_user_context)
        assert guidance.recommends_professional_help is True
        assert "professional legal representation is strongly recommended" in " ".join(guidance.detailed_steps)

    @pytest.mark.asyncio
    async def test_emergency_urgency_handling(self, legal_engine, sample_user_context):
        """Test that emergency cases get appropriate urgent guidance."""
        issue = LegalIssue(
            type=LegalIssueType.DOMESTIC_VIOLENCE,
            description="I am in immediate danger from my partner",
            urgency=UrgencyLevel.EMERGENCY,
            complexity=ComplexityLevel.COMPLEX,
            involved_parties=["partner"]
        )
        
        guidance = await legal_engine.generate_guidance(issue, sample_user_context)
        assert guidance.recommends_professional_help is True
        assert "URGENT" in guidance.detailed_steps[0]
        assert "911" in guidance.detailed_steps[0]

    @pytest.mark.asyncio
    async def test_create_legal_issue_from_query(self, legal_engine):
        """Test creating a complete legal issue from a user query."""
        query = "My landlord is trying to evict me tomorrow and I have a lease agreement"
        
        issue = await legal_engine.create_legal_issue_from_query(query)
        
        assert issue.type == LegalIssueType.TENANT_RIGHTS
        assert issue.urgency == UrgencyLevel.HIGH  # "tomorrow" should trigger high urgency
        assert "landlord" in issue.involved_parties
        assert "lease" in issue.documents
        assert issue.complexity in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX]

    @pytest.mark.asyncio
    async def test_enhanced_complexity_scoring(self, legal_engine):
        """Test the enhanced complexity scoring system."""
        # High complexity case
        complex_issue = LegalIssue(
            type=LegalIssueType.DOMESTIC_VIOLENCE,
            description="This is a very long and detailed description of a complex domestic violence situation involving multiple incidents over several years with police reports and court documents and multiple family members and witnesses and ongoing threats and harassment",
            urgency=UrgencyLevel.EMERGENCY,
            complexity=ComplexityLevel.SIMPLE,  # Will be reassessed
            involved_parties=["partner", "police", "family", "court"],
            documents=["court_document", "employment_record", "identification", "contract"],
            timeframe="ongoing for years"
        )
        
        complexity = await legal_engine.assess_complexity(complex_issue)
        assert complexity == ComplexityLevel.COMPLEX

    def test_extract_involved_parties(self, legal_engine):
        """Test extraction of involved parties from description."""
        description = "My landlord and the property manager are harassing me and my employer is also involved"
        parties = legal_engine._extract_involved_parties(description)
        
        assert "landlord" in parties
        assert "employer" in parties

    def test_extract_timeframe(self, legal_engine):
        """Test extraction of timeframe from description."""
        description = "This happened last month and is still ongoing"
        timeframe = legal_engine._extract_timeframe(description)
        
        assert timeframe is not None
        assert "last month" in timeframe or "ongoing" in timeframe

    def test_extract_document_types(self, legal_engine):
        """Test extraction of document types from description."""
        description = "I have my lease agreement and pay stubs as evidence"
        documents = legal_engine._extract_document_types(description)
        
        assert "lease" in documents
        assert "employment_record" in documents


class TestUrgencyAssessment:
    """Test urgency assessment functionality."""

    def test_assess_emergency_urgency(self, legal_engine):
        """Test assessment of emergency urgency."""
        description = "I am in immediate danger and need help right now"
        urgency = legal_engine._assess_urgency_from_description(description)
        assert urgency == UrgencyLevel.EMERGENCY

    def test_assess_high_urgency(self, legal_engine):
        """Test assessment of high urgency."""
        description = "I have a court date next week and need help quickly"
        urgency = legal_engine._assess_urgency_from_description(description)
        assert urgency == UrgencyLevel.HIGH

    def test_assess_medium_urgency(self, legal_engine):
        """Test assessment of medium urgency."""
        description = "I have a general question about my lease and need advice soon"
        urgency = legal_engine._assess_urgency_from_description(description)
        assert urgency == UrgencyLevel.MEDIUM

    def test_assess_low_urgency(self, legal_engine):
        """Test assessment of low urgency."""
        description = "I have a general question about property law"
        urgency = legal_engine._assess_urgency_from_description(description)
        assert urgency == UrgencyLevel.LOW