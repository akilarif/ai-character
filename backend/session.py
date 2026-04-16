"""WebSocket session: mic audio, conversation state, and client controls."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Mapping, cast

import numpy as np
from fastapi import WebSocket
from pipeline import Pipeline
from protocol import (
    EMOTION_KEY,
    LLM_RESPONSE_TEXT_KEY,
    TTS_AUDIO_BYTES_KEY,
    UPDATED_HISTORY_KEY,
    ClientControl,
    ClientEventField,
    ConversationState,
    OrchestrateResult,
    conversation_state_payload,
    speaking_turn_payload,
    thinking_turn_payload,
)


@dataclass
class WebSocketSession:
    """Per-connection state for audio buffering, chat history, and phase."""

    pipeline: Pipeline
    stream_llm_responses: bool
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger(__name__))
    current_state: ConversationState = ConversationState.IDLE
    audio_buffer: list[np.ndarray] = field(default_factory=list)
    chat_history: list[dict] = field(default_factory=list)

    async def handle_message(
        self, websocket: WebSocket, data: Mapping[str, object]
    ) -> None:
        """Dispatch one Starlette websocket frame (binary PCM or text JSON)."""
        if "bytes" in data:
            await self._handle_audio_chunk(websocket, cast(bytes, data["bytes"]))
            return
        if "text" in data:
            await self._handle_text_command(websocket, cast(str, data["text"]))

    async def _handle_audio_chunk(self, websocket: WebSocket, chunk: bytes) -> None:
        """Buffer mic PCM, detect end-of-utterance, then run STT/LLM/TTS."""
        if self.current_state not in {
            ConversationState.IDLE,
            ConversationState.LISTENING,
        }:
            return

        samples = np.frombuffer(chunk, dtype=np.int16)
        if samples.size == 0:
            return

        is_silent = self.pipeline.is_silent(samples)
        if self.current_state == ConversationState.IDLE and not is_silent:
            self.current_state = ConversationState.LISTENING
            await websocket.send_json(
                conversation_state_payload(ConversationState.LISTENING)
            )

        self.audio_buffer.append(samples)

        if not self.pipeline.is_user_speech_finalized(self.audio_buffer):
            return

        full_audio_bytes = np.concatenate(self.audio_buffer).astype(np.int16).tobytes()
        self.audio_buffer.clear()
        user_text = await self.pipeline.transcribe_audio(bytearray(full_audio_bytes))
        if not user_text:
            self.current_state = ConversationState.IDLE
            await websocket.send_json(
                conversation_state_payload(ConversationState.IDLE)
            )
            return

        self.current_state = ConversationState.THINKING
        await websocket.send_json(
            thinking_turn_payload(
                state=ConversationState.THINKING,
                user_text=user_text,
            )
        )

        if self.stream_llm_responses:
            await self._stream_pipeline(websocket, user_text)
            return

        await self._run_pipeline_once(websocket, user_text)

    async def _stream_pipeline(self, websocket: WebSocket, user_text: str) -> None:
        """Stream LLM/TTS fragments after a finalized utterance (sentence-chunked)."""
        async for pipeline_result in self.pipeline.orchestrate_streaming_from_user_text(
            user_text, self.chat_history
        ):
            if not pipeline_result:
                continue
            await self._send_speaking_update(websocket, pipeline_result)

    async def _run_pipeline_once(self, websocket: WebSocket, user_text: str) -> None:
        """Run full STT → LLM → TTS once for a finalized utterance."""
        pipeline_result = await self.pipeline.orchestrate_from_user_text(
            user_text, self.chat_history
        )
        if not pipeline_result:
            return

        await self._send_speaking_update(websocket, pipeline_result)

    async def _send_speaking_update(
        self, websocket: WebSocket, pipeline_result: OrchestrateResult
    ) -> None:
        """Notify the UI and send one WAV TTS chunk for a pipeline slice."""
        self.chat_history = pipeline_result[UPDATED_HISTORY_KEY]
        llm_response = pipeline_result[LLM_RESPONSE_TEXT_KEY]
        emotion = pipeline_result[EMOTION_KEY]
        tts_audio_bytes = pipeline_result[TTS_AUDIO_BYTES_KEY]

        self.current_state = ConversationState.SPEAKING
        await websocket.send_json(
            speaking_turn_payload(
                state=ConversationState.SPEAKING,
                llm_response=llm_response,
                emotion=emotion,
            )
        )
        await websocket.send_bytes(tts_audio_bytes)

    async def _handle_text_command(self, websocket: WebSocket, text: str) -> None:
        """Handle client JSON controls (playback finished, mic stopped)."""
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            self.logger.warning("Skipping malformed websocket command payload.")
            return

        message_type = payload.get(ClientEventField.TYPE)
        if message_type == ClientControl.AUDIO_DONE:
            self.current_state = ConversationState.IDLE
            await websocket.send_json(
                conversation_state_payload(ConversationState.IDLE)
            )
            return

        if (
            message_type == ClientControl.MIC_STOPPED
            and self.current_state == ConversationState.LISTENING
        ):
            self.audio_buffer.clear()
            self.current_state = ConversationState.IDLE
            await websocket.send_json(
                conversation_state_payload(ConversationState.IDLE)
            )
