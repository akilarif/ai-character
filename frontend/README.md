# Frontend Directory

This folder contains the browser client: the page shell, styles, app bootstrap, microphone worklet, bundled third-party runtimes, and the Live2D model assets.

## Files

- `index.html` defines the UI shell, status cards, mic button, transcript areas, and script tags that load the bundled libraries plus the app entrypoint.
- `styles.css` provides the full visual layout and state-driven styling for the stage, control panel, transcripts, and status indicators.
- `main.js` is the browser entrypoint. It applies the PIXI compatibility shim and starts the app in `src/app.js`.
- `pcm-worklet.js` is an `AudioWorkletProcessor` that converts live microphone `Float32` samples into `Int16` PCM chunks for the backend STT pipeline.

## Subdirectories

- `src/` holds the app's first-party JavaScript modules.
- `lib/` holds bundled third-party browser libraries used by the Live2D client.
- `models/` contains the Live2D character assets, including model JSON, textures, motions, expressions, and optional sound files.

The Live2D runtime and model assets used by this frontend come from the [Live2D Cubism SDK ecosystem](https://www.live2d.com/en/sdk/about/).

## Runtime Flow

The browser loads `index.html`, `main.js` starts the app, the modules in `src/` manage UI/audio/websocket behavior, and the assets in `lib/` plus `models/` drive the rendered character.
