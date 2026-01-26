/**
 * Voice Interface Components
 * Interfaces for speech recognition and synthesis services
 */

import { SessionId, SpeechError, AudioBuffer } from '../types';

/**
 * Speech-to-Text Service Interface
 * Converts user voice input to text with high accuracy
 */
export interface SpeechToTextService {
  /**
   * Start listening for speech input in the specified language
   * @param sessionId - Unique session identifier
   * @param language - Language code (e.g., 'en-US', 'es-ES')
   */
  startListening(sessionId: SessionId, language: string): Promise<void>;

  /**
   * Stop listening and return the recognized text
   * @param sessionId - Unique session identifier
   * @returns Recognized text from speech input
   */
  stopListening(sessionId: SessionId): Promise<string>;

  /**
   * Register callback for speech recognition events
   * @param callback - Function to call when speech is recognized
   */
  onSpeechRecognized(callback: (text: string, confidence: number) => void): void;

  /**
   * Register callback for speech recognition errors
   * @param callback - Function to call when errors occur
   */
  onError(callback: (error: SpeechError) => void): void;
}

/**
 * Text-to-Speech Service Interface
 * Converts system responses to natural-sounding speech
 */
export interface TextToSpeechService {
  /**
   * Synthesize text to speech audio
   * @param text - Text to convert to speech
   * @param language - Language code for synthesis
   * @param voice - Optional specific voice to use
   * @returns Audio buffer containing synthesized speech
   */
  synthesize(text: string, language: string, voice?: string): Promise<AudioBuffer>;

  /**
   * Play audio buffer through the system's audio output
   * @param audio - Audio buffer to play
   */
  playAudio(audio: AudioBuffer): Promise<void>;

  /**
   * Configure voice settings for speech synthesis
   * @param rate - Speech rate (0.5 to 2.0)
   * @param volume - Volume level (0.0 to 1.0)
   */
  setVoiceSettings(rate: number, volume: number): void;
}