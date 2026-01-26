"""
Resource Directory implementation for the AI Legal Aid System.

This module provides functionality for managing legal aid organizations,
searching for resources, and generating referrals based on user needs.
"""

import math
from typing import Dict, List, Optional

from ai_legal_aid.interfaces.resources import ResourceDirectory
from ai_legal_aid.types import (
    LegalIssueType,
    Location,
    LegalAidOrganization,
    SearchCriteria,
    ContactInfo,
    Address,
    OperatingHours,
    GeographicArea,
    ContactMethod,
    ResourceReferral,
)


class OrganizationNotFoundError(Exception):
    """Raised when a requested organization is not found."""
    pass


class BasicResourceDirectory:
    """
    Basic implementation of the Resource Directory.
    
    This implementation provides in-memory storage and search functionality
    for legal aid organizations with geographic and specialization-based matching.
    """

    def __init__(self):
        """Initialize the resource directory with sample organizations."""
        self._organizations: Dict[str, LegalAidOrganization] = {}
        self._initialize_sample_organizations()

    def _initialize_sample_organizations(self):
        """Initialize the directory with sample legal aid organizations."""
        
        # Sample organizations covering different specializations and locations
        sample_orgs = [
            {
                "id": "legal_aid_society_la",
                "name": "Legal Aid Society of Los Angeles",
                "contact_info": ContactInfo(
                    phone="(213) 555-0123",
                    email="intake@lasla.org",
                    address=Address(
                        street="1234 Main St",
                        city="Los Angeles",
                        state="CA",
                        zip_code="90012"
                    ),
                    website="https://www.lasla.org",
                    intake_hours=OperatingHours(
                        monday={"open": "9:00 AM", "close": "5:00 PM"},
                        tuesday={"open": "9:00 AM", "close": "5:00 PM"},
                        wednesday={"open": "9:00 AM", "close": "5:00 PM"},
                        thursday={"open": "9:00 AM", "close": "5:00 PM"},
                        friday={"open": "9:00 AM", "close": "3:00 PM"}
                    )
                ),
                "specializations": [
                    LegalIssueType.TENANT_RIGHTS,
                    LegalIssueType.WAGE_THEFT,
                    LegalIssueType.DOMESTIC_VIOLENCE
                ],
                "service_area": GeographicArea(
                    states=["CA"],
                    counties=["Los Angeles"],
                    zip_codes=["90001", "90002", "90012", "90013", "90014"]
                ),
                "languages": ["en", "es"],
                "availability": OperatingHours(
                    monday={"open": "8:00 AM", "close": "6:00 PM"},
                    tuesday={"open": "8:00 AM", "close": "6:00 PM"},
                    wednesday={"open": "8:00 AM", "close": "6:00 PM"},
                    thursday={"open": "8:00 AM", "close": "6:00 PM"},
                    friday={"open": "8:00 AM", "close": "4:00 PM"}
                ),
                "eligibility_requirements": [
                    "Income below 125% of Federal Poverty Level",
                    "Resident of Los Angeles County"
                ]
            },
            {
                "id": "domestic_violence_center_ca",
                "name": "California Domestic Violence Legal Center",
                "contact_info": ContactInfo(
                    phone="(800) 555-0199",
                    email="help@dvlegal-ca.org",
                    address=Address(
                        street="5678 Safety Blvd",
                        city="San Francisco",
                        state="CA",
                        zip_code="94102"
                    ),
                    website="https://www.dvlegal-ca.org",
                    intake_hours=OperatingHours(
                        monday={"open": "24 hours", "close": "24 hours"},
                        tuesday={"open": "24 hours", "close": "24 hours"},
                        wednesday={"open": "24 hours", "close": "24 hours"},
                        thursday={"open": "24 hours", "close": "24 hours"},
                        friday={"open": "24 hours", "close": "24 hours"},
                        saturday={"open": "24 hours", "close": "24 hours"},
                        sunday={"open": "24 hours", "close": "24 hours"}
                    )
                ),
                "specializations": [LegalIssueType.DOMESTIC_VIOLENCE],
                "service_area": GeographicArea(
                    states=["CA"],
                    counties=["Los Angeles", "San Francisco", "Orange", "San Diego"]
                ),
                "languages": ["en", "es"],
                "availability": OperatingHours(
                    monday={"open": "24 hours", "close": "24 hours"},
                    tuesday={"open": "24 hours", "close": "24 hours"},
                    wednesday={"open": "24 hours", "close": "24 hours"},
                    thursday={"open": "24 hours", "close": "24 hours"},
                    friday={"open": "24 hours", "close": "24 hours"},
                    saturday={"open": "24 hours", "close": "24 hours"},
                    sunday={"open": "24 hours", "close": "24 hours"}
                ),
                "eligibility_requirements": [
                    "Victim of domestic violence",
                    "California resident"
                ]
            },
            {
                "id": "housing_rights_center",
                "name": "Housing Rights Center",
                "contact_info": ContactInfo(
                    phone="(213) 555-0156",
                    email="info@housingrights.org",
                    address=Address(
                        street="9876 Tenant Ave",
                        city="Los Angeles",
                        state="CA",
                        zip_code="90015"
                    ),
                    website="https://www.housingrights.org",
                    intake_hours=OperatingHours(
                        monday={"open": "9:00 AM", "close": "5:00 PM"},
                        tuesday={"open": "9:00 AM", "close": "5:00 PM"},
                        wednesday={"open": "9:00 AM", "close": "5:00 PM"},
                        thursday={"open": "9:00 AM", "close": "5:00 PM"},
                        friday={"open": "9:00 AM", "close": "5:00 PM"}
                    )
                ),
                "specializations": [
                    LegalIssueType.TENANT_RIGHTS,
                    LegalIssueType.LAND_DISPUTE
                ],
                "service_area": GeographicArea(
                    states=["CA"],
                    counties=["Los Angeles", "Orange", "Ventura"]
                ),
                "languages": ["en", "es", "ko"],
                "availability": OperatingHours(
                    monday={"open": "9:00 AM", "close": "5:00 PM"},
                    tuesday={"open": "9:00 AM", "close": "5:00 PM"},
                    wednesday={"open": "9:00 AM", "close": "5:00 PM"},
                    thursday={"open": "9:00 AM", "close": "5:00 PM"},
                    friday={"open": "9:00 AM", "close": "5:00 PM"}
                ),
                "eligibility_requirements": [
                    "Low to moderate income",
                    "Housing-related legal issue"
                ]
            },
            {
                "id": "workers_rights_legal_clinic",
                "name": "Workers' Rights Legal Clinic",
                "contact_info": ContactInfo(
                    phone="(213) 555-0178",
                    email="intake@workersrights.org",
                    address=Address(
                        street="4321 Labor St",
                        city="Los Angeles",
                        state="CA",
                        zip_code="90017"
                    ),
                    website="https://www.workersrights.org",
                    intake_hours=OperatingHours(
                        monday={"open": "8:00 AM", "close": "6:00 PM"},
                        tuesday={"open": "8:00 AM", "close": "6:00 PM"},
                        wednesday={"open": "8:00 AM", "close": "6:00 PM"},
                        thursday={"open": "8:00 AM", "close": "6:00 PM"},
                        friday={"open": "8:00 AM", "close": "4:00 PM"}
                    )
                ),
                "specializations": [LegalIssueType.WAGE_THEFT],
                "service_area": GeographicArea(
                    states=["CA"],
                    counties=["Los Angeles", "Orange", "Riverside", "San Bernardino"]
                ),
                "languages": ["en", "es"],
                "availability": OperatingHours(
                    monday={"open": "8:00 AM", "close": "6:00 PM"},
                    tuesday={"open": "8:00 AM", "close": "6:00 PM"},
                    wednesday={"open": "8:00 AM", "close": "6:00 PM"},
                    thursday={"open": "8:00 AM", "close": "6:00 PM"},
                    friday={"open": "8:00 AM", "close": "4:00 PM"}
                ),
                "eligibility_requirements": [
                    "Low-wage worker",
                    "Employment-related legal issue"
                ]
            },
            {
                "id": "national_domestic_violence_hotline",
                "name": "National Domestic Violence Hotline",
                "contact_info": ContactInfo(
                    phone="1-800-799-7233",
                    email="info@thehotline.org",
                    address=Address(
                        street="P.O. Box 161810",
                        city="Austin",
                        state="TX",
                        zip_code="78716"
                    ),
                    website="https://www.thehotline.org",
                    intake_hours=OperatingHours(
                        monday={"open": "24 hours", "close": "24 hours"},
                        tuesday={"open": "24 hours", "close": "24 hours"},
                        wednesday={"open": "24 hours", "close": "24 hours"},
                        thursday={"open": "24 hours", "close": "24 hours"},
                        friday={"open": "24 hours", "close": "24 hours"},
                        saturday={"open": "24 hours", "close": "24 hours"},
                        sunday={"open": "24 hours", "close": "24 hours"}
                    )
                ),
                "specializations": [LegalIssueType.DOMESTIC_VIOLENCE],
                "service_area": GeographicArea(
                    states=["ALL"],  # National coverage
                    counties=[]
                ),
                "languages": ["en", "es"],
                "availability": OperatingHours(
                    monday={"open": "24 hours", "close": "24 hours"},
                    tuesday={"open": "24 hours", "close": "24 hours"},
                    wednesday={"open": "24 hours", "close": "24 hours"},
                    thursday={"open": "24 hours", "close": "24 hours"},
                    friday={"open": "24 hours", "close": "24 hours"},
                    saturday={"open": "24 hours", "close": "24 hours"},
                    sunday={"open": "24 hours", "close": "24 hours"}
                ),
                "eligibility_requirements": [
                    "Anyone affected by domestic violence"
                ]
            }
        ]

        # Convert sample data to LegalAidOrganization objects and store
        for org_data in sample_orgs:
            org = LegalAidOrganization(**org_data)
            self._organizations[org.id] = org

    async def find_organizations(
        self, criteria: SearchCriteria
    ) -> List[LegalAidOrganization]:
        """
        Find legal aid organizations matching search criteria.
        
        Searches based on location, issue type, language, and urgency.
        """
        matching_orgs = []
        
        for org in self._organizations.values():
            if self._matches_criteria(org, criteria):
                matching_orgs.append(org)
        
        # Sort by relevance (specialization match, then geographic proximity)
        matching_orgs.sort(
            key=lambda org: self._calculate_relevance_score(org, criteria),
            reverse=True
        )
        
        return matching_orgs

    async def get_organization_details(self, org_id: str) -> LegalAidOrganization:
        """Get detailed information about a specific organization."""
        if org_id not in self._organizations:
            raise OrganizationNotFoundError(f"Organization with ID '{org_id}' not found")
        
        return self._organizations[org_id]

    async def update_organization_info(self, org_id: str, updates: dict) -> None:
        """Update organization information."""
        if org_id not in self._organizations:
            raise OrganizationNotFoundError(f"Organization with ID '{org_id}' not found")
        
        org = self._organizations[org_id]
        
        # Update fields that are provided
        for field, value in updates.items():
            if hasattr(org, field):
                setattr(org, field, value)

    async def search_by_specialization(
        self, issue_type: LegalIssueType, location: Location
    ) -> List[LegalAidOrganization]:
        """Search for organizations by legal issue specialization and location."""
        criteria = SearchCriteria(
            location=location,
            issue_type=issue_type
        )
        
        return await self.find_organizations(criteria)

    def _matches_criteria(self, org: LegalAidOrganization, criteria: SearchCriteria) -> bool:
        """Check if an organization matches the search criteria."""
        
        # Check issue type specialization
        if criteria.issue_type and criteria.issue_type not in org.specializations:
            return False
        
        # Check language support
        if criteria.language and criteria.language not in org.languages:
            return False
        
        # Check geographic coverage
        if criteria.location:
            if not self._serves_location(org, criteria.location):
                return False
        
        return True

    def _serves_location(self, org: LegalAidOrganization, location: Location) -> bool:
        """Check if an organization serves a specific location."""
        service_area = org.service_area
        
        # Check if organization serves all states (national coverage)
        if "ALL" in service_area.states:
            return True
        
        # Check state coverage
        if location.state not in service_area.states:
            return False
        
        # If counties are specified, check county coverage
        if service_area.counties and location.county:
            if location.county not in service_area.counties:
                return False
        
        # If ZIP codes are specified, check ZIP code coverage
        if service_area.zip_codes and location.zip_code:
            if location.zip_code not in service_area.zip_codes:
                return False
        
        return True

    def _calculate_relevance_score(
        self, org: LegalAidOrganization, criteria: SearchCriteria
    ) -> float:
        """Calculate relevance score for ranking organizations."""
        score = 0.0
        
        # Specialization match (highest priority)
        if criteria.issue_type and criteria.issue_type in org.specializations:
            score += 10.0
            
            # Bonus for organizations that specialize only in this issue type
            if len(org.specializations) == 1:
                score += 5.0
        
        # Language match
        if criteria.language and criteria.language in org.languages:
            score += 3.0
        
        # Geographic proximity (simplified - could be enhanced with actual distance calculation)
        if criteria.location:
            if self._serves_location(org, criteria.location):
                score += 2.0
                
                # Bonus for local organizations
                if criteria.location.county and org.service_area.counties:
                    if criteria.location.county in org.service_area.counties:
                        score += 3.0
        
        # Urgency considerations
        if criteria.urgency:
            # 24-hour availability for urgent cases
            if self._has_24_hour_availability(org):
                score += 2.0
        
        return score

    def _has_24_hour_availability(self, org: LegalAidOrganization) -> bool:
        """Check if organization has 24-hour availability."""
        hours = org.availability
        
        # Check if any day has 24-hour availability
        for day_hours in [hours.monday, hours.tuesday, hours.wednesday, 
                         hours.thursday, hours.friday, hours.saturday, hours.sunday]:
            if day_hours and day_hours.get("open") == "24 hours":
                return True
        
        return False

    async def generate_referrals(
        self, criteria: SearchCriteria, max_referrals: int = 3
    ) -> List[ResourceReferral]:
        """
        Generate resource referrals based on search criteria.
        
        Returns a list of ResourceReferral objects with recommended next steps.
        """
        organizations = await self.find_organizations(criteria)
        referrals = []
        
        for org in organizations[:max_referrals]:
            relevance_score = self._calculate_relevance_score(org, criteria)
            
            # Determine recommended contact method
            contact_method = self._get_recommended_contact_method(org, criteria)
            
            # Generate next steps
            next_steps = self._generate_next_steps(org, criteria)
            
            # Estimate wait time
            wait_time = self._estimate_wait_time(org, criteria)
            
            referral = ResourceReferral(
                organization=org,
                relevance_score=min(relevance_score / 20.0, 1.0),  # Normalize to 0-1
                contact_method=contact_method,
                next_steps=next_steps,
                estimated_wait_time=wait_time
            )
            
            referrals.append(referral)
        
        return referrals

    def _get_recommended_contact_method(
        self, org: LegalAidOrganization, criteria: SearchCriteria
    ) -> ContactMethod:
        """Determine the best contact method for an organization."""
        
        # For urgent cases, recommend phone
        if criteria.urgency and criteria.urgency.value in ["high", "emergency"]:
            return ContactMethod.PHONE
        
        # For domestic violence, recommend phone for safety
        if criteria.issue_type == LegalIssueType.DOMESTIC_VIOLENCE:
            return ContactMethod.PHONE
        
        # Default to phone for most cases
        return ContactMethod.PHONE

    def _generate_next_steps(
        self, org: LegalAidOrganization, criteria: SearchCriteria
    ) -> List[str]:
        """Generate recommended next steps for contacting an organization."""
        steps = []
        
        # Basic contact step
        steps.append(f"Call {org.contact_info.phone} during intake hours")
        
        # Preparation steps
        steps.append("Gather relevant documents and information about your situation")
        
        # Eligibility check
        if org.eligibility_requirements:
            steps.append("Review eligibility requirements before calling")
        
        # Language considerations
        if criteria.language and criteria.language in org.languages:
            if criteria.language != "en":
                steps.append(f"Services available in your preferred language")
        
        # Urgency-specific steps
        if criteria.urgency and criteria.urgency.value == "emergency":
            steps.insert(0, "This is an emergency resource - call immediately")
        
        return steps

    def _estimate_wait_time(
        self, org: LegalAidOrganization, criteria: SearchCriteria
    ) -> Optional[str]:
        """Estimate wait time for services."""
        
        # Emergency services
        if criteria.urgency and criteria.urgency.value == "emergency":
            if self._has_24_hour_availability(org):
                return "Immediate assistance available"
            else:
                return "Call during business hours for urgent assistance"
        
        # General estimates based on organization type
        if org.specializations == [LegalIssueType.DOMESTIC_VIOLENCE]:
            return "Usually same-day response for safety planning"
        
        return "Typically 1-2 weeks for initial consultation"


# Factory function for creating the resource directory
def create_resource_directory() -> ResourceDirectory:
    """Create and return a resource directory instance."""
    return BasicResourceDirectory()