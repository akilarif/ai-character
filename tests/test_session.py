import json
import types

import numpy as np
import pytest

from protocol import ClientControl, ConversationState
from session import WebSocketSession


class StubPipeline:
    def __init__(self):
        self.orchestrate_calls = 0

    def is_silent(self, _samples):
        return False

    def is_user_speech_finalized(self, _buffer):
        return False

    async def orchestrate(self, _audio, _history):
        self.orchestrate_calls += 1
        return None

    async def orchestrate_streaming(self, _audio, _history):
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
