"""
Tests for the Disclaimer Service implementation.

This module tests the disclaimer management, compliance tracking,
and context-aware disclaimer delivery functionality.
"""

import pytest
from datetime import datetime

from ai_legal_aid.disclaimer_service import BasicDisclaimerService
from ai_legal_aid.types import (
    SessionId,
    LegalIssueType,
    UrgencyLevel,
    ConversationContext,
    Session,
    UserContext,
    Location,
)


@pytest.fixture
def disclaimer_service():
    """Create a disclaimer service for testing."""
    return BasicDisclaimerService()


@pytest.fixture
def sample_session():
    """Create a sample session for testing."""
    return Session(
        id=SessionId("test_session_123"),
        start_time=datetime.now(),
        last_activity=datetime.now(),
        language="en",
        conversation_history=[],
        user_context=UserContext(
            location=Location(state="CA", county="Los Angeles"),
            preferred_language="en",
            legal_issue_type=LegalIssueType.TENANT_RIGHTS,
            urgency_level=UrgencyLevel.MEDIUM
        ),
        disclaimer_acknowledged=False
    )


@pytest.fixture
def sample_conversation_context(sample_session):
    """Create a sample conversation context for testing."""
    return ConversationContext(
        session=sample_session,
        current_turn=1,
        last_user_input="I have a question about my lease",
        pending_questions=[],
        conversation_length=1
    )


class TestDisclaimerService:
    """Test basic disclaimer service functionality."""

    @pytest.mark.asyncio
    async def test_get_initial_disclaimer_english(self, disclaimer_service):
        """Test getting initial disclaimer in English."""
        disclaimer = await disclaimer_service.get_initial_disclaimer("en")
        
        assert "IMPORTANT LEGAL DISCLAIMER" in disclaimer
        assert "NOT a substitute for professional legal advice" in disclaimer
        assert "attorney-client relationship" in disclaimer

    @pytest.mark.asyncio
    async def test_get_initial_disclaimer_spanish(self, disclaimer_service):
        """Test getting initial disclaimer in Spanish."""
        disclaimer = await disclaimer_service.get_initial_disclaimer("es")
        
        assert "AVISO LEGAL IMPORTANTE" in disclaimer
        assert "NO es un sustituto del consejo legal profesional" in disclaimer
        assert "abogado-cliente" in disclaimer

    @pytest.mark.asyncio
    async def test_get_contextual_disclaimer_domestic_violence(self, disclaimer_service):
        """Test getting contextual disclaimer for domestic violence."""
        disclaimer = await disclaimer_service.get_contextual_disclaimer(
            LegalIssueType.DOMESTIC_VIOLENCE, "en"
        )
        
        assert "DOMESTIC VIOLENCE SAFETY DISCLAIMER" in disclaimer
        assert "call 911" in disclaimer
        assert "National Domestic Violence Hotline" in disclaimer

    @pytest.mark.asyncio
    async def test_get_contextual_disclaimer_tenant_rights(self, disclaimer_service):
        """Test getting contextual disclaimer for tenant rights."""
        disclaimer = await disclaimer_service.get_contextual_disclaimer(
            LegalIssueType.TENANT_RIGHTS, "en"
        )
        
        assert "HOUSING LAW DISCLAIMER" in disclaimer
        assert "vary significantly by state" in disclaimer
        assert "tenant rights attorney" in disclaimer

    @pytest.mark.asyncio
    async def test_get_contextual_disclaimer_wage_theft(self, disclaimer_service):
        """Test getting contextual disclaimer for wage theft."""
        disclaimer = await disclaimer_service.get_contextual_disclaimer(
            LegalIssueType.WAGE_THEFT, "en"
        )
        
        assert "EMPLOYMENT LAW DISCLAIMER" in disclaimer
        assert "filing deadlines" in disclaimer
        assert "Department of Labor" in disclaimer

    @pytest.mark.asyncio
    async def test_get_contextual_disclaimer_land_dispute(self, disclaimer_service):
        """Test getting contextual disclaimer for land disputes."""
        disclaimer = await disclaimer_service.get_contextual_disclaimer(
            LegalIssueType.LAND_DISPUTE, "en"
        )
        
        assert "PROPERTY LAW DISCLAIMER" in disclaimer
        assert "professional surveying" in disclaimer
        assert "real estate attorney" in disclaimer

    @pytest.mark.asyncio
    async def test_get_contextual_disclaimer_unknown_type(self, disclaimer_service):
        """Test getting contextual disclaimer for unknown issue type."""
        disclaimer = await disclaimer_service.get_contextual_disclaimer(
            LegalIssueType.OTHER, "en"
        )
        
        assert "educational purposes only" in disclaimer
        assert "qualified attorney" in disclaimer

    @pytest.mark.asyncio
    async def test_record_disclaimer_acknowledgment(self, disclaimer_service):
        """Test recording disclaimer acknowledgment."""
        session_id = SessionId("test_session")
        disclaimer_type = "initial"
        
        await disclaimer_service.record_disclaimer_acknowledgment(session_id, disclaimer_type)
        
        # Check that acknowledgment was recorded
        status = disclaimer_service.get_disclaimer_acknowledgment_status(session_id)
        assert status["initial"] is True

    @pytest.mark.asyncio
    async def test_multiple_disclaimer_acknowledgments(self, disclaimer_service):
        """Test recording multiple disclaimer acknowledgments."""
        session_id = SessionId("test_session")
        
        await disclaimer_service.record_disclaimer_acknowledgment(session_id, "initial")
        await disclaimer_service.record_disclaimer_acknowledgment(session_id, "contextual_domestic_violence")
        
        status = disclaimer_service.get_disclaimer_acknowledgment_status(session_id)
        assert status["initial"] is True
        assert status["contextual_domestic_violence"] is True
        assert status["contextual_tenant_rights"] is False


