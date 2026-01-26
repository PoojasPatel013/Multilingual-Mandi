"""
Voice interface protocols for the AI Legal Aid System.

This module defines the contracts for speech-to-text and text-to-speech
services, enabling voice interaction with the legal aid system.
"""

from abc import abstractmethod
from typing import Callable, Protocol

from ai_legal_aid.types import SessionId, AudioBuffer, SpeechError


class SpeechToTextService(Protocol):
    """Protocol for speech-to-text conversion services."""

    @abstractmethod
    async def start_listening(self, session_id: SessionId, language: str) -> None:
        """
        Start listening for speech input.

        Args:
            session_id: Unique session identifier
            language: Language code (e.g., 'en', 'es')
        """
        ...

    @abstractmethod
    async def stop_listening(self, session_id: SessionId) -> str:
        """
        Stop listening and return recognized text.

        Args:
            session_id: Unique session identifier

        Returns:
            Recognized text from speech input
        """
        ...

    @abstractmethod
    def on_speech_recognized(self, callback: Callable[[str, float], None]) -> None:
        """
        Register callback for speech recognition events.

        Args:
            callback: Function to call with (text, confidence) when speech is recognized
        """
        ...

    @abstractmethod
    def on_error(self, callback: Callable[[SpeechError], None]) -> None:
        """
        Register callback for speech recognition errors.

        Args:
            callback: Function to call when speech recognition errors occur
        """
        ...


class TextToSpeechService(Protocol):
    """Protocol for text-to-speech synthesis services."""

    @abstractmethod
    async def synthesize(
        self, text: str, language: str, voice: str | None = None
    ) -> AudioBuffer:
        """
        Convert text to speech audio.

        Args:
            text: Text to convert to speech
            language: Language code (e.g., 'en', 'es')
            voice: Optional specific voice to use

        Returns:
            Audio buffer containing synthesized speech
        """
        ...

    @abstractmethod
    async def play_audio(self, audio: AudioBuffer) -> None:
        """
        Play audio buffer through speakers.

        Args:
            audio: Audio buffer to play
        """
        ...

    @abstractmethod
    def set_voice_settings(self, rate: float, volume: float) -> None:
        """
        Configure voice synthesis settings.

        Args:
            rate: Speech rate (0.5 to 2.0)
            volume: Volume level (0.0 to 1.0)
        """
        ...
