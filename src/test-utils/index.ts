/**
 * Test utilities and helpers for AI Legal Aid System
 */

export * from './generators';

// Test helper functions
export const delay = (ms: number): Promise<void> => 
  new Promise(resolve => setTimeout(resolve, ms));

export const mockDate = (date: string | Date): jest.SpyInstance => {
  const mockDate = new Date(date);
  return jest.spyOn(global, 'Date').mockImplementation(() => mockDate as any);
};

export const restoreDate = (spy: jest.SpyInstance): void => {
  spy.mockRestore();
};

// Property test helpers
export const runPropertyTest = async (
  property: () => boolean,
  options?: { numRuns?: number; seed?: number }
): Promise<void> => {
  const { numRuns = 100, seed } = options || {};
  
  for (let i = 0; i < numRuns; i++) {
    if (seed) {
      // Set seed for reproducible tests
      Math.random = jest.fn(() => seed / 2147483647);
    }
    
    const result = property();
    if (!result) {
      throw new Error(`Property test failed on iteration ${i + 1}`);
    }
  }
};

// Mock implementations for testing
export const createMockAudioBuffer = (): ArrayBuffer => {
  return new ArrayBuffer(1024);
};

export const createMockSpeechError = (code: string, message: string): any => ({
  code,
  message,
  recoverable: code !== 'FATAL_ERROR',
});

// Assertion helpers
export const expectValidSessionId = (sessionId: string): void => {
  expect(sessionId).toBeDefined();
  expect(typeof sessionId).toBe('string');
  expect(sessionId.length).toBeGreaterThan(0);
};

export const expectValidTimestamp = (timestamp: Date): void => {
  expect(timestamp).toBeInstanceOf(Date);
  expect(timestamp.getTime()).not.toBeNaN();
};

export const expectValidLanguageCode = (language: string): void => {
  expect(language).toBeDefined();
  expect(typeof language).toBe('string');
  expect(['en-US', 'es-ES', 'en', 'es']).toContain(language);
};