class TestDisclaimerLogic:
    """Test disclaimer display logic."""

    def test_should_show_disclaimer_initial_not_acknowledged(self, disclaimer_service, sample_conversation_context):
        """Test that initial disclaimer is shown when not acknowledged."""
        should_show = disclaimer_service.should_show_disclaimer(sample_conversation_context)
        assert should_show is True

    @pytest.mark.asyncio
    async def test_should_show_disclaimer_initial_acknowledged(self, disclaimer_service, sample_conversation_context):
        """Test disclaimer logic after initial acknowledgment."""
        session_id = sample_conversation_context.session.id
        
        # Acknowledge initial disclaimer
        await disclaimer_service.record_disclaimer_acknowledgment(session_id, "initial")
        
        should_show = disclaimer_service.should_show_disclaimer(sample_conversation_context)
        # Should still show contextual disclaimer for tenant rights
        assert should_show is True

    @pytest.mark.asyncio
    async def test_should_show_disclaimer_contextual_new_issue(self, disclaimer_service, sample_conversation_context):
        """Test that contextual disclaimer is shown for new issue types."""
        session_id = sample_conversation_context.session.id
        
        # Acknowledge initial disclaimer
        await disclaimer_service.record_disclaimer_acknowledgment(session_id, "initial")
        
        # Change issue type to domestic violence
        sample_conversation_context.session.user_context.legal_issue_type = LegalIssueType.DOMESTIC_VIOLENCE
        
        should_show = disclaimer_service.should_show_disclaimer(sample_conversation_context)
        assert should_show is True

    def test_should_show_disclaimer_periodic_reminder(self, disclaimer_service, sample_conversation_context):
        """Test that disclaimer is shown periodically."""
        # Set conversation length to trigger periodic reminder
        sample_conversation_context.conversation_length = 5
        
        should_show = disclaimer_service.should_show_disclaimer(sample_conversation_context)
        assert should_show is True

    def test_should_show_disclaimer_high_risk_keywords(self, disclaimer_service, sample_conversation_context):
        """Test that disclaimer is shown for high-risk keywords."""
        sample_conversation_context.last_user_input = "I want to sue my landlord"
        
        should_show = disclaimer_service.should_show_disclaimer(sample_conversation_context)
        assert should_show is True

    def test_should_show_disclaimer_high_urgency(self, disclaimer_service, sample_conversation_context):
        """Test that disclaimer is shown for high urgency situations."""
        sample_conversation_context.session.user_context.urgency_level = UrgencyLevel.EMERGENCY
        
        should_show = disclaimer_service.should_show_disclaimer(sample_conversation_context)
        assert should_show is True

    def test_should_show_disclaimer_domestic_violence_always(self, disclaimer_service, sample_conversation_context):
        """Test that disclaimer is always shown for domestic violence cases."""
        sample_conversation_context.session.user_context.legal_issue_type = LegalIssueType.DOMESTIC_VIOLENCE
        
        should_show = disclaimer_service.should_show_disclaimer(sample_conversation_context)
        assert should_show is True


