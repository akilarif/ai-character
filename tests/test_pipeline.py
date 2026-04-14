import numpy as np
import pytest

from pipeline import Pipeline


@pytest.mark.asyncio
async def test_run_llm_without_mcp_returns_tuple_and_history():
    pipe = Pipeline.__new__(Pipeline)
    pipe.llm_config = {}
    pipe.mcp_servers_config = []
    pipe.system_prompt = "You are helpful."
    pipe.llm_model = object()
    pipe.llm_tokenizer = object()
    pipe.DEFAULT_LLM_ENABLE_THINKING = False
    pipe.DEFAULT_LLM_MAX_TOKENS = None
    pipe.DEFAULT_MAX_TOOL_TURNS = 5
    pipe.DEFAULT_MAX_LLM_CHAT_HISTORY_LENGTH = 10

    pipe._run_mlx = lambda *_args, **_kwargs: "assistant reply"
    pipe._strip_thinking = lambda text: text

    response, updated_history = await pipe.run_llm("hello", [])

    assert response == "assistant reply"
    assert updated_history[-2]["role"] == "user"
    assert updated_history[-1] == {"role": "assistant", "content": "assistant reply"}


def test_compute_chunk_duration_uses_sample_count_for_ndarray():
    pipe = Pipeline.__new__(Pipeline)
    pipe.stt_config = {"rate": 16000}

    samples = np.zeros(16000, dtype=np.int16)
    duration = pipe.compute_chunk_duration(samples)
    assert duration == 1.0
