"""
Compliance and disclaimer protocols for the AI Legal Aid System.

This module defines the contract for managing legal disclaimers,
compliance requirements, and boundary enforcement for legal advice.
"""

from abc import abstractmethod
from typing import Protocol

from ai_legal_aid.types import (
    SessionId,
    LegalIssueType,
    ConversationContext,
)


class DisclaimerService(Protocol):
    """Protocol for managing legal disclaimers and compliance requirements."""

    @abstractmethod
    async def get_initial_disclaimer(self, language: str) -> str:
        """
        Get the initial disclaimer shown to users at session start.

        Args:
            language: Language code for disclaimer text

        Returns:
            Initial disclaimer text in the specified language
        """
        ...

    @abstractmethod
    async def get_contextual_disclaimer(
        self, issue_type: LegalIssueType, language: str
    ) -> str:
        """
        Get a contextual disclaimer based on the legal issue type.

        Args:
            issue_type: Type of legal issue being discussed
            language: Language code for disclaimer text

        Returns:
            Contextual disclaimer text in the specified language
        """
        ...

    @abstractmethod
    async def record_disclaimer_acknowledgment(
        self, session_id: SessionId, disclaimer_type: str
    ) -> None:
        """
        Record that a user has acknowledged a disclaimer.

        Args:
            session_id: Current session identifier
            disclaimer_type: Type of disclaimer acknowledged
        """
        ...

    @abstractmethod
    def should_show_disclaimer(self, context: ConversationContext) -> bool:
        """
        Determine if a disclaimer should be shown based on conversation context.

        Args:
            context: Current conversation context

        Returns:
            True if disclaimer should be shown, False otherwise
        """
        ...
