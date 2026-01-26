"""
Data models for the AI Legal Aid System.

This module contains all the Pydantic models that define the structure
of data used throughout the system. These models provide validation,
serialization, and type safety for all system components.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from ai_legal_aid.types.base import (
    SessionId,
    LegalIssueType,
    UrgencyLevel,
    ComplexityLevel,
    ContactMethod,
    DocumentType,
    IncomeRange,
)


class Location(BaseModel):
    """Geographic location information."""

    state: str = Field(..., description="State or province")
    county: Optional[str] = Field(None, description="County or region")
    zip_code: Optional[str] = Field(None, description="ZIP or postal code")
    coordinates: Optional[Dict[str, float]] = Field(
        None, description="Latitude and longitude coordinates"
    )

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, v):
        if v is not None:
            if "latitude" not in v or "longitude" not in v:
                raise ValueError("Coordinates must include latitude and longitude")
            if not (-90 <= v["latitude"] <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= v["longitude"] <= 180):
                raise ValueError("Longitude must be between -180 and 180")
        return v


class GeographicArea(BaseModel):
    """Geographic service area for legal aid organizations."""

    states: List[str] = Field(..., description="States served")
    counties: Optional[List[str]] = Field(None, description="Counties served")
    zip_codes: Optional[List[str]] = Field(None, description="ZIP codes served")
    radius: Optional[float] = Field(None, description="Service radius in miles")


class UserContext(BaseModel):
    """Context information about the user and their situation."""

    location: Optional[Location] = None
    preferred_language: str = Field(
        default="en", description="User's preferred language"
    )
    legal_issue_type: Optional[LegalIssueType] = None
    urgency_level: Optional[UrgencyLevel] = None
    has_minor_children: Optional[bool] = None
    household_income: Optional[IncomeRange] = None


class LegalIssue(BaseModel):
    """Representation of a legal issue presented by the user."""

    type: LegalIssueType
    description: str = Field(..., description="User's description of the issue")
    urgency: UrgencyLevel
    complexity: ComplexityLevel
    involved_parties: List[str] = Field(default_factory=list)
    timeframe: Optional[str] = Field(None, description="When the issue occurred")
    documents: Optional[List[DocumentType]] = Field(default_factory=list)


class LegalGuidance(BaseModel):
    """Legal guidance provided by the system."""

    summary: str = Field(..., description="Brief summary of the guidance")
    detailed_steps: List[str] = Field(..., description="Step-by-step guidance")
    urgency_level: UrgencyLevel
    recommends_professional_help: bool = Field(
        ..., description="Whether professional legal help is recommended"
    )
    applicable_laws: List[str] = Field(
        default_factory=list, description="Relevant laws and regulations"
    )


class LegalCitation(BaseModel):
    """Citation to a legal authority or resource."""

    title: str = Field(..., description="Title of the legal authority")
    section: Optional[str] = Field(None, description="Specific section or subsection")
    jurisdiction: str = Field(..., description="Legal jurisdiction")
    url: Optional[str] = Field(None, description="URL to the resource")
    summary: str = Field(..., description="Brief summary of relevance")


class OperatingHours(BaseModel):
    """Operating hours for an organization."""

    monday: Optional[Dict[str, str]] = None
    tuesday: Optional[Dict[str, str]] = None
    wednesday: Optional[Dict[str, str]] = None
    thursday: Optional[Dict[str, str]] = None
    friday: Optional[Dict[str, str]] = None
    saturday: Optional[Dict[str, str]] = None
    sunday: Optional[Dict[str, str]] = None
    notes: Optional[str] = None

    @field_validator(
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
    )
    @classmethod
    def validate_hours(cls, v):
        if v is not None:
            if "open" not in v or "close" not in v:
                raise ValueError("Hours must include 'open' and 'close' times")
        return v


class Address(BaseModel):
    """Physical address information."""

    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State or province")
    zip_code: str = Field(..., description="ZIP or postal code")
    country: str = Field(default="US", description="Country")


class ContactInfo(BaseModel):
    """Contact information for legal aid organizations."""

    phone: str = Field(..., description="Primary phone number")
    email: Optional[str] = Field(None, description="Email address")
    address: Address = Field(..., description="Physical address")
    website: Optional[str] = Field(None, description="Website URL")
    intake_hours: OperatingHours = Field(
        ..., description="Hours for intake/consultation"
    )


class LegalAidOrganization(BaseModel):
    """Legal aid organization information."""

    id: str = Field(..., description="Unique organization identifier")
    name: str = Field(..., description="Organization name")
    contact_info: ContactInfo = Field(..., description="Contact information")
    specializations: List[LegalIssueType] = Field(
        ..., description="Legal issue types the organization handles"
    )
    service_area: GeographicArea = Field(..., description="Geographic area served")
    languages: List[str] = Field(..., description="Languages supported")
    availability: OperatingHours = Field(..., description="General operating hours")
    eligibility_requirements: List[str] = Field(
        default_factory=list, description="Eligibility requirements for services"
    )


class ResourceReferral(BaseModel):
    """Referral to a legal aid organization."""

    organization: LegalAidOrganization
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Relevance score (0-1)"
    )
    contact_method: ContactMethod = Field(..., description="Recommended contact method")
    next_steps: List[str] = Field(..., description="Recommended next steps")
    estimated_wait_time: Optional[str] = Field(
        None, description="Estimated wait time for services"
    )


class SearchCriteria(BaseModel):
    """Criteria for searching legal aid organizations."""

    location: Optional[Location] = None
    issue_type: Optional[LegalIssueType] = None
    language: Optional[str] = None
    urgency: Optional[UrgencyLevel] = None
    max_distance: Optional[float] = Field(None, description="Maximum distance in miles")


class Action(BaseModel):
    """System-suggested action for the user."""

    type: str = Field(..., description="Action type")
    description: str = Field(..., description="Human-readable description")
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Action parameters"
    )


class SystemResponse(BaseModel):
    """Response from the system to user input."""

    text: str = Field(..., description="Response text")
    requires_disclaimer: bool = Field(
        ..., description="Whether a disclaimer should be shown"
    )
    suggested_actions: List[Action] = Field(
        default_factory=list, description="Suggested actions for the user"
    )
    resources: List[ResourceReferral] = Field(
        default_factory=list, description="Resource referrals"
    )
    follow_up_questions: Optional[List[str]] = Field(
        None, description="Follow-up questions to ask the user"
    )


class ConversationTurn(BaseModel):
    """Single turn in a conversation."""

    timestamp: datetime = Field(default_factory=datetime.now)
    user_input: str = Field(..., description="User's input")
    system_response: SystemResponse = Field(..., description="System's response")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    disclaimer_shown: bool = Field(
        default=False, description="Whether disclaimer was shown"
    )


class Session(BaseModel):
    """User session information."""

    id: SessionId = Field(..., description="Unique session identifier")
    start_time: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    language: str = Field(default="en", description="Session language")
    conversation_history: List[ConversationTurn] = Field(
        default_factory=list, description="Conversation history"
    )
    user_context: UserContext = Field(
        default_factory=UserContext, description="User context information"
    )
    disclaimer_acknowledged: bool = Field(
        default=False, description="Whether user acknowledged disclaimer"
    )


class ConversationContext(BaseModel):
    """Context for the current conversation state."""

    session: Session = Field(..., description="Current session")
    current_turn: int = Field(..., description="Current conversation turn number")
    last_user_input: str = Field(..., description="Last user input")
    pending_questions: List[str] = Field(
        default_factory=list, description="Questions waiting for user response"
    )
    conversation_length: int = Field(
        ..., description="Total number of conversation turns"
    )


class ConversationSummary(BaseModel):
    """Summary of a completed conversation."""

    session_id: SessionId = Field(..., description="Session identifier")
    duration: float = Field(..., description="Duration in minutes")
    issues_discussed: List[LegalIssueType] = Field(
        ..., description="Legal issues discussed"
    )
    resources_provided: List[ResourceReferral] = Field(
        ..., description="Resources provided to user"
    )
    next_steps: List[str] = Field(..., description="Recommended next steps")
    disclaimers_shown: List[str] = Field(
        ..., description="Disclaimers shown during conversation"
    )


class SpeechError(BaseModel):
    """Error in speech processing."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    recoverable: bool = Field(..., description="Whether error is recoverable")


class AudioBuffer(BaseModel):
    """Audio data buffer."""

    data: bytes = Field(..., description="Audio data")
    format: str = Field(..., description="Audio format")
    sample_rate: int = Field(..., description="Sample rate in Hz")
    channels: int = Field(..., description="Number of audio channels")


class AuditRecord(BaseModel):
    """Audit record for compliance tracking."""

    session_id: SessionId = Field(..., description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.now)
    action: str = Field(..., description="Action performed")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Additional details"
    )
    compliance_flags: List[str] = Field(
        default_factory=list, description="Compliance-related flags"
    )


class SystemError(BaseModel):
    """System error information."""

    code: str = Field(..., description="Error code")
    component: str = Field(..., description="Component where error occurred")
    message: str = Field(..., description="Error message")
    recoverable: bool = Field(..., description="Whether error is recoverable")
    user_message: Optional[str] = Field(None, description="User-friendly error message")
