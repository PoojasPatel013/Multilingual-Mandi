/**
 * Property-based test generators for AI Legal Aid System
 * Custom generators for legal scenarios, user contexts, and system data
 */

import * as fc from 'fast-check';
import {
  LegalIssueType,
  UrgencyLevel,
  ComplexityLevel,
  ContactMethod,
  DocumentType,
  IncomeRange,
  Location,
  UserContext,
  LegalIssue,
  LegalAidOrganization,
  Session,
  SessionId,
  ConversationTurn,
  SystemResponse,
  SearchCriteria,
} from '../types';

// Basic generators for enums
export const legalIssueTypeGen = fc.constantFrom(...Object.values(LegalIssueType));
export const urgencyLevelGen = fc.constantFrom(...Object.values(UrgencyLevel));
export const complexityLevelGen = fc.constantFrom(...Object.values(ComplexityLevel));
export const contactMethodGen = fc.constantFrom(...Object.values(ContactMethod));
export const documentTypeGen = fc.constantFrom(...Object.values(DocumentType));
export const incomeRangeGen = fc.constantFrom(...Object.values(IncomeRange));

// Language generators
export const supportedLanguageGen = fc.constantFrom('en-US', 'es-ES', 'en', 'es');
export const languageCodeGen = fc.constantFrom('en-US', 'es-ES', 'fr-FR', 'de-DE');

// Geographic generators
export const stateGen = fc.constantFrom(
  'CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI',
  'NJ', 'VA', 'WA', 'AZ', 'MA', 'TN', 'IN', 'MO', 'MD', 'WI'
);

export const zipCodeGen = fc.integer({ min: 10000, max: 99999 }).map(n => n.toString());

export const locationGen = fc.record({
  state: stateGen,
  county: fc.option(fc.string({ minLength: 3, maxLength: 20 })),
  zipCode: fc.option(zipCodeGen),
  coordinates: fc.option(fc.record({
    latitude: fc.float({ min: -90, max: 90 }),
    longitude: fc.float({ min: -180, max: 180 }),
  })),
});

// User context generators
export const userContextGen = fc.record({
  location: fc.option(locationGen),
  preferredLanguage: supportedLanguageGen,
  legalIssueType: fc.option(legalIssueTypeGen),
  urgencyLevel: fc.option(urgencyLevelGen),
  hasMinorChildren: fc.option(fc.boolean()),
  householdIncome: fc.option(incomeRangeGen),
});

// Legal issue generators
export const legalIssueGen = fc.record({
  type: legalIssueTypeGen,
  description: fc.string({ minLength: 10, maxLength: 500 }),
  urgency: urgencyLevelGen,
  complexity: complexityLevelGen,
  involvedParties: fc.array(fc.string({ minLength: 2, maxLength: 50 }), { minLength: 1, maxLength: 5 }),
  timeframe: fc.option(fc.string({ minLength: 5, maxLength: 100 })),
  documents: fc.option(fc.array(documentTypeGen, { maxLength: 5 })),
});

// Session and conversation generators
export const sessionIdGen = fc.uuid();

export const conversationTurnGen = fc.record({
  timestamp: fc.date(),
  userInput: fc.string({ minLength: 1, maxLength: 1000 }),
  systemResponse: fc.record({
    text: fc.string({ minLength: 1, maxLength: 2000 }),
    requiresDisclaimer: fc.boolean(),
    suggestedActions: fc.array(fc.record({
      type: fc.string({ minLength: 1, maxLength: 50 }),
      description: fc.string({ minLength: 1, maxLength: 200 }),
      parameters: fc.option(fc.dictionary(fc.string(), fc.anything())),
    }), { maxLength: 3 }),
    resources: fc.array(fc.anything(), { maxLength: 3 }), // Simplified for now
    followUpQuestions: fc.option(fc.array(fc.string({ minLength: 5, maxLength: 200 }), { maxLength: 3 })),
  }),
  confidence: fc.float({ min: 0, max: 1 }),
  disclaimerShown: fc.boolean(),
});

export const sessionGen = fc.record({
  id: sessionIdGen,
  startTime: fc.date(),
  lastActivity: fc.date(),
  language: supportedLanguageGen,
  conversationHistory: fc.array(conversationTurnGen, { maxLength: 20 }),
  userContext: userContextGen,
  disclaimerAcknowledged: fc.boolean(),
});

// Organization generators
export const phoneGen = fc.string({ minLength: 10, maxLength: 15 })
  .filter(s => /^\+?[\d\s\-\(\)]+$/.test(s));

export const emailGen = fc.emailAddress();

export const addressGen = fc.record({
  street: fc.string({ minLength: 5, maxLength: 100 }),
  city: fc.string({ minLength: 2, maxLength: 50 }),
  state: stateGen,
  zipCode: zipCodeGen,
  country: fc.option(fc.constantFrom('US', 'USA', 'United States')),
});

