# Frontend Source Directory

This folder contains the app's first-party JavaScript modules. Together they wire up the UI, microphone capture, websocket transport, Live2D model control, and TTS playback.

## Files

- `app.js` is the main coordinator. It grabs DOM elements, initializes UI state and the Live2D model, connects the websocket client, starts mic capture, and routes server state/audio into the UI and playback queue.
- `constants.js` centralizes configuration and shared constants such as server host/port, DOM element IDs, conversation states, UI labels, audio settings, and Live2D presentation presets.
- `ui-state.js` owns DOM updates for connection state, audio unlock status, mic button state, user transcript text, LLM response text, and visual AI-state changes.
- `audio-capture.js` manages microphone permissions, `AudioContext` setup, the PCM worklet connection, and start/stop behavior for live capture.
- `socket-client.js` wraps the browser `WebSocket` with reconnect logic plus safe helpers for sending JSON control messages and binary PCM audio.
- `tts-playback-queue.js` queues synthesized WAV responses from the backend and plays them sequentially through `PIXI.sound`, keeping model lip-sync/audio playback in order.
- `model-controller.js` creates the PIXI application, loads the Live2D model, applies motion/expression presets for conversation states, and prepares motion sound playback.
- `pixi-compat.js` patches PIXI v8 globals so the Live2D plugin and sound integration keep working with the bundled runtime versions.

## Suggested Reading Order

If you are new to the client, start with `app.js`, then read `constants.js`, `socket-client.js`, `audio-capture.js`, `tts-playback-queue.js`, and `model-controller.js`.
