"""
Disclaimer Service implementation for the AI Legal Aid System.

This module provides functionality for managing legal disclaimers,
compliance requirements, and boundary enforcement for legal advice.
"""

from datetime import datetime
from typing import Dict, List, Set

from ai_legal_aid.interfaces.compliance import DisclaimerService
from ai_legal_aid.types import (
    SessionId,
    LegalIssueType,
    ConversationContext,
    AuditRecord,
)


class BasicDisclaimerService:
    """
    Basic implementation of the Disclaimer Service.
    
    This implementation provides context-aware disclaimer delivery,
    acknowledgment tracking, and compliance audit trails.
    """

    def __init__(self):
        """Initialize the disclaimer service with templates and tracking."""
        self._disclaimer_acknowledgments: Dict[SessionId, Set[str]] = {}
        self._audit_records: List[AuditRecord] = []
        self._disclaimer_templates = self._initialize_disclaimer_templates()

    def _initialize_disclaimer_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize disclaimer templates for different contexts and languages."""
        return {
            "initial": {
                "en": """
IMPORTANT LEGAL DISCLAIMER

This AI Legal Aid System provides general legal information only and is NOT a substitute for professional legal advice. 

KEY LIMITATIONS:
• This system does NOT provide legal advice or create an attorney-client relationship
• Information provided is general in nature and may not apply to your specific situation
• Laws vary by jurisdiction and change frequently
• This system cannot replace consultation with a qualified attorney

RECOMMENDATIONS:
• For specific legal advice, consult with a licensed attorney
• For emergencies, contact 911 or emergency services immediately
• For urgent legal matters, seek immediate professional legal assistance

By continuing, you acknowledge that you understand these limitations and that any information provided is for educational purposes only.

Do you understand and acknowledge this disclaimer?
""",
                "es": """
AVISO LEGAL IMPORTANTE

Este Sistema de Asistencia Legal con IA proporciona solo información legal general y NO es un sustituto del consejo legal profesional.

LIMITACIONES CLAVE:
• Este sistema NO proporciona consejo legal ni crea una relación abogado-cliente
• La información proporcionada es de naturaleza general y puede no aplicarse a su situación específica
• Las leyes varían según la jurisdicción y cambian frecuentemente
• Este sistema no puede reemplazar la consulta con un abogado calificado

RECOMENDACIONES:
• Para consejo legal específico, consulte con un abogado licenciado
• Para emergencias, contacte al 911 o servicios de emergencia inmediatamente
• Para asuntos legales urgentes, busque asistencia legal profesional inmediata

Al continuar, usted reconoce que entiende estas limitaciones y que cualquier información proporcionada es solo para propósitos educativos.

¿Entiende y reconoce este aviso legal?
"""
            },
            "domestic_violence": {
                "en": """
DOMESTIC VIOLENCE SAFETY DISCLAIMER

IMMEDIATE SAFETY: If you are in immediate danger, call 911 now.

IMPORTANT SAFETY CONSIDERATIONS:
• Your safety is the top priority
• This system cannot assess your immediate safety situation
• Technology use may be monitored by abusers
• Consider using a safe computer or phone if possible

PROFESSIONAL HELP STRONGLY RECOMMENDED:
• Domestic violence cases require specialized legal and safety expertise
• Contact the National Domestic Violence Hotline: 1-800-799-7233
• Seek assistance from local domestic violence organizations
• Consider consulting with an attorney experienced in domestic violence cases

This system provides general information only and cannot replace professional safety planning and legal advice for domestic violence situations.
""",
                "es": """
AVISO DE SEGURIDAD PARA VIOLENCIA DOMÉSTICA

SEGURIDAD INMEDIATA: Si está en peligro inmediato, llame al 911 ahora.

CONSIDERACIONES IMPORTANTES DE SEGURIDAD:
• Su seguridad es la máxima prioridad
• Este sistema no puede evaluar su situación de seguridad inmediata
• El uso de tecnología puede ser monitoreado por abusadores
• Considere usar una computadora o teléfono seguro si es posible

AYUDA PROFESIONAL FUERTEMENTE RECOMENDADA:
• Los casos de violencia doméstica requieren experiencia legal y de seguridad especializada
• Contacte la Línea Nacional de Violencia Doméstica: 1-800-799-7233
• Busque asistencia de organizaciones locales de violencia doméstica
• Considere consultar con un abogado con experiencia en casos de violencia doméstica

