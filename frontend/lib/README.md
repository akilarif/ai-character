# Frontend Library Directory

This folder contains third-party browser libraries that are loaded directly by `frontend/index.html`. They provide the rendering, audio, and Live2D runtime pieces the client depends on.

## Files

- `live2d.min.js`: legacy Live2D runtime required by the PIXI Live2D integration used in this project. Bundled runtime generation: `Cubism 2.1`.
- `live2dcubismcore.min.js`: official Live2D Cubism Core runtime used to load and animate Cubism model data. Bundled runtime generation: `Cubism 5`.
- `pixi.min.js`: bundled PixiJS rendering engine used to create the canvas app and render the Live2D model. Bundled version: `8.17.1`.
- `pixi-sound.js`: PIXI sound/audio playback layer used for TTS playback and optional motion-linked sound effects. Bundled version: `6.0.1`.
- `untitled-pixi-live2d-engine_index.min.js`: PIXI Live2D integration plugin that bridges PixiJS with Live2D model loading, animation, expressions, and lip sync. Bundled version: `1.0.1`.

## Sources

- `live2d.min.js`: Official distribution was discontinued on [September 4, 2019](https://help.live2d.com/en/other/other_20/). Archived copies can be found in [dylanNew/live2d on GitHub](https://github.com/dylanNew/live2d/tree/master/webgl/Live2D/lib) or [jsDelivr](https://cdn.jsdelivr.net/gh/dylanNew/live2d/webgl/Live2D/lib/live2d.min.js).
- `live2dcubismcore.min.js`: Part of the [Live2D Cubism SDK ecosystem](https://www.live2d.com/en/sdk/download/web/).
- `pixi.min.js`: Release builds come from [PixiJS releases](https://github.com/pixijs/pixijs/releases).
- `pixi-sound.js`: Release builds come from [Pixi Sound releases](https://github.com/pixijs/sound/releases).
- `untitled-pixi-live2d-engine_index.min.js`: Comes from the [GitHub project `untitled-pixi-live2d-engine`](https://github.com/Untitled-Story/untitled-pixi-live2d-engine).

## Notes

These are vendor bundles loaded directly by `frontend/index.html`, so they are typically updated by replacing the built file rather than editing it in place.