export const operatingHoursGen = fc.record({
  monday: fc.option(fc.record({
    open: fc.constantFrom('08:00', '09:00', '10:00'),
    close: fc.constantFrom('16:00', '17:00', '18:00'),
  })),
  tuesday: fc.option(fc.record({
    open: fc.constantFrom('08:00', '09:00', '10:00'),
    close: fc.constantFrom('16:00', '17:00', '18:00'),
  })),
  wednesday: fc.option(fc.record({
    open: fc.constantFrom('08:00', '09:00', '10:00'),
    close: fc.constantFrom('16:00', '17:00', '18:00'),
  })),
  thursday: fc.option(fc.record({
    open: fc.constantFrom('08:00', '09:00', '10:00'),
    close: fc.constantFrom('16:00', '17:00', '18:00'),
  })),
  friday: fc.option(fc.record({
    open: fc.constantFrom('08:00', '09:00', '10:00'),
    close: fc.constantFrom('16:00', '17:00', '18:00'),
  })),
  saturday: fc.option(fc.record({
    open: fc.constantFrom('09:00', '10:00', '11:00'),
    close: fc.constantFrom('14:00', '15:00', '16:00'),
  })),
  sunday: fc.option(fc.record({
    open: fc.constantFrom('10:00', '11:00', '12:00'),
    close: fc.constantFrom('14:00', '15:00', '16:00'),
  })),
  notes: fc.option(fc.string({ maxLength: 200 })),
});

export const legalAidOrganizationGen = fc.record({
  id: fc.uuid(),
  name: fc.string({ minLength: 5, maxLength: 100 }),
  contactInfo: fc.record({
    phone: phoneGen,
    email: fc.option(emailGen),
    address: addressGen,
    website: fc.option(fc.webUrl()),
    intakeHours: operatingHoursGen,
  }),
  specializations: fc.array(legalIssueTypeGen, { minLength: 1, maxLength: 4 }),
  serviceArea: fc.record({
    states: fc.array(stateGen, { minLength: 1, maxLength: 3 }),
    counties: fc.option(fc.array(fc.string({ minLength: 3, maxLength: 30 }), { maxLength: 10 })),
    zipCodes: fc.option(fc.array(zipCodeGen, { maxLength: 20 })),
    radius: fc.option(fc.integer({ min: 5, max: 100 })),
  }),
  languages: fc.array(supportedLanguageGen, { minLength: 1, maxLength: 3 }),
  availability: operatingHoursGen,
  eligibilityRequirements: fc.array(fc.string({ minLength: 10, maxLength: 200 }), { maxLength: 5 }),
});

// Search criteria generator
export const searchCriteriaGen = fc.record({
  location: fc.option(locationGen),
  issueType: fc.option(legalIssueTypeGen),
  language: fc.option(supportedLanguageGen),
  urgency: fc.option(urgencyLevelGen),
  maxDistance: fc.option(fc.integer({ min: 1, max: 200 })),
});

// Voice input generators for testing speech recognition
export const voiceInputGen = fc.record({
  text: fc.string({ minLength: 1, maxLength: 500 }),
  language: supportedLanguageGen,
  confidence: fc.float({ min: 0.5, max: 1.0 }),
  hasBackgroundNoise: fc.boolean(),
  audioQuality: fc.constantFrom('excellent', 'good', 'fair', 'poor'),
});

// Legal query generators for testing classification
export const landDisputeQueryGen = fc.constantFrom(
  'My neighbor built a fence on my property',
  'There is a boundary dispute with my neighbor',
  'Someone is claiming ownership of my land',
  'My property deed shows different boundaries than what exists',
  'A developer is trying to take my land through eminent domain'
);

export const domesticViolenceQueryGen = fc.constantFrom(
  'My partner has been physically abusing me',
  'I need a restraining order against my ex-husband',
  'My spouse threatens me and I fear for my safety',
  'I need help escaping an abusive relationship',
  'My partner controls all my finances and won\'t let me leave'
);

export const wageTheftQueryGen = fc.constantFrom(
  'My employer hasn\'t paid me for overtime work',
  'My boss is withholding my final paycheck',
  'I worked extra hours but didn\'t get paid for them',
  'My employer is paying me below minimum wage',
  'My company deducted money from my paycheck illegally'
);

export const tenantRightsQueryGen = fc.constantFrom(
  'My landlord won\'t fix the broken heating system',
  'I received an eviction notice but I paid my rent',
  'My landlord is trying to raise my rent illegally',
  'There are health code violations in my apartment',
  'My landlord entered my apartment without permission'
);

export const legalQueryGen = fc.oneof(
  landDisputeQueryGen,
  domesticViolenceQueryGen,
  wageTheftQueryGen,
  tenantRightsQueryGen,
  fc.string({ minLength: 10, maxLength: 200 }) // Generic legal queries
);

// Generators for testing error conditions
export const invalidInputGen = fc.oneof(
  fc.constant(''),
  fc.constant('   '),
  fc.string({ maxLength: 0 }),
  fc.constant(null),
  fc.constant(undefined)
);

export const extremeInputGen = fc.oneof(
  fc.string({ minLength: 10000, maxLength: 50000 }), // Very long input
  fc.string({ minLength: 1, maxLength: 1 }), // Very short input
  fc.constant('a'.repeat(100000)), // Extremely long repetitive input
);

// Utility functions for test data generation
export const generateTestSession = (): Session => fc.sample(sessionGen, 1)[0]!;
export const generateTestLegalIssue = (): LegalIssue => fc.sample(legalIssueGen, 1)[0]!;
export const generateTestOrganization = (): LegalAidOrganization => fc.sample(legalAidOrganizationGen, 1)[0]!;
export const generateTestUserContext = (): UserContext => fc.sample(userContextGen, 1)[0]!;