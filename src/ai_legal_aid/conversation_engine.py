"""
Conversation Engine implementation for the AI Legal Aid System.

This module provides the core conversation orchestration functionality,
managing dialogue state, integrating all system components, and
coordinating the flow of legal guidance conversations.
"""

from datetime import datetime
from typing import List, Optional

from ai_legal_aid.interfaces.legal import ConversationEngine
from ai_legal_aid.interfaces.session import SessionManager
from ai_legal_aid.interfaces.resources import ResourceDirectory
from ai_legal_aid.interfaces.compliance import DisclaimerService
from ai_legal_aid.legal_guidance_engine import BasicLegalGuidanceEngine
from ai_legal_aid.types import (
    SessionId,
    SystemResponse,
    ConversationContext,
    ConversationSummary,
    ConversationTurn,
    Action,
    LegalIssue,
    UrgencyLevel,
    LegalIssueType,
    SearchCriteria,
    ContactMethod,
)


class BasicConversationEngine:
    """
    Basic implementation of the Conversation Engine.
    
    This implementation orchestrates conversations by integrating
    legal guidance, resource referrals, disclaimer management,
    and session state tracking.
    """

    def __init__(
        self,
        session_manager: SessionManager,
        legal_guidance_engine: BasicLegalGuidanceEngine,
        resource_directory: ResourceDirectory,
        disclaimer_service: DisclaimerService
    ):
        """Initialize the conversation engine with required components."""
        self.session_manager = session_manager
        self.legal_guidance_engine = legal_guidance_engine
        self.resource_directory = resource_directory
        self.disclaimer_service = disclaimer_service

    async def process_user_input(
        self, session_id: SessionId, input_text: str
    ) -> SystemResponse:
        """
        Process user input and generate appropriate system response.
        
        This is the main orchestration method that coordinates all system components.
        """
        # Get current session
        session = await self.session_manager.get_session(session_id)
        
        # Create conversation context
        context = ConversationContext(
            session=session,
            current_turn=len(session.conversation_history) + 1,
            last_user_input=input_text,
            pending_questions=[],
            conversation_length=len(session.conversation_history)
        )

        # Check if user is acknowledging a disclaimer
        if self._is_disclaimer_acknowledgment(input_text) and self.disclaimer_service.should_show_disclaimer(context):
            return await self._handle_disclaimer_acknowledgment(session_id, input_text, context)

        # Check if we need to show disclaimers first
        if self.disclaimer_service.should_show_disclaimer(context):
            return await self._handle_disclaimer_flow(session_id, input_text, context)

        # Process the legal query
        return await self._process_legal_query(session_id, input_text, context)

    async def _handle_disclaimer_flow(
        self, session_id: SessionId, input_text: str, context: ConversationContext
    ) -> SystemResponse:
        """Handle disclaimer presentation flow."""
        
        # Determine which disclaimer to show
        if not self.disclaimer_service._has_acknowledged_disclaimer(session_id, "initial"):
            disclaimer_text = await self.disclaimer_service.get_initial_disclaimer(
                context.session.language
            )
            disclaimer_type = "initial"
        elif self.disclaimer_service._is_high_risk_situation(context) and not self.disclaimer_service._has_acknowledged_disclaimer(session_id, "high_risk"):
            # High-risk situation disclaimer
            disclaimer_text = await self.disclaimer_service.get_contextual_disclaimer(
                LegalIssueType.OTHER, context.session.language
            )
            disclaimer_type = "high_risk"
        elif context.session.user_context.legal_issue_type:
            issue_type = context.session.user_context.legal_issue_type
            disclaimer_text = await self.disclaimer_service.get_contextual_disclaimer(
                issue_type, context.session.language
            )
            disclaimer_type = f"contextual_{issue_type.value}"
        else:
            # Periodic reminder
            disclaimer_text = await self.disclaimer_service.get_contextual_disclaimer(
                LegalIssueType.OTHER, context.session.language
            )
            disclaimer_type = "reminder"

        # Create response with disclaimer
        response = SystemResponse(
            text=disclaimer_text,
            requires_disclaimer=True,
            suggested_actions=[
                Action(
                    type="acknowledge_disclaimer",
                    description="Acknowledge that you understand the disclaimer",
                    parameters={"disclaimer_type": disclaimer_type}
                )
            ],
            resources=[],
            follow_up_questions=["Do you understand and acknowledge this disclaimer?"]
        )

        # Record the conversation turn
        await self._record_conversation_turn(session_id, input_text, response, 1.0, True)

        return response

    async def _handle_disclaimer_acknowledgment(
        self, session_id: SessionId, input_text: str, context: ConversationContext
    ) -> SystemResponse:
        """Handle user acknowledgment of disclaimers."""
        
        # Determine disclaimer type being acknowledged
        if not self.disclaimer_service._has_acknowledged_disclaimer(session_id, "initial"):
            disclaimer_type = "initial"
        elif context.session.user_context.legal_issue_type:
            issue_type = context.session.user_context.legal_issue_type
            disclaimer_type = f"contextual_{issue_type.value}"
        else:
            disclaimer_type = "reminder"

        # Record the acknowledgment
        await self.disclaimer_service.record_disclaimer_acknowledgment(session_id, disclaimer_type)

        # Update session to mark disclaimer as acknowledged
        await self.session_manager.update_session(session_id, {"disclaimer_acknowledged": True})

        # Provide acknowledgment response
        if context.session.language == "es":
            response_text = "Gracias por reconocer el aviso legal. ¿Cómo puedo ayudarle con su situación legal hoy?"
        else:
            response_text = "Thank you for acknowledging the disclaimer. How can I help you with your legal situation today?"

        response = SystemResponse(
            text=response_text,
            requires_disclaimer=False,
            suggested_actions=[
                Action(
                    type="describe_issue",
                    description="Describe your legal issue",
                    parameters={}
                )
            ],
            resources=[],
            follow_up_questions=[
                "What type of legal issue are you facing?",
                "Can you describe your situation?"
            ]
        )

        # Record the conversation turn
        await self._record_conversation_turn(session_id, input_text, response, 1.0, False)

        return response

    async def _process_legal_query(
        self, session_id: SessionId, input_text: str, context: ConversationContext
    ) -> SystemResponse:
        """Process a legal query and generate guidance."""
        
        # Create or update legal issue from user input
        legal_issue = await self.legal_guidance_engine.create_legal_issue_from_query(
            input_text, context.session.user_context
        )

        # Update session with issue information
        await self.session_manager.update_session(session_id, {
            "user_context": {
                **context.session.user_context.model_dump(),
                "legal_issue_type": legal_issue.type,
                "urgency_level": legal_issue.urgency
            }
        })

        # Generate legal guidance
        guidance = await self.legal_guidance_engine.generate_guidance(
            legal_issue, context.session.user_context
        )

        # Generate resource referrals if professional help is recommended
        resources = []
        if guidance.recommends_professional_help:
            search_criteria = SearchCriteria(
                location=context.session.user_context.location,
                issue_type=legal_issue.type,
                language=context.session.user_context.preferred_language,
                urgency=legal_issue.urgency
            )
            resources = await self.resource_directory.generate_referrals(search_criteria, max_referrals=3)

        # Generate follow-up questions
        follow_up_questions = await self.generate_follow_up_questions(context)

        # Create suggested actions
        suggested_actions = self._generate_suggested_actions(legal_issue, guidance, resources)

        # Build response text
        response_text = self._build_response_text(guidance, resources, context.session.language)

        # Create system response
        response = SystemResponse(
            text=response_text,
            requires_disclaimer=False,
            suggested_actions=suggested_actions,
            resources=resources,
            follow_up_questions=follow_up_questions
        )

        # Record the conversation turn
        confidence = 0.9 if legal_issue.type != LegalIssueType.OTHER else 0.7
        await self._record_conversation_turn(session_id, input_text, response, confidence, False)

        return response

    async def generate_follow_up_questions(
        self, context: ConversationContext
    ) -> List[str]:
        """Generate relevant follow-up questions based on conversation context."""
        
        questions = []
        issue_type = context.session.user_context.legal_issue_type
        
        if not issue_type or issue_type == LegalIssueType.OTHER:
            # General clarifying questions
            questions = [
                "Can you provide more details about your situation?",
                "What type of legal issue are you facing?",
                "When did this situation begin?"
            ]
        elif issue_type == LegalIssueType.DOMESTIC_VIOLENCE:
            questions = [
                "Are you currently in a safe location?",
                "Do you need immediate safety resources?",
                "Have you been able to document any incidents?"
            ]
        elif issue_type == LegalIssueType.TENANT_RIGHTS:
            questions = [
                "What specific issue are you having with your landlord?",
                "Do you have a written lease agreement?",
                "Have you documented the problem in writing to your landlord?"
            ]
        elif issue_type == LegalIssueType.WAGE_THEFT:
            questions = [
                "Do you have records of your hours worked?",
                "Have you spoken with your employer about the missing wages?",
                "Do you have pay stubs or other documentation?"
            ]
        elif issue_type == LegalIssueType.LAND_DISPUTE:
            questions = [
                "Do you have a deed or other property documents?",
                "What is the nature of the property dispute?",
                "Have you had a recent property survey done?"
            ]

        # Translate questions if needed
        if context.session.language == "es":
            questions = self._translate_questions_to_spanish(questions)

        return questions[:3]  # Limit to 3 questions

    def _translate_questions_to_spanish(self, questions: List[str]) -> List[str]:
        """Translate follow-up questions to Spanish."""
        
        translation_map = {
            "Can you provide more details about your situation?": "¿Puede proporcionar más detalles sobre su situación?",
            "What type of legal issue are you facing?": "¿Qué tipo de problema legal está enfrentando?",
            "When did this situation begin?": "¿Cuándo comenzó esta situación?",
            "Are you currently in a safe location?": "¿Se encuentra actualmente en un lugar seguro?",
            "Do you need immediate safety resources?": "¿Necesita recursos de seguridad inmediatos?",
            "Have you been able to document any incidents?": "¿Ha podido documentar algún incidente?",
            "What specific issue are you having with your landlord?": "¿Qué problema específico tiene con su arrendador?",
            "Do you have a written lease agreement?": "¿Tiene un contrato de arrendamiento por escrito?",
            "Have you documented the problem in writing to your landlord?": "¿Ha documentado el problema por escrito a su arrendador?",
            "Do you have records of your hours worked?": "¿Tiene registros de las horas que trabajó?",
            "Have you spoken with your employer about the missing wages?": "¿Ha hablado con su empleador sobre los salarios faltantes?",
            "Do you have pay stubs or other documentation?": "¿Tiene talones de pago u otra documentación?",
            "Do you have a deed or other property documents?": "¿Tiene una escritura u otros documentos de propiedad?",
            "What is the nature of the property dispute?": "¿Cuál es la naturaleza de la disputa de propiedad?",
            "Have you had a recent property survey done?": "¿Ha tenido un levantamiento topográfico reciente de la propiedad?"
        }
        
        return [translation_map.get(q, q) for q in questions]

    def _generate_suggested_actions(self, legal_issue: LegalIssue, guidance, resources) -> List[Action]:
        """Generate suggested actions based on the legal issue and guidance."""
        
        actions = []
        
        # Document gathering action
        actions.append(Action(
            type="gather_documents",
            description="Gather relevant documents for your case",
            parameters={"issue_type": legal_issue.type.value}
        ))

        # Contact resource action if resources are available
        if resources:
            actions.append(Action(
                type="contact_resource",
                description=f"Contact {resources[0].organization.name}",
                parameters={
                    "organization_id": resources[0].organization.id,
                    "phone": resources[0].organization.contact_info.phone,
                    "contact_method": resources[0].contact_method.value
                }
            ))

        # Emergency action for urgent cases
        if legal_issue.urgency == UrgencyLevel.EMERGENCY:
            actions.append(Action(
                type="emergency_action",
                description="Seek immediate help",
                parameters={"urgency": "emergency"}
            ))

        return actions

    def _build_response_text(self, guidance, resources, language: str) -> str:
        """Build the response text combining guidance and resources."""
        
        response_parts = []
        
        # Add guidance summary
        response_parts.append(guidance.summary)
        
        # Add key steps
        if guidance.detailed_steps:
            if language == "es":
                response_parts.append("\nPasos recomendados:")
            else:
                response_parts.append("\nRecommended steps:")
            
            for i, step in enumerate(guidance.detailed_steps[:5], 1):  # Limit to 5 steps
                response_parts.append(f"{i}. {step}")

        # Add resource information
        if resources:
            if language == "es":
                response_parts.append(f"\nRecursos recomendados:")
            else:
                response_parts.append(f"\nRecommended resources:")
            
            for resource in resources[:2]:  # Limit to 2 resources in response text
                org = resource.organization
                response_parts.append(f"\n• {org.name}")
                response_parts.append(f"  Phone: {org.contact_info.phone}")
                if org.specializations:
                    specializations = [spec.value.replace('_', ' ').title() for spec in org.specializations]
                    if language == "es":
                        response_parts.append(f"  Especialidades: {', '.join(specializations)}")
                    else:
                        response_parts.append(f"  Specializations: {', '.join(specializations)}")

        # Add professional help recommendation
        if guidance.recommends_professional_help:
            if language == "es":
                response_parts.append("\nSe recomienda encarecidamente consultar con un abogado calificado para su situación específica.")
            else:
                response_parts.append("\nIt is strongly recommended to consult with a qualified attorney for your specific situation.")

        return "\n".join(response_parts)

    async def summarize_conversation(
        self, session_id: SessionId
    ) -> ConversationSummary:
        """Generate a summary of the conversation."""
        
        session = await self.session_manager.get_session(session_id)
        
        # Calculate duration
        duration = (session.last_activity - session.start_time).total_seconds() / 60.0
        
        # Extract issues discussed
        issues_discussed = []
        if session.user_context.legal_issue_type:
            issues_discussed.append(session.user_context.legal_issue_type)
        
        # Extract resources provided from conversation history
        resources_provided = []
        for turn in session.conversation_history:
            resources_provided.extend(turn.system_response.resources)
        
        # Generate next steps from the last guidance provided
        next_steps = []
        if session.conversation_history:
            last_response = session.conversation_history[-1].system_response
            if last_response.suggested_actions:
                next_steps = [action.description for action in last_response.suggested_actions]
        
        # Extract disclaimers shown
        disclaimers_shown = []
        for turn in session.conversation_history:
            if turn.disclaimer_shown:
                disclaimers_shown.append("Legal disclaimer presented")
        
        return ConversationSummary(
            session_id=session_id,
            duration=duration,
            issues_discussed=issues_discussed,
            resources_provided=resources_provided,
            next_steps=next_steps,
            disclaimers_shown=disclaimers_shown
        )

    def should_end_conversation(self, context: ConversationContext) -> bool:
        """Determine if the conversation should be ended."""
        
        # End if conversation is very long (more than 20 turns)
        if context.conversation_length > 20:
            return True
        
        # End if user indicates they want to end
        end_indicators = ["goodbye", "thank you", "that's all", "no more questions", 
                         "adiós", "gracias", "eso es todo", "no más preguntas"]
        
        user_input_lower = context.last_user_input.lower()
        for indicator in end_indicators:
            if indicator in user_input_lower:
                return True
        
        return False

    def _is_disclaimer_acknowledgment(self, input_text: str) -> bool:
        """Check if user input is acknowledging a disclaimer."""
        
        acknowledgment_phrases = [
            "yes", "i understand", "i acknowledge", "i agree", "understood", "ok", "okay",
            "sí", "entiendo", "reconozco", "estoy de acuerdo", "entendido"
        ]
        
        input_lower = input_text.lower().strip()
        
        # Check for negative responses first
        negative_phrases = ["no", "don't", "not", "disagree", "refuse"]
        if any(neg in input_lower for neg in negative_phrases):
            return False
        
        return any(phrase in input_lower for phrase in acknowledgment_phrases)

    async def _record_conversation_turn(
        self, session_id: SessionId, user_input: str, system_response: SystemResponse,
        confidence: float, disclaimer_shown: bool
    ) -> None:
        """Record a conversation turn in the session history."""
        
        turn = ConversationTurn(
            timestamp=datetime.now(),
            user_input=user_input,
            system_response=system_response,
            confidence=confidence,
            disclaimer_shown=disclaimer_shown
        )
        
        # Get current session
        session = await self.session_manager.get_session(session_id)
        
        # Add turn to conversation history
        session.conversation_history.append(turn)
        
        # Update session
        await self.session_manager.update_session(session_id, {
            "conversation_history": [turn.model_dump() for turn in session.conversation_history],
            "last_activity": datetime.now()
        })


# Factory function for creating the conversation engine
def create_conversation_engine(
    session_manager: SessionManager,
    legal_guidance_engine: BasicLegalGuidanceEngine,
    resource_directory: ResourceDirectory,
    disclaimer_service: DisclaimerService
) -> ConversationEngine:
    """Create and return a conversation engine instance."""
    return BasicConversationEngine(
        session_manager, legal_guidance_engine, resource_directory, disclaimer_service
    )