/**
 * Core type definitions for the AI Legal Aid System
 * Based on the design document interfaces and data models
 */

// Basic type aliases
export type SessionId = string;

// Enums for legal issue classification
export enum LegalIssueType {
  LAND_DISPUTE = 'land_dispute',
  DOMESTIC_VIOLENCE = 'domestic_violence',
  WAGE_THEFT = 'wage_theft',
  TENANT_RIGHTS = 'tenant_rights',
  OTHER = 'other',
}

export enum UrgencyLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  EMERGENCY = 'emergency',
}

export enum ComplexityLevel {
  SIMPLE = 'simple',
  MODERATE = 'moderate',
  COMPLEX = 'complex',
}

export enum ContactMethod {
  PHONE = 'phone',
  EMAIL = 'email',
  WALK_IN = 'walk_in',
  ONLINE = 'online',
}

export enum DocumentType {
  CONTRACT = 'contract',
  LEASE = 'lease',
  EMPLOYMENT_RECORD = 'employment_record',
  COURT_DOCUMENT = 'court_document',
  IDENTIFICATION = 'identification',
  OTHER = 'other',
}

export enum IncomeRange {
  VERY_LOW = 'very_low', // Below 30% AMI
  LOW = 'low', // 30-50% AMI
  MODERATE = 'moderate', // 50-80% AMI
  ABOVE_MODERATE = 'above_moderate', // Above 80% AMI
}

// Location and geographic data
export interface Location {
  state: string;
  county?: string;
  zipCode?: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
}

export interface GeographicArea {
  states: string[];
  counties?: string[];
  zipCodes?: string[];
  radius?: number; // in miles
}

// User context and session data
export interface UserContext {
  location?: Location;
  preferredLanguage: string;
  legalIssueType?: LegalIssueType;
  urgencyLevel?: UrgencyLevel;
  hasMinorChildren?: boolean;
  householdIncome?: IncomeRange;
}

// Legal issue modeling
export interface LegalIssue {
  type: LegalIssueType;
  description: string;
  urgency: UrgencyLevel;
  complexity: ComplexityLevel;
  involvedParties: string[];
  timeframe?: string;
  documents?: DocumentType[];
}

export interface LegalGuidance {
  summary: string;
  detailedSteps: string[];
  urgencyLevel: UrgencyLevel;
  recommendsProfessionalHelp: boolean;
  applicableLaws: string[];
}

export interface LegalCitation {
  title: string;
  section?: string;
  jurisdiction: string;
  url?: string;
  summary: string;
}

// Operating hours and contact information
export interface OperatingHours {
  monday?: { open: string; close: string };
  tuesday?: { open: string; close: string };
  wednesday?: { open: string; close: string };
  thursday?: { open: string; close: string };
  friday?: { open: string; close: string };
  saturday?: { open: string; close: string };
  sunday?: { open: string; close: string };
  notes?: string;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zipCode: string;
  country?: string;
}

export interface ContactInfo {
  phone: string;
  email?: string;
  address: Address;
  website?: string;
  intakeHours: OperatingHours;
}

// Resource and organization data
export interface LegalAidOrganization {
  id: string;
  name: string;
  contactInfo: ContactInfo;
  specializations: LegalIssueType[];
  serviceArea: GeographicArea;
  languages: string[];
  availability: OperatingHours;
  eligibilityRequirements: string[];
}

export interface ResourceReferral {
  organization: LegalAidOrganization;
  relevanceScore: number;
  contactMethod: ContactMethod;
  nextSteps: string[];
  estimatedWaitTime?: string;
}

export interface SearchCriteria {
  location?: Location;
  issueType?: LegalIssueType;
  language?: string;
  urgency?: UrgencyLevel;
  maxDistance?: number; // in miles
}

// Conversation and session data
export interface ConversationTurn {
  timestamp: Date;
  userInput: string;
  systemResponse: SystemResponse;
  confidence: number;
  disclaimerShown: boolean;
}

export interface Session {
  id: SessionId;
  startTime: Date;
  lastActivity: Date;
  language: string;
  conversationHistory: ConversationTurn[];
  userContext: UserContext;
  disclaimerAcknowledged: boolean;
}

export interface ConversationContext {
  session: Session;
  currentTurn: number;
  lastUserInput: string;
  pendingQuestions: string[];
  conversationLength: number;
}

export interface ConversationSummary {
  sessionId: SessionId;
  duration: number; // in minutes
  issuesDiscussed: LegalIssueType[];
  resourcesProvided: ResourceReferral[];
  nextSteps: string[];
  disclaimersShown: string[];
}

// System responses and actions
export interface Action {
  type: string;
  description: string;
  parameters?: Record<string, unknown>;
}

export interface SystemResponse {
  text: string;
  requiresDisclaimer: boolean;
  suggestedActions: Action[];
  resources: ResourceReferral[];
  followUpQuestions?: string[];
}

// Voice interface types
export interface SpeechError {
  code: string;
  message: string;
  recoverable: boolean;
}

export interface AudioBuffer {
  data: ArrayBuffer;
  format: string;
  sampleRate: number;
  channels: number;
}

// Audit and compliance
export interface AuditRecord {
  sessionId: SessionId;
  timestamp: Date;
  action: string;
  details: Record<string, unknown>;
  complianceFlags: string[];
}

// Error types
export interface SystemError extends Error {
  code: string;
  component: string;
  recoverable: boolean;
  userMessage?: string;
}