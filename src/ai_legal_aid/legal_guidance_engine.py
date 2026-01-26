"""
Legal Guidance Engine implementation for the AI Legal Aid System.

This module provides the core legal guidance functionality including
issue classification, guidance generation, complexity assessment,
and legal citation retrieval.
"""

import re
from typing import Dict, List

from ai_legal_aid.interfaces.legal import LegalGuidanceEngine
from ai_legal_aid.types import (
    LegalIssueType,
    ComplexityLevel,
    UrgencyLevel,
    LegalIssue,
    LegalGuidance,
    LegalCitation,
    UserContext,
)


class BasicLegalGuidanceEngine:
    """
    Basic implementation of the Legal Guidance Engine.
    
    This implementation provides rule-based legal issue classification
    and guidance generation for common legal issues.
    """

    def __init__(self):
        """Initialize the legal guidance engine with knowledge base."""
        self._issue_keywords = {
            LegalIssueType.LAND_DISPUTE: [
                "property", "land", "boundary", "deed", "title", "neighbor",
                "fence", "easement", "zoning", "property line", "real estate",
                "ownership", "survey", "encroachment"
            ],
            LegalIssueType.DOMESTIC_VIOLENCE: [
                "domestic violence", "abuse", "restraining order", "protection order",
                "stalking", "harassment", "intimate partner", "spouse", "boyfriend",
                "girlfriend", "family violence", "assault", "battery", "threats"
            ],
            LegalIssueType.WAGE_THEFT: [
                "wages", "paycheck", "overtime", "unpaid", "salary", "minimum wage",
                "employer", "work", "job", "labor", "hours", "pay", "compensation",
                "benefits", "time", "shift"
            ],
            LegalIssueType.TENANT_RIGHTS: [
                "rent", "landlord", "tenant", "lease", "eviction", "deposit",
                "apartment", "housing", "repairs", "maintenance", "utilities",
                "habitability", "rental", "renter", "property manager", "evict"
            ]
        }

        self._guidance_templates = {
            LegalIssueType.LAND_DISPUTE: {
                "summary": "Property disputes often involve boundary issues, ownership questions, or neighbor conflicts.",
                "steps": [
                    "Gather all property documents including deed, survey, and title insurance",
                    "Document the specific issue with photos and written descriptions",
                    "Check local zoning laws and property records",
                    "Attempt to resolve the matter through direct communication with the other party",
                    "Consider mediation services before pursuing litigation",
                    "Consult with a real estate attorney if the dispute involves significant value or complex legal issues"
                ],
                "laws": ["State Property Law", "Local Zoning Ordinances", "Adverse Possession Statutes"]
            },
            LegalIssueType.DOMESTIC_VIOLENCE: {
                "summary": "Domestic violence is a serious crime with legal protections available for victims.",
                "steps": [
                    "Ensure your immediate safety - call 911 if in danger",
                    "Contact the National Domestic Violence Hotline: 1-800-799-7233",
                    "Document all incidents with dates, photos, and witness information",
                    "Consider filing for a restraining order or protection order",
                    "Preserve evidence including medical records, photos, and communications",
                    "Seek support from local domestic violence organizations",
                    "Consult with an attorney who specializes in domestic violence cases"
                ],
                "laws": ["Violence Against Women Act (VAWA)", "State Domestic Violence Laws", "Protection Order Statutes"]
            },
            LegalIssueType.WAGE_THEFT: {
                "summary": "Workers have legal rights to fair wages and proper compensation for their work.",
                "steps": [
                    "Keep detailed records of hours worked, pay stubs, and employment agreements",
                    "Calculate the exact amount of unpaid wages owed",
                    "Speak with your employer about the wage issue in writing",
                    "File a complaint with your state's Department of Labor",
                    "Contact the U.S. Department of Labor Wage and Hour Division",
                    "Consider filing a lawsuit if other remedies are unsuccessful",
                    "Consult with an employment attorney for complex cases"
                ],
                "laws": ["Fair Labor Standards Act (FLSA)", "State Minimum Wage Laws", "State Overtime Laws"]
            },
            LegalIssueType.TENANT_RIGHTS: {
                "summary": "Tenants have legal rights regarding housing conditions, rent, and eviction procedures.",
                "steps": [
                    "Review your lease agreement carefully",
                    "Document any housing problems with photos and written notices to landlord",
                    "Understand your state's tenant rights and landlord obligations",
                    "Communicate with your landlord in writing about issues",
                    "Know the proper legal procedures for rent withholding or repair requests",
                    "Contact local tenant rights organizations for assistance",
                    "Seek legal counsel if facing eviction or serious habitability issues"
                ],
                "laws": ["State Landlord-Tenant Laws", "Local Housing Codes", "Fair Housing Act"]
            }
        }

        self._complexity_indicators = {
            "high": [
                "court", "lawsuit", "attorney", "legal action", "trial", "judge",
                "criminal", "felony", "federal", "constitutional", "appeal"
            ],
            "moderate": [
                "contract dispute", "agreement violation", "breach", "dispute", "claim",
                "damages", "settlement", "mediation", "arbitration", "violation"
            ]
        }

        self._urgency_indicators = {
            "emergency": [
                "emergency", "immediate danger", "threat", "violence", "assault",
                "eviction notice", "deadline tomorrow", "urgent"
            ],
            "high": [
                "court date next week", "deadline", "time sensitive", "quickly",
                "harassment", "stalking", "unsafe", "threatened", "need help quickly"
            ]
        }

    async def classify_legal_issue(self, query: str) -> LegalIssueType:
        """
        Classify a legal query into a specific issue type.
        
        Uses keyword matching to determine the most likely legal issue type
        based on the user's description.
        """
        query_lower = query.lower()
        scores = {}

        # Score each issue type based on keyword matches
        for issue_type, keywords in self._issue_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    # Give higher weight to exact phrase matches
                    if len(keyword.split()) > 1:
                        score += 3
                    else:
                        score += 1
            scores[issue_type] = score

        # Return the highest scoring issue type, or OTHER if no clear match
        if not scores or max(scores.values()) == 0:
            return LegalIssueType.OTHER

        return max(scores, key=scores.get)

    async def generate_guidance(
        self, issue: LegalIssue, context: UserContext
    ) -> LegalGuidance:
        """
        Generate legal guidance for a specific issue.
        
        Provides structured guidance including summary, steps, and applicable laws.
        Enhanced with better professional help referral logic.
        """
        template = self._guidance_templates.get(issue.type)
        
        if not template:
            # Generic guidance for unrecognized issues
            return LegalGuidance(
                summary="This appears to be a legal issue that may require professional consultation.",
                detailed_steps=[
                    "Document all relevant facts and gather supporting materials",
                    "Research applicable laws in your jurisdiction",
                    "Consider consulting with a qualified attorney",
                    "Contact your local bar association for attorney referrals",
                    "Look into legal aid organizations in your area"
                ],
                urgency_level=issue.urgency,
                recommends_professional_help=True,
                applicable_laws=["Consult with attorney for applicable laws"]
            )

        # Customize guidance based on urgency and complexity
        steps = template["steps"].copy()
        
        # Enhanced professional help recommendation logic
        recommends_professional = self._should_recommend_professional_help(issue, context)
        
        # Add urgency-specific guidance
        if issue.urgency == UrgencyLevel.EMERGENCY:
            steps.insert(0, "URGENT: Seek immediate help - call 911 if in physical danger")
            steps.insert(1, "Contact emergency legal services or domestic violence hotline immediately")
            recommends_professional = True
        elif issue.urgency == UrgencyLevel.HIGH:
            steps.insert(0, "Address this issue promptly as time may be critical")
            steps.insert(1, "Consider seeking immediate legal consultation")

        # Add complexity-specific guidance
        if issue.complexity == ComplexityLevel.COMPLEX:
            steps.append("This is a complex legal matter - professional legal representation is strongly recommended")
            steps.append("Consider seeking a consultation with a specialist attorney in this area of law")
            recommends_professional = True
        elif issue.complexity == ComplexityLevel.MODERATE:
            steps.append("Consider consulting with an attorney for personalized advice on your situation")

        # Add context-specific guidance
        if context.location and context.location.state:
            steps.append(f"Research {context.location.state} state-specific laws that may apply to your situation")
            
        if context.household_income in ["very_low", "low"]:
            steps.append("You may qualify for free or low-cost legal aid services")
            steps.append("Contact your local legal aid society for assistance")

        return LegalGuidance(
            summary=template["summary"],
            detailed_steps=steps,
            urgency_level=issue.urgency,
            recommends_professional_help=recommends_professional,
            applicable_laws=template["laws"]
        )

    def _should_recommend_professional_help(self, issue: LegalIssue, context: UserContext) -> bool:
        """
        Determine if professional legal help should be recommended.
        
        Enhanced logic considering multiple factors.
        """
        # Always recommend for complex cases
        if issue.complexity == ComplexityLevel.COMPLEX:
            return True
            
        # Always recommend for emergency situations
        if issue.urgency == UrgencyLevel.EMERGENCY:
            return True
            
        # Recommend for domestic violence cases regardless of complexity
        if issue.type == LegalIssueType.DOMESTIC_VIOLENCE:
            return True
            
        # Recommend for high urgency cases
        if issue.urgency == UrgencyLevel.HIGH:
            return True
            
        # Recommend for moderate complexity cases
        if issue.complexity == ComplexityLevel.MODERATE:
            return True
            
        # Recommend if multiple parties are involved
        if len(issue.involved_parties) > 1:
            return True
            
        # Recommend if significant documents are involved
        if issue.documents and len(issue.documents) > 2:
            return True
            
        # Check for specific keywords that indicate need for professional help
        description_lower = issue.description.lower()
        professional_help_keywords = [
            "sue", "sued", "lawsuit", "court", "trial", "judge", "attorney",
            "legal action", "damages", "settlement", "contract", "criminal",
            "arrest", "charges", "felony", "misdemeanor"
        ]
        
        for keyword in professional_help_keywords:
            if keyword in description_lower:
                return True
                
        return False

    async def assess_complexity(self, issue: LegalIssue) -> ComplexityLevel:
        """
        Assess the complexity level of a legal issue.
        
        Uses keyword analysis and issue characteristics to determine complexity.
        Enhanced with better referral logic.
        """
        description_lower = issue.description.lower()
        
        # Check for high complexity indicators
        for indicator in self._complexity_indicators["high"]:
            if indicator in description_lower:
                return ComplexityLevel.COMPLEX

        # Check for moderate complexity indicators
        for indicator in self._complexity_indicators["moderate"]:
            if indicator in description_lower:
                return ComplexityLevel.MODERATE

        # Enhanced complexity assessment based on issue characteristics
        complexity_score = 0
        
        # Issue-specific complexity factors
        if issue.type == LegalIssueType.DOMESTIC_VIOLENCE:
            # DV cases are inherently complex due to safety and legal considerations
            complexity_score += 2
        elif issue.type == LegalIssueType.LAND_DISPUTE:
            # Property disputes can be complex due to legal technicalities
            complexity_score += 1
        
        # Multiple parties increase complexity
        if len(issue.involved_parties) > 2:
            complexity_score += 2
        elif len(issue.involved_parties) == 2:
            complexity_score += 1
            
        # Many documents suggest complexity
        if issue.documents and len(issue.documents) > 3:
            complexity_score += 2
        elif issue.documents and len(issue.documents) > 1:
            complexity_score += 1
            
        # Urgency can indicate complexity
        if issue.urgency == UrgencyLevel.EMERGENCY:
            complexity_score += 2
        elif issue.urgency == UrgencyLevel.HIGH:
            complexity_score += 1
            
        # Long descriptions often indicate complex situations
        word_count = len(issue.description.split())
        if word_count > 50:
            complexity_score += 2
        elif word_count > 25:
            complexity_score += 1
            
        # Time-sensitive issues
        if issue.timeframe and any(word in issue.timeframe.lower() 
                                 for word in ["years", "months", "ongoing"]):
            complexity_score += 1
            
        # Determine final complexity level
        if complexity_score >= 4:
            return ComplexityLevel.COMPLEX
        elif complexity_score >= 2:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.SIMPLE

    async def get_citations(self, issue: LegalIssue) -> List[LegalCitation]:
        """
        Get relevant legal citations for an issue.
        
        Returns basic citations for common legal authorities relevant to each issue type.
        """
        citations = []

        if issue.type == LegalIssueType.LAND_DISPUTE:
            citations.extend([
                LegalCitation(
                    title="State Property Law",
                    jurisdiction="State",
                    summary="Governs property ownership, boundaries, and disputes"
                ),
                LegalCitation(
                    title="Local Zoning Ordinances",
                    jurisdiction="Local",
                    summary="Regulates land use and property development"
                )
            ])

        elif issue.type == LegalIssueType.DOMESTIC_VIOLENCE:
            citations.extend([
                LegalCitation(
                    title="Violence Against Women Act (VAWA)",
                    jurisdiction="Federal",
                    url="https://www.justice.gov/ovw/violence-against-women-act",
                    summary="Federal law providing protections for domestic violence victims"
                ),
                LegalCitation(
                    title="State Domestic Violence Protection Act",
                    jurisdiction="State",
                    summary="State-specific protections and remedies for domestic violence"
                )
            ])

        elif issue.type == LegalIssueType.WAGE_THEFT:
            citations.extend([
                LegalCitation(
                    title="Fair Labor Standards Act (FLSA)",
                    section="29 U.S.C. § 201",
                    jurisdiction="Federal",
                    url="https://www.dol.gov/agencies/whd/flsa",
                    summary="Federal law establishing minimum wage and overtime requirements"
                ),
                LegalCitation(
                    title="State Wage and Hour Laws",
                    jurisdiction="State",
                    summary="State-specific wage and hour protections"
                )
            ])

        elif issue.type == LegalIssueType.TENANT_RIGHTS:
            citations.extend([
                LegalCitation(
                    title="State Landlord-Tenant Act",
                    jurisdiction="State",
                    summary="Governs rental relationships and tenant rights"
                ),
                LegalCitation(
                    title="Fair Housing Act",
                    section="42 U.S.C. § 3601",
                    jurisdiction="Federal",
                    url="https://www.hud.gov/program_offices/fair_housing_equal_opp/fair_housing_act_overview",
                    summary="Prohibits housing discrimination"
                )
            ])

        return citations

    def _assess_urgency_from_description(self, description: str) -> UrgencyLevel:
        """
        Assess urgency level based on description keywords.
        
        Enhanced helper method to determine urgency from user's description.
        """
        description_lower = description.lower()

        # Check for emergency indicators
        for indicator in self._urgency_indicators["emergency"]:
            if indicator in description_lower:
                return UrgencyLevel.EMERGENCY

        # Check for high urgency indicators
        for indicator in self._urgency_indicators["high"]:
            if indicator in description_lower:
                return UrgencyLevel.HIGH

        # Enhanced time-sensitive pattern detection
        time_patterns = [
            r'\b(today|tomorrow|this week)\b',
            r'\b(deadline|due|expires?)\b',
            r'\b(court date|hearing)\b',
            r'\b(eviction notice|notice to quit)\b',
            r'\b(served|summons)\b',
            r'\b(arrest|detained|custody)\b'
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, description_lower):
                return UrgencyLevel.HIGH

        # Check for medium urgency indicators
        medium_urgency_keywords = [
            "soon", "next month", "within", "before", "by", "until",
            "worried", "concerned", "need help", "advice"
        ]
        
        for keyword in medium_urgency_keywords:
            if keyword in description_lower:
                return UrgencyLevel.MEDIUM

        return UrgencyLevel.LOW

    async def create_legal_issue_from_query(self, query: str, user_context: UserContext = None) -> LegalIssue:
        """
        Create a LegalIssue object from a user query.
        
        This is a helper method that combines classification, urgency assessment,
        and complexity assessment to create a complete LegalIssue object.
        """
        # Classify the issue type
        issue_type = await self.classify_legal_issue(query)
        
        # Assess urgency from the description
        urgency = self._assess_urgency_from_description(query)
        
        # Create initial issue object
        issue = LegalIssue(
            type=issue_type,
            description=query,
            urgency=urgency,
            complexity=ComplexityLevel.SIMPLE,  # Will be updated below
            involved_parties=self._extract_involved_parties(query),
            timeframe=self._extract_timeframe(query),
            documents=self._extract_document_types(query)
        )
        
        # Assess complexity based on the complete issue
        issue.complexity = await self.assess_complexity(issue)
        
        return issue

    def _extract_involved_parties(self, description: str) -> List[str]:
        """Extract involved parties from the description."""
        parties = []
        description_lower = description.lower()
        
        party_keywords = {
            "landlord": ["landlord", "property manager", "property owner"],
            "employer": ["employer", "boss", "company", "workplace", "job"],
            "neighbor": ["neighbor", "neighbour"],
            "spouse": ["spouse", "husband", "wife"],
            "partner": ["partner", "boyfriend", "girlfriend"],
            "family": ["family", "relative", "parent", "child"],
            "police": ["police", "officer", "cop"],
            "court": ["court", "judge", "lawyer", "attorney"]
        }
        
        for party_type, keywords in party_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    parties.append(party_type)
                    break
                    
        return list(set(parties))  # Remove duplicates

    def _extract_timeframe(self, description: str) -> str:
        """Extract timeframe information from the description."""
        description_lower = description.lower()
        
        timeframe_patterns = [
            r'\b(yesterday|today|tomorrow)\b',
            r'\b(last|this|next)\s+(week|month|year)\b',
            r'\b(\d+)\s+(days?|weeks?|months?|years?)\s+ago\b',
            r'\b(recently|ongoing|current)\b'
        ]
        
        for pattern in timeframe_patterns:
            match = re.search(pattern, description_lower)
            if match:
                return match.group(0)
                
        return None

    def _extract_document_types(self, description: str) -> List[str]:
        """Extract document types mentioned in the description."""
        documents = []
        description_lower = description.lower()
        
        document_keywords = {
            "contract": ["contract", "agreement", "deal"],
            "lease": ["lease", "rental agreement"],
            "employment_record": ["pay stub", "paycheck", "employment record", "timesheet"],
            "court_document": ["court document", "summons", "subpoena", "order"],
            "identification": ["id", "identification", "driver's license", "passport"]
        }
        
        for doc_type, keywords in document_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    documents.append(doc_type)
                    break
                    
        return list(set(documents))  # Remove duplicates


# Factory function for creating the legal guidance engine
def create_legal_guidance_engine() -> LegalGuidanceEngine:
    """Create and return a legal guidance engine instance."""
    return BasicLegalGuidanceEngine()