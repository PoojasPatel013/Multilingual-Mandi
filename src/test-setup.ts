/**
 * Test setup configuration for Jest and fast-check
 * Configures property-based testing environment
 */

import * as fc from 'fast-check';

// Configure fast-check for property-based testing
beforeAll(() => {
  // Set global configuration for property-based tests
  fc.configureGlobal({
    // Minimum number of iterations for property tests
    numRuns: 100,
    // Enable verbose mode for debugging
    verbose: process.env.NODE_ENV === 'test' && process.env.VERBOSE === 'true',
    // Seed for reproducible tests (can be overridden per test)
    seed: process.env.FC_SEED ? parseInt(process.env.FC_SEED, 10) : undefined,
    // Maximum shrinking iterations
    maxSkipsPerRun: 100,
    // Timeout for individual property test runs
    timeout: 5000,
  });
});

// Global test utilities
declare global {
  namespace jest {
    interface Matchers<R> {
      toSatisfyProperty(): R;
    }
  }
}

// Custom Jest matcher for property-based tests
expect.extend({
  toSatisfyProperty(received: () => boolean) {
    const pass = received();
    if (pass) {
      return {
        message: () => `Expected property to fail, but it passed`,
        pass: true,
      };
    } else {
      return {
        message: () => `Expected property to pass, but it failed`,
        pass: false,
      };
    }
  },
});

// Test timeout configuration
jest.setTimeout(10000);

// Mock console methods in tests to reduce noise
const originalConsole = console;
beforeEach(() => {
  if (process.env.NODE_ENV === 'test' && !process.env.VERBOSE) {
    console.log = jest.fn();
    console.info = jest.fn();
    console.warn = jest.fn();
    console.error = originalConsole.error; // Keep errors visible
  }
});

afterEach(() => {
  if (process.env.NODE_ENV === 'test' && !process.env.VERBOSE) {
    console.log = originalConsole.log;
    console.info = originalConsole.info;
    console.warn = originalConsole.warn;
    console.error = originalConsole.error;
  }
});