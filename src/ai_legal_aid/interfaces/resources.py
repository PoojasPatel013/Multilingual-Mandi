"""
Resource management protocols for the AI Legal Aid System.

This module defines the contract for managing legal aid organizations,
resource directories, and referral generation.
"""

from abc import abstractmethod
from typing import List, Protocol

from ai_legal_aid.types import (
    LegalIssueType,
    Location,
    LegalAidOrganization,
    SearchCriteria,
)


class ResourceDirectory(Protocol):
    """Protocol for managing legal aid organizations and resource referrals."""

    @abstractmethod
    async def find_organizations(
        self, criteria: SearchCriteria
    ) -> List[LegalAidOrganization]:
        """
        Find legal aid organizations matching search criteria.

        Args:
            criteria: Search criteria including location, issue type, etc.

        Returns:
            List of matching legal aid organizations
        """
        ...

    @abstractmethod
    async def get_organization_details(self, org_id: str) -> LegalAidOrganization:
        """
        Get detailed information about a specific organization.

        Args:
            org_id: Unique organization identifier

        Returns:
            Detailed organization information

        Raises:
            OrganizationNotFoundError: If organization doesn't exist
        """
        ...

    @abstractmethod
    async def update_organization_info(self, org_id: str, updates: dict) -> None:
        """
        Update organization information.

        Args:
            org_id: Unique organization identifier
            updates: Dictionary of fields to update

        Raises:
            OrganizationNotFoundError: If organization doesn't exist
        """
        ...

    @abstractmethod
    async def search_by_specialization(
        self, issue_type: LegalIssueType, location: Location
    ) -> List[LegalAidOrganization]:
        """
        Search for organizations by legal issue specialization and location.

        Args:
            issue_type: Type of legal issue
            location: Geographic location

        Returns:
            List of organizations specializing in the issue type
        """
        ...
