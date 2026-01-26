"""
Tests for the Conversation Engine implementation.

This module tests the conversation orchestration, dialogue state tracking,
and integration of all system components.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from ai_legal_aid.conversation_engine import BasicConversationEngine
from ai_legal_aid.legal_guidance_engine import BasicLegalGuidanceEngine
from ai_legal_aid.resource_directory import BasicResourceDirectory
from ai_legal_aid.disclaimer_service import BasicDisclaimerService
from ai_legal_aid.session_manager import InMemorySessionManager
from ai_legal_aid.types import (
    SessionId,
    LegalIssueType,
    UrgencyLevel,
    Session,
    UserContext,
    Location,
    ConversationContext,
)


@pytest.fixture
def session_manager():
    """Create a session manager for testing."""
    return InMemorySessionManager()


@pytest.fixture
def legal_guidance_engine():
    """Create a legal guidance engine for testing."""
    return BasicLegalGuidanceEngine()


@pytest.fixture
def resource_directory():
    """Create a resource directory for testing."""
    return BasicResourceDirectory()


@pytest.fixture
def disclaimer_service():
    """Create a disclaimer service for testing."""
    return BasicDisclaimerService()


@pytest.fixture
def conversation_engine(session_manager, legal_guidance_engine, resource_directory, disclaimer_service):
    """Create a conversation engine for testing."""
    return BasicConversationEngine(
        session_manager, legal_guidance_engine, resource_directory, disclaimer_service
    )


@pytest.fixture
async def sample_session(session_manager):
    """Create a sample session for testing."""
    session_id = await session_manager.create_session()
    session = await session_manager.get_session(session_id)
    
    # Update with sample user context
    await session_manager.update_session(session_id, {
        "user_context": {
            "location": {"state": "CA", "county": "Los Angeles"},
            "preferred_language": "en",
            "legal_issue_type": None,
            "urgency_level": None
        }
    })
    
    return session_id


class TestConversationEngine:
    """Test basic conversation engine functionality."""

    @pytest.mark.asyncio
    async def test_process_user_input_initial_disclaimer(self, conversation_engine, sample_session):
        """Test that initial disclaimer is shown for new users."""
        response = await conversation_engine.process_user_input(
            sample_session, "I have a legal question"
        )
        
        assert response.requires_disclaimer is True
        assert "IMPORTANT LEGAL DISCLAIMER" in response.text
        assert len(response.follow_up_questions) > 0

    @pytest.mark.asyncio
    async def test_process_user_input_disclaimer_acknowledgment(self, conversation_engine, sample_session):
        """Test handling of disclaimer acknowledgment."""
        # First, trigger disclaimer
        await conversation_engine.process_user_input(sample_session, "I have a legal question")
        
        # Then acknowledge it
        response = await conversation_engine.process_user_input(sample_session, "Yes, I understand")
        
        assert response.requires_disclaimer is False
        assert "Thank you for acknowledging" in response.text
        assert len(response.follow_up_questions) > 0

    @pytest.mark.asyncio
    async def test_process_legal_query_tenant_rights(self, conversation_engine, sample_session, disclaimer_service):
        """Test processing a tenant rights legal query."""
        # Acknowledge disclaimer first
        await disclaimer_service.record_disclaimer_acknowledgment(sample_session, "initial")
        
        response = await conversation_engine.process_user_input(
            sample_session, "My landlord is trying to evict me without proper notice"
        )
        
        assert response.requires_disclaimer is False
        assert len(response.text) > 0
        assert len(response.suggested_actions) > 0
        # Should include resource referrals for tenant rights
        assert len(response.resources) > 0

    @pytest.mark.asyncio
    async def test_process_legal_query_domestic_violence(self, conversation_engine, sample_session, disclaimer_service):
        """Test processing a domestic violence legal query."""
        # Acknowledge disclaimer first
        await disclaimer_service.record_disclaimer_acknowledgment(sample_session, "initial")
        
        response = await conversation_engine.process_user_input(
            sample_session, "My partner has been threatening me and I need help"
        )
        
        assert response.requires_disclaimer is False
        assert len(response.resources) > 0
        # Should recommend professional help for DV cases
        assert any("professional" in action.description.lower() or 
                 "contact" in action.description.lower() 
                 for action in response.suggested_actions)

    @pytest.mark.asyncio
    async def test_generate_follow_up_questions_tenant_rights(self, conversation_engine, sample_session):
        """Test follow-up question generation for tenant rights."""
        session = await conversation_engine.session_manager.get_session(sample_session)
        session.user_context.legal_issue_type = LegalIssueType.TENANT_RIGHTS
        
        context = ConversationContext(
            session=session,
            current_turn=1,
            last_user_input="I have a landlord problem",
            pending_questions=[],
            conversation_length=1
        )
        
        questions = await conversation_engine.generate_follow_up_questions(context)
        
        assert len(questions) > 0
        assert len(questions) <= 3
        assert any("landlord" in q.lower() or "lease" in q.lower() for q in questions)

    @pytest.mark.asyncio
    async def test_generate_follow_up_questions_domestic_violence(self, conversation_engine, sample_session):
        """Test follow-up question generation for domestic violence."""
        session = await conversation_engine.session_manager.get_session(sample_session)
        session.user_context.legal_issue_type = LegalIssueType.DOMESTIC_VIOLENCE
        
        context = ConversationContext(
            session=session,
            current_turn=1,
            last_user_input="I need help with domestic violence",
            pending_questions=[],
            conversation_length=1
        )
        
        questions = await conversation_engine.generate_follow_up_questions(context)
        
        assert len(questions) > 0
        assert any("safe" in q.lower() for q in questions)

    @pytest.mark.asyncio
    async def test_summarize_conversation(self, conversation_engine, sample_session, disclaimer_service):
        """Test conversation summarization."""
        # Acknowledge disclaimer and have a conversation
        await disclaimer_service.record_disclaimer_acknowledgment(sample_session, "initial")
        
        await conversation_engine.process_user_input(
            sample_session, "I have a tenant rights issue"
        )
        await conversation_engine.process_user_input(
            sample_session, "My landlord won't fix the heating"
        )
        
        summary = await conversation_engine.summarize_conversation(sample_session)
        
        assert summary.session_id == sample_session
        assert summary.duration >= 0
        assert len(summary.issues_discussed) > 0
        assert LegalIssueType.TENANT_RIGHTS in summary.issues_discussed

    def test_should_end_conversation_long_conversation(self, conversation_engine):
        """Test conversation ending for long conversations."""
        session = Session(
            id=SessionId("test"),
            start_time=datetime.now(),
            last_activity=datetime.now(),
            language="en",
            conversation_history=[],
            user_context=UserContext()
        )
        
        context = ConversationContext(
            session=session,
            current_turn=25,  # Very long conversation
            last_user_input="More questions",
            pending_questions=[],
            conversation_length=25
        )
        
        should_end = conversation_engine.should_end_conversation(context)
        assert should_end is True

    def test_should_end_conversation_goodbye(self, conversation_engine):
        """Test conversation ending when user says goodbye."""
        session = Session(
            id=SessionId("test"),
            start_time=datetime.now(),
            last_activity=datetime.now(),
            language="en",
            conversation_history=[],
            user_context=UserContext()
        )
        
        context = ConversationContext(
            session=session,
            current_turn=3,
            last_user_input="Thank you, that's all I needed",
            pending_questions=[],
            conversation_length=3
        )
        
        should_end = conversation_engine.should_end_conversation(context)
        assert should_end is True

    def test_should_end_conversation_continue(self, conversation_engine):
        """Test conversation continuing for normal interactions."""
        session = Session(
            id=SessionId("test"),
            start_time=datetime.now(),
            last_activity=datetime.now(),
            language="en",
            conversation_history=[],
            user_context=UserContext()
        )
        
        context = ConversationContext(
            session=session,
            current_turn=3,
            last_user_input="I have another question",
            pending_questions=[],
            conversation_length=3
        )
        
        should_end = conversation_engine.should_end_conversation(context)
        assert should_end is False


class TestDisclaimerIntegration:
    """Test disclaimer integration in conversation flow."""

    @pytest.mark.asyncio
    async def test_contextual_disclaimer_for_domestic_violence(self, conversation_engine, sample_session, disclaimer_service):
        """Test that contextual disclaimer is shown for domestic violence cases."""
        # Acknowledge initial disclaimer
        await disclaimer_service.record_disclaimer_acknowledgment(sample_session, "initial")
        
        # Update session with domestic violence issue
        await conversation_engine.session_manager.update_session(sample_session, {
            "user_context": {
                "location": {"state": "CA", "county": "Los Angeles"},
                "preferred_language": "en",
                "legal_issue_type": LegalIssueType.DOMESTIC_VIOLENCE.value,
                "urgency_level": UrgencyLevel.HIGH.value
            }
        })
        
        response = await conversation_engine.process_user_input(
            sample_session, "I need help with domestic violence"
        )
        
        # Should show contextual disclaimer for DV
        assert response.requires_disclaimer is True
        assert "DOMESTIC VIOLENCE SAFETY DISCLAIMER" in response.text

    def test_is_disclaimer_acknowledgment_english(self, conversation_engine):
        """Test disclaimer acknowledgment detection in English."""
        assert conversation_engine._is_disclaimer_acknowledgment("Yes, I understand") is True
        assert conversation_engine._is_disclaimer_acknowledgment("I acknowledge") is True
        assert conversation_engine._is_disclaimer_acknowledgment("No, I don't agree") is False

    def test_is_disclaimer_acknowledgment_spanish(self, conversation_engine):
        """Test disclaimer acknowledgment detection in Spanish."""
        assert conversation_engine._is_disclaimer_acknowledgment("Sí, entiendo") is True
        assert conversation_engine._is_disclaimer_acknowledgment("Reconozco") is True
        assert conversation_engine._is_disclaimer_acknowledgment("No estoy de acuerdo") is False


class TestResourceIntegration:
    """Test resource directory integration."""

    @pytest.mark.asyncio
    async def test_resource_referrals_included(self, conversation_engine, sample_session, disclaimer_service):
        """Test that resource referrals are included when professional help is recommended."""
        # Acknowledge disclaimer first
        await disclaimer_service.record_disclaimer_acknowledgment(sample_session, "initial")
        
        response = await conversation_engine.process_user_input(
            sample_session, "I need to sue my landlord for not returning my deposit"
        )
        
        assert len(response.resources) > 0
        assert response.resources[0].organization.name is not None
        assert response.resources[0].organization.contact_info.phone is not None

    @pytest.mark.asyncio
    async def test_emergency_resources_prioritized(self, conversation_engine, sample_session, disclaimer_service):
        """Test that emergency resources are prioritized for urgent cases."""
        # Acknowledge disclaimer first
        await disclaimer_service.record_disclaimer_acknowledgment(sample_session, "initial")
        
        response = await conversation_engine.process_user_input(
            sample_session, "I am in immediate danger from my partner"
        )
        
        assert len(response.resources) > 0
        # Should include domestic violence resources
        dv_resources = [r for r in response.resources 
                       if LegalIssueType.DOMESTIC_VIOLENCE in r.organization.specializations]
        assert len(dv_resources) > 0


class TestLanguageSupport:
    """Test multi-language support in conversation engine."""

    @pytest.mark.asyncio
    async def test_spanish_disclaimer_acknowledgment_response(self, conversation_engine, sample_session):
        """Test Spanish response for disclaimer acknowledgment."""
        # Set session language to Spanish
        await conversation_engine.session_manager.update_session(sample_session, {"language": "es"})
        
        # Trigger disclaimer first
        await conversation_engine.process_user_input(sample_session, "Tengo una pregunta legal")
        
        # Acknowledge in Spanish
        response = await conversation_engine.process_user_input(sample_session, "Sí, entiendo")
        
        assert "Gracias por reconocer" in response.text

    @pytest.mark.asyncio
    async def test_spanish_follow_up_questions(self, conversation_engine, sample_session):
        """Test that follow-up questions are translated to Spanish."""
        # Set session language to Spanish
        session = await conversation_engine.session_manager.get_session(sample_session)
        session.language = "es"
        session.user_context.legal_issue_type = LegalIssueType.TENANT_RIGHTS
        
        context = ConversationContext(
            session=session,
            current_turn=1,
            last_user_input="Tengo un problema con mi arrendador",
            pending_questions=[],
            conversation_length=1
        )
        
        questions = await conversation_engine.generate_follow_up_questions(context)
        
        assert len(questions) > 0
        # Should contain Spanish text
        assert any("arrendador" in q.lower() or "contrato" in q.lower() for q in questions)


class TestResponseBuilding:
    """Test response text building functionality."""

    def test_build_response_text_english(self, conversation_engine, legal_guidance_engine):
        """Test building response text in English."""
        from ai_legal_aid.types import LegalGuidance, UrgencyLevel
        
        guidance = LegalGuidance(
            summary="This is a tenant rights issue.",
            detailed_steps=["Step 1", "Step 2", "Step 3"],
            urgency_level=UrgencyLevel.MEDIUM,
            recommends_professional_help=True,
            applicable_laws=["Tenant Protection Act"]
        )
        
        response_text = conversation_engine._build_response_text(guidance, [], "en")
        
        assert "This is a tenant rights issue." in response_text
        assert "Recommended steps:" in response_text
        assert "1. Step 1" in response_text
        assert "qualified attorney" in response_text

    def test_build_response_text_spanish(self, conversation_engine, legal_guidance_engine):
        """Test building response text in Spanish."""
        from ai_legal_aid.types import LegalGuidance, UrgencyLevel
        
        guidance = LegalGuidance(
            summary="Este es un problema de derechos de inquilinos.",
            detailed_steps=["Paso 1", "Paso 2", "Paso 3"],
            urgency_level=UrgencyLevel.MEDIUM,
            recommends_professional_help=True,
            applicable_laws=["Ley de Protección de Inquilinos"]
        )
        
        response_text = conversation_engine._build_response_text(guidance, [], "es")
        
        assert "Este es un problema de derechos de inquilinos." in response_text
        assert "Pasos recomendados:" in response_text
        assert "1. Paso 1" in response_text
        assert "abogado calificado" in response_text