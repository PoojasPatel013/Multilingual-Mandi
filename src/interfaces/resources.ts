/**
 * Resource Management Interface
 * Manages legal aid organizations and resource referrals
 */

import {
  LegalAidOrganization,
  SearchCriteria,
  LegalIssueType,
  Location,
  ResourceReferral,
} from '../types';

/**
 * Resource Directory Interface
 * Manages and queries legal aid organizations and resources
 */
export interface ResourceDirectory {
  /**
   * Find legal aid organizations based on search criteria
   * @param criteria - Search parameters including location, issue type, etc.
   * @returns Promise resolving to array of matching organizations
   */
  findOrganizations(criteria: SearchCriteria): Promise<LegalAidOrganization[]>;

  /**
   * Get detailed information about a specific organization
   * @param orgId - Unique organization identifier
   * @returns Promise resolving to organization details or null if not found
   */
  getOrganizationDetails(orgId: string): Promise<LegalAidOrganization | null>;

  /**
   * Update organization information
   * @param orgId - Unique organization identifier
   * @param updates - Partial organization data to update
   */
  updateOrganizationInfo(
    orgId: string,
    updates: Partial<LegalAidOrganization>
  ): Promise<void>;

  /**
   * Search organizations by specialization and location
   * @param issueType - Type of legal issue
   * @param location - User's location
   * @returns Promise resolving to specialized organizations
   */
  searchBySpecialization(
    issueType: LegalIssueType,
    location: Location
  ): Promise<LegalAidOrganization[]>;

  /**
   * Get fallback national resources when no local resources are available
   * @param issueType - Type of legal issue
   * @param language - Preferred language
   * @returns Promise resolving to national resources and hotlines
   */
  getNationalResources(
    issueType: LegalIssueType,
    language: string
  ): Promise<LegalAidOrganization[]>;

  /**
   * Generate prioritized resource referrals for a user
   * @param criteria - Search criteria including location and issue type
   * @returns Promise resolving to prioritized resource referrals
   */
  generateReferrals(criteria: SearchCriteria): Promise<ResourceReferral[]>;

  /**
   * Validate organization contact information and availability
   * @param orgId - Organization to validate
   * @returns Promise resolving to validation results
   */
  validateOrganization(orgId: string): Promise<{
    contactValid: boolean;
    hoursValid: boolean;
    lastUpdated: Date;
  }>;
}