"""
Legal processing protocols for the AI Legal Aid System.

This module defines the contracts for legal guidance generation,
conversation management, and legal issue classification.
"""

from abc import abstractmethod
from typing import List, Protocol

from ai_legal_aid.types import (
    SessionId,
    LegalIssueType,
    ComplexityLevel,
    LegalIssue,
    LegalGuidance,
    LegalCitation,
    UserContext,
    SystemResponse,
    ConversationContext,
    ConversationSummary,
)


class LegalGuidanceEngine(Protocol):
    """Protocol for legal guidance generation and issue processing."""

    @abstractmethod
    async def classify_legal_issue(self, query: str) -> LegalIssueType:
        """
        Classify a legal query into a specific issue type.

        Args:
            query: User's description of their legal issue

        Returns:
            Classified legal issue type
        """
        ...

    @abstractmethod
    async def generate_guidance(
        self, issue: LegalIssue, context: UserContext
    ) -> LegalGuidance:
        """
        Generate legal guidance for a specific issue.

        Args:
            issue: Legal issue to provide guidance for
            context: User context information

        Returns:
            Generated legal guidance
        """
        ...

    @abstractmethod
    async def assess_complexity(self, issue: LegalIssue) -> ComplexityLevel:
        """
        Assess the complexity level of a legal issue.

        Args:
            issue: Legal issue to assess

        Returns:
            Complexity level assessment
        """
        ...

    @abstractmethod
    async def get_citations(self, issue: LegalIssue) -> List[LegalCitation]:
        """
        Get relevant legal citations for an issue.

        Args:
            issue: Legal issue to find citations for

        Returns:
            List of relevant legal citations
        """
        ...


class ConversationEngine(Protocol):
    """Protocol for conversation flow management and dialogue state tracking."""

    @abstractmethod
    async def process_user_input(
        self, session_id: SessionId, input_text: str
    ) -> SystemResponse:
        """
        Process user input and generate appropriate system response.

        Args:
            session_id: Current session identifier
            input_text: User's input text

        Returns:
            System response including guidance, actions, and resources
        """
        ...

    @abstractmethod
    async def generate_follow_up_questions(
        self, context: ConversationContext
    ) -> List[str]:
        """
        Generate relevant follow-up questions based on conversation context.

        Args:
            context: Current conversation context

        Returns:
            List of follow-up questions to ask the user
        """
        ...

    @abstractmethod
    async def summarize_conversation(
        self, session_id: SessionId
    ) -> ConversationSummary:
        """
        Generate a summary of the conversation.

        Args:
            session_id: Session to summarize

        Returns:
            Conversation summary including key points and next steps
        """
        ...

    @abstractmethod
    def should_end_conversation(self, context: ConversationContext) -> bool:
        """
        Determine if the conversation should be ended.

        Args:
            context: Current conversation context

        Returns:
            True if conversation should end, False otherwise
        """
        ...