class TestAuditAndCompliance:
    """Test audit and compliance functionality."""

    @pytest.mark.asyncio
    async def test_audit_record_creation(self, disclaimer_service):
        """Test that audit records are created for disclaimer acknowledgments."""
        session_id = SessionId("test_session")
        disclaimer_type = "initial"
        
        await disclaimer_service.record_disclaimer_acknowledgment(session_id, disclaimer_type)
        
        audit_records = disclaimer_service.get_audit_records(session_id)
        assert len(audit_records) == 1
        
        record = audit_records[0]
        assert record.session_id == session_id
        assert record.action == "disclaimer_acknowledged"
        assert record.details["disclaimer_type"] == disclaimer_type
        assert "disclaimer_compliance" in record.compliance_flags

    @pytest.mark.asyncio
    async def test_get_audit_records_all_sessions(self, disclaimer_service):
        """Test getting audit records for all sessions."""
        session1 = SessionId("session1")
        session2 = SessionId("session2")
        
        await disclaimer_service.record_disclaimer_acknowledgment(session1, "initial")
        await disclaimer_service.record_disclaimer_acknowledgment(session2, "initial")
        
        all_records = disclaimer_service.get_audit_records()
        assert len(all_records) == 2
        
        session1_records = disclaimer_service.get_audit_records(session1)
        assert len(session1_records) == 1
        assert session1_records[0].session_id == session1

    def test_clear_session_data(self, disclaimer_service):
        """Test clearing session data."""
        session_id = SessionId("test_session")
        
        # Add some acknowledgments
        disclaimer_service._disclaimer_acknowledgments[session_id] = {"initial", "contextual_tenant_rights"}
        
        # Clear session data
        disclaimer_service.clear_session_data(session_id)
        
        # Check that data was cleared
        status = disclaimer_service.get_disclaimer_acknowledgment_status(session_id)
        assert not any(status.values())


class TestLegalAdviceBoundaries:
    """Test legal advice boundary enforcement."""

    @pytest.mark.asyncio
    async def test_get_legal_advice_boundary_message_english(self, disclaimer_service):
        """Test getting legal advice boundary message in English."""
        message = await disclaimer_service.get_legal_advice_boundary_message("en")
        
        assert "cannot provide specific legal advice" in message
        assert "What I CAN do:" in message
        assert "What I CANNOT do:" in message
        assert "licensed attorney" in message

    @pytest.mark.asyncio
    async def test_get_legal_advice_boundary_message_spanish(self, disclaimer_service):
        """Test getting legal advice boundary message in Spanish."""
        message = await disclaimer_service.get_legal_advice_boundary_message("es")
        
        assert "No puedo proporcionar consejo legal específico" in message
        assert "Lo que SÍ puedo hacer:" in message
        assert "Lo que NO puedo hacer:" in message
        assert "abogado licenciado" in message


class TestLanguageSupport:
    """Test multi-language support."""

    @pytest.mark.asyncio
    async def test_all_disclaimers_support_spanish(self, disclaimer_service):
        """Test that all disclaimer types support Spanish."""
        issue_types = [
            LegalIssueType.DOMESTIC_VIOLENCE,
            LegalIssueType.TENANT_RIGHTS,
            LegalIssueType.WAGE_THEFT,
            LegalIssueType.LAND_DISPUTE,
            LegalIssueType.OTHER
        ]
        
        for issue_type in issue_types:
            disclaimer = await disclaimer_service.get_contextual_disclaimer(issue_type, "es")
            assert len(disclaimer) > 0
            # Should contain Spanish text (basic check)
            assert any(word in disclaimer.lower() for word in ["legal", "abogado", "consulte", "información"])

    @pytest.mark.asyncio
    async def test_fallback_to_english_for_unsupported_language(self, disclaimer_service):
        """Test fallback to English for unsupported languages."""
        disclaimer_en = await disclaimer_service.get_initial_disclaimer("en")
        disclaimer_unsupported = await disclaimer_service.get_initial_disclaimer("fr")  # French not supported
        
        assert disclaimer_en == disclaimer_unsupported