Este sistema proporciona solo información general y no puede reemplazar la planificación profesional de seguridad y consejo legal para situaciones de violencia doméstica.
"""
            },
            "tenant_rights": {
                "en": """
HOUSING LAW DISCLAIMER

JURISDICTION-SPECIFIC LAWS:
• Housing and tenant laws vary significantly by state, county, and city
• Local ordinances may provide additional protections
• This information may not reflect your local laws

PROFESSIONAL CONSULTATION RECOMMENDED:
• Housing law can be complex and fact-specific
• Eviction proceedings have strict timelines and procedures
• Consider consulting with a tenant rights attorney or housing counselor
• Contact local legal aid organizations for assistance

This system provides general information about tenant rights and housing law, but cannot provide specific legal advice for your situation.
""",
                "es": """
AVISO SOBRE LEYES DE VIVIENDA

LEYES ESPECÍFICAS POR JURISDICCIÓN:
• Las leyes de vivienda e inquilinos varían significativamente por estado, condado y ciudad
• Las ordenanzas locales pueden proporcionar protecciones adicionales
• Esta información puede no reflejar sus leyes locales

CONSULTA PROFESIONAL RECOMENDADA:
• La ley de vivienda puede ser compleja y específica a los hechos
• Los procedimientos de desalojo tienen plazos y procedimientos estrictos
• Considere consultar con un abogado de derechos de inquilinos o consejero de vivienda
• Contacte organizaciones locales de asistencia legal para ayuda

Este sistema proporciona información general sobre derechos de inquilinos y ley de vivienda, pero no puede proporcionar consejo legal específico para su situación.
"""
            },
            "wage_theft": {
                "en": """
EMPLOYMENT LAW DISCLAIMER

FEDERAL AND STATE LAW VARIATIONS:
• Employment laws vary between federal and state jurisdictions
• Some states provide greater protections than federal law
• Local ordinances may also apply

TIME-SENSITIVE MATTERS:
• Wage claims often have strict filing deadlines
• Document preservation is critical
• Prompt action may be required to preserve your rights

PROFESSIONAL ASSISTANCE RECOMMENDED:
• Employment law can be complex with specific procedural requirements
• Consider consulting with an employment attorney
• Contact your state's Department of Labor for guidance
• Document all communications and keep detailed records

This system provides general information about employment rights, but cannot provide specific legal advice for your wage and hour situation.
""",
                "es": """
AVISO SOBRE LEYES LABORALES

VARIACIONES EN LEYES FEDERALES Y ESTATALES:
• Las leyes laborales varían entre jurisdicciones federales y estatales
• Algunos estados proporcionan mayores protecciones que la ley federal
• Las ordenanzas locales también pueden aplicar

ASUNTOS SENSIBLES AL TIEMPO:
• Los reclamos salariales a menudo tienen plazos de presentación estrictos
• La preservación de documentos es crítica
• Puede requerirse acción rápida para preservar sus derechos

ASISTENCIA PROFESIONAL RECOMENDADA:
• La ley laboral puede ser compleja con requisitos procesales específicos
• Considere consultar con un abogado laboral
• Contacte el Departamento de Trabajo de su estado para orientación
• documente todas las comunicaciones y mantenga registros detallados

Este sistema proporciona información general sobre derechos laborales, pero no puede proporcionar consejo legal específico para su situación de salarios y horas.
"""
            },
            "land_dispute": {
                "en": """
PROPERTY LAW DISCLAIMER

COMPLEX LEGAL AREA:
• Property law involves complex legal concepts and procedures
• Boundary disputes may require professional surveying
• Title issues can have significant financial implications

DOCUMENTATION CRITICAL:
• Property disputes often depend on detailed documentation
• Professional legal review of documents is recommended
• Survey and title work may be necessary

PROFESSIONAL CONSULTATION STRONGLY RECOMMENDED:
• Property law varies significantly by jurisdiction
• Real estate transactions and disputes can involve substantial financial stakes
• Consider consulting with a real estate attorney
• Title companies and surveyors may also provide valuable assistance

This system provides general information about property rights, but cannot provide specific legal advice for your property situation.
""",
                "es": """
AVISO SOBRE LEYES DE PROPIEDAD

