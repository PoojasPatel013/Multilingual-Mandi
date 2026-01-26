/**
 * Legal Processing Interfaces
 * Components for legal guidance, issue classification, and conversation management
 */

import {
  LegalIssueType,
  LegalIssue,
  LegalGuidance,
  LegalCitation,
  ComplexityLevel,
  UserContext,
  SessionId,
  SystemResponse,
  ConversationContext,
  ConversationSummary,
} from '../types';

/**
 * Legal Guidance Engine Interface
 * Processes legal queries and provides appropriate guidance
 */
export interface LegalGuidanceEngine {
  /**
   * Classify a legal query into a specific issue type
   * @param query - User's legal query text
   * @returns Promise resolving to classified legal issue type
   */
  classifyLegalIssue(query: string): Promise<LegalIssueType>;

  /**
   * Generate legal guidance for a specific issue and user context
   * @param issue - Classified legal issue
   * @param context - User context and situation details
   * @returns Promise resolving to comprehensive legal guidance
   */
  generateGuidance(issue: LegalIssue, context: UserContext): Promise<LegalGuidance>;

  /**
   * Assess the complexity level of a legal issue
   * @param issue - Legal issue to assess
   * @returns Promise resolving to complexity assessment
   */
  assessComplexity(issue: LegalIssue): Promise<ComplexityLevel>;

  /**
   * Get relevant legal citations for an issue
   * @param issue - Legal issue requiring citations
   * @returns Promise resolving to array of relevant legal citations
   */
  getCitations(issue: LegalIssue): Promise<LegalCitation[]>;

  /**
   * Determine if an issue requires immediate professional help
   * @param issue - Legal issue to evaluate
   * @returns Promise resolving to boolean indicating urgency
   */
  requiresImmediateProfessionalHelp(issue: LegalIssue): Promise<boolean>;
}

/**
 * Conversation Engine Interface
 * Orchestrates conversation flow and manages dialogue state
 */
export interface ConversationEngine {
  /**
   * Process user input and generate appropriate system response
   * @param sessionId - Current session identifier
   * @param input - User's text input
   * @returns Promise resolving to system response
   */
  processUserInput(sessionId: SessionId, input: string): Promise<SystemResponse>;

  /**
   * Generate relevant follow-up questions based on conversation context
   * @param context - Current conversation context
   * @returns Promise resolving to array of follow-up questions
   */
  generateFollowUpQuestions(context: ConversationContext): Promise<string[]>;

  /**
   * Create a summary of the conversation for the user
   * @param sessionId - Session to summarize
   * @returns Promise resolving to conversation summary
   */
  summarizeConversation(sessionId: SessionId): Promise<ConversationSummary>;

  /**
   * Determine if the conversation should be ended
   * @param context - Current conversation context
   * @returns Boolean indicating if conversation should end
   */
  shouldEndConversation(context: ConversationContext): boolean;

  /**
   * Handle unclear or ambiguous user input
   * @param input - Unclear user input
   * @param context - Conversation context
   * @returns Promise resolving to clarification questions
   */
  handleUnclearInput(input: string, context: ConversationContext): Promise<string[]>;
}