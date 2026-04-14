"""MLX-based speech, language, and TTS pipeline with optional MCP tools.

Loads models and configuration from YAML, runs Whisper STT, MLX LM generation
(with an MCP tool-calling loop when configured), and MLX audio TTS. Used by
the websocket session to produce assistant replies and WAV audio bytes.
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import sys
from contextlib import AsyncExitStack
from queue import Queue
from threading import Thread
from typing import Any, Final, Optional

import mlx_whisper
import numpy as np
import soundfile as sf
import yaml
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mlx_audio.tts.utils import load_model
from mlx_lm import generate, load, stream_generate

from protocol import OrchestrateResult, PipelineResultKey


class Pipeline:
    """Configured STT/LLM/TTS stack and MCP tool integration for one process."""

    DEFAULT_STT_NUM_CHANNELS: Final = 1
    DEFAULT_STT_SAMPLE_RATE: Final = 16000
    DEFAULT_STT_CHUNK_SIZE: Final = 1024
    DEFAULT_STT_SILENCE_THRESHOLD: Final = 500
    DEFAULT_STT_SILENCE_DURATION: Final = 1.5
    DEFAULT_STT_MIN_AUDIO_DURATION: Final = 0.5

    DEFAULT_LLM_ENABLE_THINKING: Final = False
    DEFAULT_LLM_MAX_TOKENS: Final = None
    DEFAULT_MAX_LLM_CHAT_HISTORY_LENGTH: Final = 10
    DEFAULT_MAX_TOOL_TURNS: Final = 5

    DEFAULT_TTS_SAMPLE_RATE: Final = 24000

    config: dict
    stt_config: dict
    llm_config: dict
    tts_config: dict
    mcp_servers_config: dict

    llm_model: Any
    llm_tokenizer: Any
    tts_model: Any

    mcp_stack: AsyncExitStack
    tool_registry: dict[str, tuple[ClientSession, str]]
    system_prompt: str

    def __init__(self, config_path="config.yaml"):
        """Load YAML (with ``${VAR}`` expansion) and initialize heavy models."""
        with open(config_path, "r") as f:
            # Use expandvars to swap the ${} in yaml with actual values
            self.config = yaml.safe_load(os.path.expandvars(f.read()))
        self.stt_config = self.config.get("stt", {})
        self.llm_config = self.config.get("llm", {})
        self.tts_config = self.config.get("tts", {})
        self.mcp_servers_config = self.config.get("mcp_servers", [])

        # Prewarm STT with dummy audio of 1 second of silence
        print("Prewarming STT model...")
        dummy_audio = np.zeros(
            self.stt_config.get("rate", Pipeline.DEFAULT_STT_SAMPLE_RATE),
            dtype=np.float32,
        )
        mlx_whisper.transcribe(
            dummy_audio, path_or_hf_repo=self.stt_config.get("model_path")
        )
        print("STT model prewarmed")
        print("Loading LLM...")
        self.llm_model, self.llm_tokenizer = load(self.llm_config.get("model_path"))
        print("LLM loaded")
        print("Loading TTS model...")
        self.tts_model = load_model(self.tts_config.get("model_path"))
        print("TTS model loaded")

        self.mcp_stack = AsyncExitStack()
        self.tool_registry = {}
        self.system_prompt = ""

    def is_silent(self, samples: np.ndarray):
        """Return True when RMS level is below ``stt.silence_threshold``."""
        rms_volume = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
        silence_threshold = self.stt_config.get(
            "silence_threshold", self.DEFAULT_STT_SILENCE_THRESHOLD
        )
        return rms_volume < silence_threshold

    def compute_chunk_duration(self, chunk: bytes | np.ndarray, dtype=np.int16):
        """Duration in seconds for mono PCM (``bytes`` or int16 ``ndarray``)."""
        rate = self.stt_config.get("rate", Pipeline.DEFAULT_STT_SAMPLE_RATE)
        if isinstance(chunk, np.ndarray):
            return len(chunk) / rate

        bytes_per_sample = np.dtype(dtype).itemsize
        return len(chunk) / (rate * bytes_per_sample)

    def is_user_speech_finalized(
        self, audio_buffer: list[np.ndarray], dtype=np.int16
    ) -> bool:
        """
        Returns True if the user has stopped speaking.
        Uses RMS volume + dynamic chunk duration + minimum speech duration.
        """
        if not audio_buffer:
            return False

        total_duration = 0.0
        silent_time = 0.0
        silence_duration = self.stt_config.get(
            "silence_duration", self.DEFAULT_STT_SILENCE_DURATION
        )
        min_audio_duration = self.stt_config.get(
            "min_audio_duration", self.DEFAULT_STT_MIN_AUDIO_DURATION
        )

        for chunk in audio_buffer:
            if chunk.size == 0:
                continue
            chunk_duration = self.compute_chunk_duration(chunk, dtype=dtype)
            total_duration += chunk_duration

            if self.is_silent(chunk):
                silent_time += chunk_duration
            else:
                silent_time = 0.0  # reset on speech

        ## Log for debugging
        # print(f"mylog: Total Duration: {total_duration:.2f}s, Silent Time: {silent_time:.2f}s, RMS: {rms_volume:.2f}")

        if total_duration >= min_audio_duration and silent_time >= silence_duration:
            return True
        return False

    async def orchestrate(
        self, input_audio_bytes: bytearray, chat_history: list[dict]
    ) -> OrchestrateResult | None:
        """Full turn: transcribe, respond, synthesize; ``None`` if STT is empty."""
        print("Starting to transcribe...")
        user_text = await asyncio.to_thread(self.run_stt, input_audio_bytes)
        if not user_text:
            return None
        print("Finished transcribing. Transcription = ", user_text)
        print("Calling LLM...")
        llm_response_text, updated_history = await self.run_llm(user_text, chat_history)
        print("Got LLM response: ", llm_response_text)
        print("Generating TTS...")
        tts_audio_bytes = await asyncio.to_thread(self.run_tts, llm_response_text)
        print("Finished generating TTS")
        return {
            PipelineResultKey.USER_TEXT: user_text,
            PipelineResultKey.LLM_RESPONSE_TEXT: llm_response_text,
            PipelineResultKey.UPDATED_HISTORY: updated_history,
            PipelineResultKey.TTS_AUDIO_BYTES: tts_audio_bytes,
        }

    async def orchestrate_streaming(
        self, input_audio_bytes: bytearray, chat_history: list[dict]
    ):
        """Like :meth:`orchestrate` but yields TTS per detected sentence while streaming."""
        print("Starting to transcribe...")
        user_text = await asyncio.to_thread(self.run_stt, input_audio_bytes)
        if not user_text:
            return
        print("Finished transcribing. Transcription = ", user_text)

        print("Calling LLM Streaming...")
        sentence_buffer = ""
        async for token in self.run_llm_streaming(user_text, chat_history):
            sentence_buffer += token

            # Trigger TTS when a sentence is finished
            # TODO: Improve this logic. It splits decimals like 3.14
            if (
                any(p in token for p in [".", "!", "?", "\n"])
                and len(sentence_buffer.strip()) > 15
            ):
                current_llm_response_text = sentence_buffer.strip()
                if "TOOL_CALL:" in current_llm_response_text:
                    # We don't clear the buffer yet, because we need the full JSON
                    # for the tool logic later in the function.
                    sentence_buffer = ""
                    continue
                print(f"Generating TTS for sentence: {current_llm_response_text}")
                tts_audio_bytes = await asyncio.to_thread(
                    self.run_tts, current_llm_response_text
                )
                yield {
                    PipelineResultKey.USER_TEXT: user_text,
                    PipelineResultKey.LLM_RESPONSE_TEXT: current_llm_response_text,
                    PipelineResultKey.UPDATED_HISTORY: chat_history,
                    PipelineResultKey.TTS_AUDIO_BYTES: tts_audio_bytes,
                }
                sentence_buffer = ""

        # Handle any leftover text in the buffer after the LLM finishes
        if sentence_buffer.strip():
            current_text = sentence_buffer.strip()
            tts_audio_bytes = await asyncio.to_thread(self.run_tts, current_text)
            yield {
                PipelineResultKey.USER_TEXT: user_text,
                PipelineResultKey.LLM_RESPONSE_TEXT: current_text,
                PipelineResultKey.UPDATED_HISTORY: chat_history,
                PipelineResultKey.TTS_AUDIO_BYTES: tts_audio_bytes,
            }

    def run_stt(self, byte_data: bytearray) -> str:
        """Blocking Whisper transcription of int16 PCM in ``byte_data``."""
        if not byte_data:
            return ""
        audio_np = np.frombuffer(byte_data, dtype=np.int16).astype(np.float32) / 32768.0
        result = mlx_whisper.transcribe(
            audio_np, path_or_hf_repo=self.stt_config.get("model_path")
        )
        return result["text"].strip()

    async def run_llm(
        self, user_text: str, chat_history: list[dict]
    ) -> tuple[str, list[dict]]:
        """Generate assistant text; loop on MCP ``TOOL_CALL`` when configured."""
        enable_thinking = self.llm_config.get(
            "enable_thinking", self.DEFAULT_LLM_ENABLE_THINKING
        )
        max_tokens = self.llm_config.get("max_tokens", self.DEFAULT_LLM_MAX_TOKENS)
        max_tool_turns = self.llm_config.get(
            "max_tool_turns", self.DEFAULT_MAX_TOOL_TURNS
        )

        # Keep only the last N messages to save memory
        max_chat_history_length = self.llm_config.get(
            "max_chat_history_length", self.DEFAULT_MAX_LLM_CHAT_HISTORY_LENGTH
        )
        if len(chat_history) > max_chat_history_length:
            system_msg = chat_history[0]
            chat_history = [system_msg] + chat_history[-(max_chat_history_length - 1) :]

        if not chat_history:
            chat_history.append({"role": "system", "content": self.system_prompt})
        chat_history.append({"role": "user", "content": user_text})

        if not self.mcp_servers_config:
            raw_response = await asyncio.to_thread(
                self._run_mlx,
                self.llm_model,
                self.llm_tokenizer,
                chat_history,
                enable_thinking,
                max_tokens,
            )
            response = self._strip_thinking(raw_response).strip()
            chat_history.append({"role": "assistant", "content": response})
            return response, chat_history

        for _ in range(max_tool_turns):
            raw_response = await asyncio.to_thread(
                self._run_mlx,
                self.llm_model,
                self.llm_tokenizer,
                chat_history,
                enable_thinking,
                max_tokens,
            )
            response_without_thought = self._strip_thinking(raw_response)
            chat_history.append(
                {"role": "assistant", "content": response_without_thought.strip()}
            )
            tool_call = self._extract_tool_call(response_without_thought)
            if tool_call is None:
                return response_without_thought.strip(), chat_history

            full_name = tool_call["name"]
            args = tool_call["arguments"]
            if full_name not in self.tool_registry:
                err = f"Unknown tool name {full_name!r}. Valid names: {sorted(self.tool_registry.keys())}"
                print(err, file=sys.stderr)
                chat_history.append({"role": "user", "content": err})
                continue

            session, mcp_tool_name = self.tool_registry[full_name]
            print(
                f"Calling tool: {full_name} -> {mcp_tool_name}({args})", file=sys.stderr
            )
            tool_result = await session.call_tool(mcp_tool_name, arguments=args)
            tool_text = self._tool_result_text(tool_result)
            chat_history.append(
                {
                    "role": "user",
                    "content": (
                        f"Original question: {user_text}\n\n"
                        f"Tool `{full_name}` result:\n{tool_text}\n\n"
                        "If you need another tool, reply with ONLY:\n"
                        'TOOL_CALL: {"name": "<tool name>", "arguments": { ... }}\n'
                        "Otherwise answer in plain language."
                    ),
                }
            )

        print("Stopped after max tool turns; last model output was:", file=sys.stderr)
        return response_without_thought.strip(), chat_history

    async def run_llm_streaming(self, user_text: str, chat_history: list[dict]):
        """Stream MLX tokens from a thread; supports MCP tool rounds like :meth:`run_llm`."""
        enable_thinking = self.llm_config.get(
            "enable_thinking", self.DEFAULT_LLM_ENABLE_THINKING
        )
        max_tokens = self.llm_config.get("max_tokens", self.DEFAULT_LLM_MAX_TOKENS)
        max_tool_turns = self.llm_config.get(
            "max_tool_turns", self.DEFAULT_MAX_TOOL_TURNS
        )

        max_chat_history_length = self.llm_config.get(
            "max_chat_history_length", self.DEFAULT_MAX_LLM_CHAT_HISTORY_LENGTH
        )
        if len(chat_history) > max_chat_history_length:
            system_msg = chat_history[0]
            chat_history = [system_msg] + chat_history[-(max_chat_history_length - 1) :]

        if not chat_history:
            chat_history.append({"role": "system", "content": self.system_prompt})
        chat_history.append({"role": "user", "content": user_text})

        for _ in range(max_tool_turns):
            token_queue = Queue()
            sentinel = object()

            # Define the Producer: Runs in a background thread
            def producer():
                try:
                    # This calls the mlx_lm.stream_generate wrapper
                    for token in self._run_mlx_stream(
                        self.llm_model,
                        self.llm_tokenizer,
                        chat_history,
                        enable_thinking,
                        max_tokens,
                    ):
                        token_queue.put(token)
                except Exception as e:
                    token_queue.put(e)
                finally:
                    token_queue.put(sentinel)

            # Start the background thread
            Thread(target=producer, daemon=True).start()

            full_response = ""
            is_potential_tool = False
            yielded_buffered_tokens = False

            # The Consumer: Pulls tokens from the queue without blocking FastAPI
            while True:
                # Get next token from thread (non-blocking for the event loop)
                token = await asyncio.to_thread(token_queue.get)

                if token is sentinel:
                    break
                if isinstance(token, Exception):
                    print(f"LLM Error: {token}")
                    break

                full_response += token

                # Real-time filtering: Don't stream internal tool call JSON to TTS
                if "TOOL_CALL:" in full_response:
                    is_potential_tool = True

                if not is_potential_tool:
                    # If we haven't confirmed it's NOT a tool yet, wait until
                    # we have at least 10 chars (length of "TOOL_CALL:")
                    if len(full_response) >= 10:
                        if not yielded_buffered_tokens:
                            # First time reaching the threshold? Yield everything we held back
                            yield full_response
                            yielded_buffered_tokens = True
                        else:
                            # We already cleared the buffer, just yield the new token
                            yield token

            response_without_thought = self._strip_thinking(full_response)
            chat_history.append(
                {"role": "assistant", "content": response_without_thought.strip()}
            )

            if not self.mcp_servers_config:
                return
            tool_call = self._extract_tool_call(response_without_thought)
            if tool_call is None:
                return

            full_name = tool_call["name"]
            args = tool_call["arguments"]

            if full_name not in self.tool_registry:
                err = f"Unknown tool name {full_name!r}. Valid names: {sorted(self.tool_registry.keys())}"
                print(err, file=sys.stderr)
                chat_history.append({"role": "user", "content": err})
                continue

            session, mcp_tool_name = self.tool_registry[full_name]
            print(
                f"Calling tool: {full_name} -> {mcp_tool_name}({args})", file=sys.stderr
            )
            tool_result = await session.call_tool(mcp_tool_name, arguments=args)
            tool_text = self._tool_result_text(tool_result)
            chat_history.append(
                {
                    "role": "user",
                    "content": (
                        f"Original question: {user_text}\n\n"
                        f"Tool `{full_name}` result:\n{tool_text}\n\n"
                        "If you need another tool, reply with ONLY:\n"
                        'TOOL_CALL: {"name": "<tool name>", "arguments": { ... }}\n'
                        "Otherwise answer in plain language."
                    ),
                }
            )

        print("Stopped after max tool turns; last model output was:", file=sys.stderr)

    def run_tts(self, text: str) -> bytes:
        """Synthesize ``text`` to WAV bytes using the loaded MLX TTS model."""
        all_audio = []
        for result in self.tts_model.generate(
            text,
            voice=self.tts_config.get("voice", ""),
            lang_code=self.tts_config.get("lang_code", ""),
        ):
            all_audio.append(np.array(result.audio))
        all_audio_combined = np.concatenate(all_audio)
        wav_buffer = io.BytesIO()
        sf.write(
            wav_buffer,
            all_audio_combined,
            self.tts_config.get("sample_rate", self.DEFAULT_TTS_SAMPLE_RATE),
            format="WAV",
        )
        return wav_buffer.getvalue()

    async def initialize_mcp(self):
        """Connect MCP servers from config and build tool registry + system prompt."""
        if not self.mcp_servers_config:
            self.system_prompt = self._build_system_prompt(
                "(No MCP servers configured.)"
            )
            return
        mcp_sessions = await self._connect_mcp_sessions_stack(
            self.mcp_stack, self.mcp_servers_config
        )
        tool_catalog, self.tool_registry = await self._build_tool_catalog_and_registry(
            mcp_sessions
        )
        self.system_prompt = self._build_system_prompt(tool_catalog)

    async def close_mcp(self):
        """Release MCP stdio transports and child processes."""
        await self.mcp_stack.aclose()

    @staticmethod
    def _build_system_prompt(tool_catalog: str) -> str:
        """System prompt including tool list and TOOL_CALL instructions."""
        return f"""You are a helpful assistant.

    Answer from your own knowledge when that is enough. Use tools when the user needs live or external information.

    ## Available tools

    Each tool has a unique name. To call a tool, your entire reply must be ONLY this line (no other text):
    TOOL_CALL: {{"name": "<exact tool name from list below>", "arguments": {{ ... }}}}

    Use the exact JSON object shape; arguments must match the tool's parameters.

    You may call tools multiple times. If results are insufficient, call again with a refined name or arguments, or try another tool.

    When you do not need a tool, answer in normal language (do not write TOOL_CALL).

    ---

    {tool_catalog}
    """

    @staticmethod
    def _strip_thinking(text: str) -> str:
        """If ``</think>`` appears, return only the text after that marker."""
        if "</think>" in text:
            print("Thought: ", text.split("</think>", 1)[0])
            print("-" * 50)
            return text.split("</think>", 1)[1].strip()
        return text

    @staticmethod
    def _find_balanced_json_object(s: str) -> int | None:
        """Index after the first top-level balanced ``{...}`` in ``s``, or ``None``."""
        if not s.startswith("{"):
            return None
        depth = 0
        for i, c in enumerate(s):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return i + 1
        return None

    @staticmethod
    def _extract_tool_call(assistant_text: str) -> dict[str, Any] | None:
        """Parse TOOL_CALL: {{...}} JSON with optional multiline object."""
        text = Pipeline._strip_thinking(assistant_text.strip())
        marker = "TOOL_CALL:"
        idx = text.find(marker)
        if idx == -1:
            return None
        rest = text[idx + len(marker) :].strip()
        end = Pipeline._find_balanced_json_object(rest)
        if end is None:
            return None
        try:
            obj = json.loads(rest[:end])
        except json.JSONDecodeError:
            return None
        if not isinstance(obj, dict) or "name" not in obj:
            return None
        name = obj["name"]
        if not isinstance(name, str) or not name.strip():
            return None
        args = obj.get("arguments", {})
        if args is None:
            args = {}
        if not isinstance(args, dict):
            return None
        return {"name": name.strip(), "arguments": args}

    @staticmethod
    def _tool_result_text(result: types.CallToolResult) -> str:
        """Flatten MCP tool result content into a single string for the chat."""
        parts: list[str] = []
        for block in result.content:
            if isinstance(block, types.TextContent):
                parts.append(block.text)
        if result.isError:
            return (
                "Tool error:\n" + "\n".join(parts)
                if parts
                else "Tool error (no message)."
            )
        return "\n".join(parts)

    @staticmethod
    async def _build_tool_catalog_and_registry(
        sessions: list[tuple[str, ClientSession]],
    ) -> tuple[str, dict[str, tuple[ClientSession, str]]]:
        """
        Returns (markdown catalog for system prompt, registry).
        Registry: full_name -> (ClientSession, original_mcp_tool_name)
        """
        catalog_lines: list[str] = []
        registry: dict[str, tuple[ClientSession, str]] = {}

        for server_id, session in sessions:
            list_tools_result = await session.list_tools()
            for tool in list_tools_result.tools:
                full_name = f"{server_id}__{tool.name}"
                registry[full_name] = (session, tool.name)
                description = (tool.description or "").strip() or "(no description)"
                schema = tool.inputSchema if getattr(tool, "inputSchema", None) else {}
                schema_str = json.dumps(schema, indent=2) if schema else "{}"
                catalog_lines.append(
                    f"- **{full_name}**\n  - Description: {description}\n  - Parameters (JSON Schema):\n```json\n{schema_str}\n```\n"
                )

        catalog = (
            "\n".join(catalog_lines)
            if catalog_lines
            else "(No MCP tools — configure MCP_SERVERS.)"
        )
        return catalog, registry

    @staticmethod
    async def _connect_mcp_sessions_stack(
        stack: AsyncExitStack,
        configs: list[dict],
    ) -> list[tuple[str, ClientSession]]:
        """Start one MCP ``ClientSession`` per config entry under ``stack``."""
        output: list[tuple[str, ClientSession]] = []
        for config in configs:
            studio_server_params = StdioServerParameters(
                command=config.get("command", "uvx"),
                args=config.get("args", []),
                env=config.get("env", {}),
            )
            transport = await stack.enter_async_context(
                stdio_client(studio_server_params)
            )
            read, write = transport
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            output.append((config.get("id", "unknown"), session))
        return output

    @staticmethod
    def _run_mlx(
        model,
        tokenizer,
        messages: list[dict],
        enable_thinking: bool,
        max_tokens: Optional[int],
    ) -> str:
        """Single-shot MLX LM generation (blocking; run via ``asyncio.to_thread``)."""
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=enable_thinking,
        )
        if max_tokens:
            return generate(model, tokenizer, prompt=prompt, max_tokens=max_tokens)
        return generate(model, tokenizer, prompt=prompt)

    @staticmethod
    def _run_mlx_stream(
        model,
        tokenizer,
        messages: list[dict],
        enable_thinking: bool,
        max_tokens: Optional[int],
    ):
        """Stream MLX LM tokens (blocking iterator; consumed from a worker thread)."""
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=enable_thinking,
        )
        stream = (
            stream_generate(model, tokenizer, prompt=prompt, max_tokens=max_tokens)
            if max_tokens
            else stream_generate(model, tokenizer, prompt=prompt)
        )
        for response in stream:
            if hasattr(response, "text"):
                yield response.text
            else:
                yield str(response)
