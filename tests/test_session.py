import json
import types

import numpy as np
import pytest
from protocol import (
    LLM_RESPONSE_TEXT_KEY,
    TTS_AUDIO_BYTES_KEY,
    UPDATED_HISTORY_KEY,
    USER_TEXT_KEY,
    ClientControl,
    ConversationState,
)
from session import WebSocketSession


class StubPipeline:
    def __init__(self):
        self.orchestrate_calls = 0
        self.transcribe_audio_calls = 0

    def is_silent(self, _samples):
        return False

    def is_user_speech_finalized(self, _buffer):
        return False

    async def transcribe_audio(self, _audio):
        self.transcribe_audio_calls += 1
        return ""

    async def orchestrate_from_user_text(self, _user_text, _history):
        self.orchestrate_calls += 1
        return None

    async def orchestrate(self, _audio, _history):
        self.orchestrate_calls += 1
        return None

    async def orchestrate_streaming(self, _audio, _history):
        if False:
            yield

    async def orchestrate_streaming_from_user_text(self, _user_text, _history):
        if False:
            yield


class StubWebSocket:
    def __init__(self):
        self.sent_json = []
        self.sent_bytes = []

    async def send_json(self, payload):
        self.sent_json.append(payload)

    async def send_bytes(self, payload):
        self.sent_bytes.append(payload)


@pytest.mark.asyncio
async def test_handle_audio_done_transitions_to_idle():
    ws = StubWebSocket()
    pipeline = StubPipeline()
    session = WebSocketSession(
        pipeline=pipeline,
        stream_llm_responses=True,
        logger=types.SimpleNamespace(warning=lambda *_: None),
    )
    session.current_state = ConversationState.SPEAKING

    await session.handle_message(
        ws, {"text": json.dumps({"type": ClientControl.AUDIO_DONE})}
    )

    assert session.current_state == ConversationState.IDLE
    assert ws.sent_json[-1] == {"state": ConversationState.IDLE.value}


@pytest.mark.asyncio
async def test_handle_mic_stopped_clears_buffer_when_listening():
    ws = StubWebSocket()
    pipeline = StubPipeline()
    session = WebSocketSession(
        pipeline=pipeline,
        stream_llm_responses=True,
        logger=types.SimpleNamespace(warning=lambda *_: None),
    )
    session.current_state = ConversationState.LISTENING
    session.audio_buffer = [np.zeros(10, dtype=np.int16)]

    await session.handle_message(
        ws, {"text": json.dumps({"type": ClientControl.MIC_STOPPED})}
    )

    assert session.current_state == ConversationState.IDLE
    assert session.audio_buffer == []
    assert ws.sent_json[-1] == {"state": ConversationState.IDLE.value}


@pytest.mark.asyncio
async def test_finalized_audio_sends_user_text_during_thinking_before_speaking():
    ws = StubWebSocket()
    pipeline = StubPipeline()
    session = WebSocketSession(
        pipeline=pipeline,
        stream_llm_responses=False,
        logger=types.SimpleNamespace(warning=lambda *_: None),
    )

    pipeline.is_user_speech_finalized = lambda _buffer: True
    pipeline.transcribe_audio = lambda _audio: _async_return("Hello there")
    pipeline.orchestrate_from_user_text = lambda _user_text, _history: _async_return(
        {
            USER_TEXT_KEY: "Hello there",
            LLM_RESPONSE_TEXT_KEY: "Hi there.",
            UPDATED_HISTORY_KEY: [],
            TTS_AUDIO_BYTES_KEY: b"wav",
        }
    )

    await session.handle_message(
        ws, {"bytes": np.array([1, 2, 3], dtype=np.int16).tobytes()}
    )

    assert ws.sent_json == [
        {"state": ConversationState.LISTENING.value},
        {"state": ConversationState.THINKING.value, "userText": "Hello there"},
        {"state": ConversationState.SPEAKING.value, "llmResponse": "Hi there."},
    ]
    assert ws.sent_bytes == [b"wav"]


async def _async_return(value):
    return value
