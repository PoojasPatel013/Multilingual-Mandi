/**
 * Disclaimer and Compliance Interface
 * Manages legal disclaimers and compliance requirements
 */

import { SessionId, LegalIssueType, ConversationContext } from '../types';

/**
 * Disclaimer Service Interface
 * Manages legal disclaimers and compliance requirements
 */
export interface DisclaimerService {
  /**
   * Get the initial disclaimer shown to new users
   * @param language - User's preferred language
   * @returns Promise resolving to initial disclaimer text
   */
  getInitialDisclaimer(language: string): Promise<string>;

  /**
   * Get contextual disclaimer based on legal issue type
   * @param issueType - Type of legal issue being discussed
   * @param language - User's preferred language
   * @returns Promise resolving to contextual disclaimer text
   */
  getContextualDisclaimer(issueType: LegalIssueType, language: string): Promise<string>;

  /**
   * Record that a user has acknowledged a disclaimer
   * @param sessionId - Current session identifier
   * @param disclaimerType - Type of disclaimer acknowledged
   */
  recordDisclaimerAcknowledgment(sessionId: SessionId, disclaimerType: string): Promise<void>;

  /**
   * Determine if a disclaimer should be shown in the current context
   * @param context - Current conversation context
   * @returns Boolean indicating if disclaimer is needed
   */
  shouldShowDisclaimer(context: ConversationContext): boolean;

  /**
   * Get disclaimer for legal advice boundary enforcement
   * @param language - User's preferred language
   * @returns Promise resolving to legal advice limitation disclaimer
   */
  getLegalAdviceBoundaryDisclaimer(language: string): Promise<string>;

  /**
   * Detect if user is requesting specific legal advice
   * @param userInput - User's input text
   * @returns Promise resolving to boolean indicating legal advice request
   */
  detectLegalAdviceRequest(userInput: string): Promise<boolean>;

  /**
   * Get professional referral recommendation text
   * @param issueComplexity - Complexity level of the legal issue
   * @param urgency - Urgency level of the situation
   * @param language - User's preferred language
   * @returns Promise resolving to referral recommendation text
   */
  getProfessionalReferralText(
    issueComplexity: string,
    urgency: string,
    language: string
  ): Promise<string>;

  /**
   * Get all disclaimers shown during a session for audit purposes
   * @param sessionId - Session to audit
   * @returns Promise resolving to array of disclaimer records
   */
  getSessionDisclaimers(sessionId: SessionId): Promise<{
    type: string;
    timestamp: Date;
    acknowledged: boolean;
  }[]>;
}