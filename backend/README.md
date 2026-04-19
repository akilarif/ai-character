# Backend Directory

This folder contains the FastAPI server, the realtime websocket session logic, and the speech/LLM/TTS pipeline that powers the character.

## Files

- `main.py` starts the FastAPI app, serves the frontend from `/client`, initializes the shared `Pipeline`, and accepts websocket connections from the browser.
- `personas/` directory containing YAML files for each AI character (e.g., `haru.yaml`).
- `session.py` manages one browser connection at a time. It buffers mic audio, detects end-of-speech, triggers the pipeline, tracks conversation state, and sends JSON state updates (including parsed emotion tags) plus synthesized audio back to the client.
- `pipeline.py` contains the heavy AI orchestration layer. It loads config and models, runs speech-to-text, generates LLM replies with embedded emotion tags (e.g., `[happy]`), parses those tags for the client, synthesizes TTS audio, and optionally integrates MCP tools.
- `protocol.py` defines the shared wire protocol for browser/server communication, including conversation states, control message types, payload helpers, and typed pipeline result keys.
- `config.yaml.example` is the example configuration file showing the expected YAML structure for STT, LLM, TTS, and MCP server settings.

## How It Fits Together

`main.py` creates one shared `Pipeline`, then each websocket client gets its own `WebSocketSession`. The session uses `protocol.py` to keep payloads consistent while `pipeline.py` does the actual AI work.

## Personas

AI personalities are modular. Each character has a YAML file in `backend/personas/`.

- **Placeholders**: Use `{{emotions}}` to inject the list of supported emotion tags (dynamically read from `frontend/src/model-config.js`) and `{{tool_catalog}}` to inject available MCP tools.
- **Recency Bias**: It is recommended to place `{{tool_catalog}}` at the end of the `system_prompt` to improve tool-calling reliability.
- **Selection**: Choose the active persona by setting the `persona` key in `backend/config.yaml` to match the filename (e.g. `persona: "haru"` matches `haru.yaml`).