ÁREA LEGAL COMPLEJA:
• La ley de propiedad involucra conceptos y procedimientos legales complejos
• Las disputas de límites pueden requerir topografía profesional
• Los problemas de título pueden tener implicaciones financieras significativas

DOCUMENTACIÓN CRÍTICA:
• Las disputas de propiedad a menudo dependen de documentación detallada
• Se recomienda revisión legal profesional de documentos
• Puede ser necesario trabajo de topografía y título

CONSULTA PROFESIONAL FUERTEMENTE RECOMENDADA:
• La ley de propiedad varía significativamente por jurisdicción
• Las transacciones y disputas de bienes raíces pueden involucrar intereses financieros sustanciales
• Considere consultar con un abogado de bienes raíces
• Las compañías de títulos y topógrafos también pueden proporcionar asistencia valiosa

Este sistema proporciona información general sobre derechos de propiedad, pero no puede proporcionar consejo legal específico para su situación de propiedad.
"""
            },
            "contextual_reminder": {
                "en": """
REMINDER: This information is for educational purposes only and does not constitute legal advice. For specific guidance on your situation, please consult with a qualified attorney.
""",
                "es": """
RECORDATORIO: Esta información es solo para propósitos educativos y no constituye consejo legal. Para orientación específica sobre su situación, por favor consulte con un abogado calificado.
"""
            }
        }

    async def get_initial_disclaimer(self, language: str = "en") -> str:
        """Get the initial disclaimer shown to users at session start."""
        return self._disclaimer_templates["initial"].get(language, 
                                                        self._disclaimer_templates["initial"]["en"])

    async def get_contextual_disclaimer(
        self, issue_type: LegalIssueType, language: str = "en"
    ) -> str:
        """Get a contextual disclaimer based on the legal issue type."""
        
        # Map issue types to disclaimer templates
        issue_disclaimer_map = {
            LegalIssueType.DOMESTIC_VIOLENCE: "domestic_violence",
            LegalIssueType.TENANT_RIGHTS: "tenant_rights",
            LegalIssueType.WAGE_THEFT: "wage_theft",
            LegalIssueType.LAND_DISPUTE: "land_dispute",
        }
        
        disclaimer_type = issue_disclaimer_map.get(issue_type)
        
        if disclaimer_type and disclaimer_type in self._disclaimer_templates:
            return self._disclaimer_templates[disclaimer_type].get(
                language, self._disclaimer_templates[disclaimer_type]["en"]
            )
        
        # Default contextual reminder for unknown issue types
        return self._disclaimer_templates["contextual_reminder"].get(
            language, self._disclaimer_templates["contextual_reminder"]["en"]
        )

    async def record_disclaimer_acknowledgment(
        self, session_id: SessionId, disclaimer_type: str
    ) -> None:
        """Record that a user has acknowledged a disclaimer."""
        
        # Initialize session tracking if not exists
        if session_id not in self._disclaimer_acknowledgments:
            self._disclaimer_acknowledgments[session_id] = set()
        
        # Record the acknowledgment
        self._disclaimer_acknowledgments[session_id].add(disclaimer_type)
        
        # Create audit record
        audit_record = AuditRecord(
            session_id=session_id,
            timestamp=datetime.now(),
            action="disclaimer_acknowledged",
            details={
                "disclaimer_type": disclaimer_type,
                "acknowledged_at": datetime.now().isoformat()
            },
            compliance_flags=["disclaimer_compliance"]
        )
        
        self._audit_records.append(audit_record)

    def should_show_disclaimer(self, context: ConversationContext) -> bool:
        """Determine if a disclaimer should be shown based on conversation context."""
        
        session_id = context.session.id
        
        # Always show initial disclaimer if not acknowledged
        if not self._has_acknowledged_disclaimer(session_id, "initial"):
            return True
        
        # Show contextual disclaimer for new issue types
        if context.session.user_context.legal_issue_type:
            issue_type = context.session.user_context.legal_issue_type
            contextual_type = f"contextual_{issue_type.value}"
            
            if not self._has_acknowledged_disclaimer(session_id, contextual_type):
                return True
        
        # Show reminder disclaimer periodically (every 5 turns)
        if context.conversation_length > 0 and context.conversation_length % 5 == 0:
            return True
        
        # Show disclaimer for high-risk situations
        if self._is_high_risk_situation(context):
            # Check if high-risk disclaimer has been acknowledged for this session
            if not self._has_acknowledged_disclaimer(session_id, "high_risk"):
                return True
        
        return False

    def _has_acknowledged_disclaimer(self, session_id: SessionId, disclaimer_type: str) -> bool:
        """Check if a user has acknowledged a specific disclaimer type."""
        if session_id not in self._disclaimer_acknowledgments:
            return False
        
        return disclaimer_type in self._disclaimer_acknowledgments[session_id]

    def _is_high_risk_situation(self, context: ConversationContext) -> bool:
        """Determine if the current situation is high-risk and requires additional disclaimers."""
        
        # High-risk keywords in user input
        high_risk_keywords = [
            "sue", "lawsuit", "court", "trial", "arrest", "criminal", "charges",
            "emergency", "urgent", "deadline", "eviction notice", "served",
            "violence", "abuse", "threat", "danger", "safety"
        ]
        
        last_input = context.last_user_input.lower()
        
        for keyword in high_risk_keywords:
            if keyword in last_input:
                return True
        
        # High urgency situations
        if (context.session.user_context.urgency_level and 
            context.session.user_context.urgency_level.value in ["high", "emergency"]):
            return True
        
        # Domestic violence cases always high-risk
        if (context.session.user_context.legal_issue_type == 
            LegalIssueType.DOMESTIC_VIOLENCE):
            return True
        
        return False

    def get_disclaimer_acknowledgment_status(self, session_id: SessionId) -> Dict[str, bool]:
        """Get the disclaimer acknowledgment status for a session."""
        if session_id not in self._disclaimer_acknowledgments:
            return {}
        
        acknowledged_types = self._disclaimer_acknowledgments[session_id]
        
        return {
            "initial": "initial" in acknowledged_types,
            "contextual_domestic_violence": "contextual_domestic_violence" in acknowledged_types,
            "contextual_tenant_rights": "contextual_tenant_rights" in acknowledged_types,
            "contextual_wage_theft": "contextual_wage_theft" in acknowledged_types,
            "contextual_land_dispute": "contextual_land_dispute" in acknowledged_types,
        }

    def get_audit_records(self, session_id: SessionId = None) -> List[AuditRecord]:
        """Get audit records for compliance tracking."""
        if session_id:
            return [record for record in self._audit_records if record.session_id == session_id]
        
        return self._audit_records.copy()

    def clear_session_data(self, session_id: SessionId) -> None:
        """Clear disclaimer data for a session (for cleanup)."""
        if session_id in self._disclaimer_acknowledgments:
            del self._disclaimer_acknowledgments[session_id]

    async def get_legal_advice_boundary_message(self, language: str = "en") -> str:
        """Get message explaining legal advice boundaries."""
        
        messages = {
            "en": """
