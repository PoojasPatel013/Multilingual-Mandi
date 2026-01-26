/**
 * Session Management Interface
 * Handles user sessions, conversation state, and data privacy
 */

import { SessionId, Session } from '../types';

/**
 * Session Manager Interface
 * Manages user sessions with privacy-compliant data handling
 */
export interface SessionManager {
  /**
   * Create a new user session
   * @returns Promise resolving to new session ID
   */
  createSession(): Promise<SessionId>;

  /**
   * Retrieve an existing session by ID
   * @param sessionId - Unique session identifier
   * @returns Promise resolving to session data or null if not found
   */
  getSession(sessionId: SessionId): Promise<Session | null>;

  /**
   * Update session data with partial updates
   * @param sessionId - Unique session identifier
   * @param updates - Partial session data to update
   */
  updateSession(sessionId: SessionId, updates: Partial<Session>): Promise<void>;

  /**
   * End a session and perform cleanup
   * @param sessionId - Unique session identifier
   */
  endSession(sessionId: SessionId): Promise<void>;

  /**
   * Clean up expired sessions (privacy compliance)
   * @returns Promise resolving to number of sessions cleaned up
   */
  cleanupExpiredSessions(): Promise<number>;

  /**
   * Check if a session exists and is active
   * @param sessionId - Unique session identifier
   * @returns Promise resolving to boolean indicating session validity
   */
  isSessionActive(sessionId: SessionId): Promise<boolean>;

  /**
   * Get session statistics for monitoring
   * @returns Promise resolving to session statistics
   */
  getSessionStats(): Promise<{
    activeSessions: number;
    totalSessions: number;
    averageSessionDuration: number;
  }>;
}