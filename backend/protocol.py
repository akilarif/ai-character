"""Shared client/server protocol for the realtime AI character.

This module holds the *names and shapes* of messages exchanged over the
browser websocket: conversation lifecycle states, client control messages,
JSON field names, and the structured result produced by the ML pipeline.

Wire payloads remain plain JSON; enums stringify to the same values the UI
already expects.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final, Literal, TypedDict


class ConversationState(StrEnum):
    """High-level phase of a single user turn (server-authoritative)."""

    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"


class ClientControl(StrEnum):
    """Commands sent from the browser to influence session flow."""

    AUDIO_DONE = "AUDIO_DONE"
    MIC_STOPPED = "MIC_STOPPED"


class ClientEventField(StrEnum):
    """Field names on JSON events sent to the browser."""

    STATE = "state"
    USER_TEXT = "userText"
    LLM_RESPONSE = "llmResponse"
    TYPE = "type"


# TypedDict keys must be literal strings for static typing; these aliases are
# the single source of truth for internal dict access and pipeline outputs.
USER_TEXT_KEY: Final[Literal["user_text"]] = "user_text"
"""Key for transcribed user text on :class:`OrchestrateResult`."""

LLM_RESPONSE_TEXT_KEY: Final[Literal["llm_response_text"]] = "llm_response_text"
"""Key for LLM response on :class:`OrchestrateResult`."""

UPDATED_HISTORY_KEY: Final[Literal["updated_history"]] = "updated_history"
"""Key for the chat message list after the LLM step."""

TTS_AUDIO_BYTES_KEY: Final[Literal["tts_audio_bytes"]] = "tts_audio_bytes"
"""Key for synthesized WAV bytes on :class:`OrchestrateResult`."""


class PipelineResultKey:
    """Dotted access to the same literals as ``USER_TEXT_KEY`` and siblings."""

    USER_TEXT = USER_TEXT_KEY
    LLM_RESPONSE_TEXT = LLM_RESPONSE_TEXT_KEY
    UPDATED_HISTORY = UPDATED_HISTORY_KEY
    TTS_AUDIO_BYTES = TTS_AUDIO_BYTES_KEY


class OrchestrateResult(TypedDict):
    """Structured output of :meth:`pipeline.Pipeline.orchestrate`."""

    user_text: str
    llm_response_text: str
    updated_history: list[dict]
    tts_audio_bytes: bytes


def conversation_state_payload(state: ConversationState) -> dict[str, str]:
    """JSON payload notifying the UI of a :class:`ConversationState` change."""
    return {ClientEventField.STATE: state.value}


def thinking_turn_payload(
    *,
    state: ConversationState,
    user_text: str,
) -> dict[str, str]:
    """JSON payload for a thinking turn with finalized user transcript."""
    return {
        ClientEventField.STATE: state.value,
        ClientEventField.USER_TEXT: user_text,
    }


def speaking_turn_payload(
    *,
    state: ConversationState,
    llm_response: str,
) -> dict[str, str]:
    """JSON payload for a speaking turn with one LLM response text fragment."""
    return {
        ClientEventField.STATE: state.value,
        ClientEventField.LLM_RESPONSE: llm_response,
    }