I cannot provide specific legal advice or tell you exactly what to do in your legal situation. 

What I CAN do:
• Provide general information about legal topics
• Explain common legal processes and procedures
• Help you understand your general rights
• Connect you with appropriate legal resources
• Suggest questions to ask a lawyer

What I CANNOT do:
• Give you specific legal advice for your situation
• Tell you what legal action to take
• Interpret legal documents for your specific case
• Represent you or act as your attorney
• Guarantee any legal outcomes

For specific legal advice tailored to your situation, you need to consult with a licensed attorney who can review your specific facts and circumstances.
""",
            "es": """
No puedo proporcionar consejo legal específico o decirle exactamente qué hacer en su situación legal.

Lo que SÍ puedo hacer:
• Proporcionar información general sobre temas legales
• Explicar procesos y procedimientos legales comunes
• Ayudarle a entender sus derechos generales
• Conectarle con recursos legales apropiados
• Sugerir preguntas para hacerle a un abogado

Lo que NO puedo hacer:
• Darle consejo legal específico para su situación
• Decirle qué acción legal tomar
• Interpretar documentos legales para su caso específico
• Representarle o actuar como su abogado
• Garantizar cualquier resultado legal

Para consejo legal específico adaptado a su situación, necesita consultar con un abogado licenciado que pueda revisar sus hechos y circunstancias específicas.
"""
        }
        
        return messages.get(language, messages["en"])


# Factory function for creating the disclaimer service
def create_disclaimer_service() -> DisclaimerService:
    """Create and return a disclaimer service instance."""
    return BasicDisclaimerService()