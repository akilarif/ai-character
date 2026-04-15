# Third-Party Notices

This repository contains first-party project code plus bundled third-party runtimes and sample assets.

## Project Code

The source code in this repository is licensed under the MIT License in [`LICENSE`](LICENSE).

## Live2D Runtimes And Sample Assets

This repository includes Live2D runtimes and sample model assets used by the frontend.

- `frontend/lib/live2d.min.js` is a legacy Live2D runtime.
- `frontend/lib/live2dcubismcore.min.js` is part of the Live2D Cubism SDK ecosystem.
- `frontend/models/Haru/` contains Live2D sample model assets.

These components are not covered by this repository's MIT license. They are subject to Live2D's license terms and sample-material terms.

- [Live2D Cubism SDK overview](https://www.live2d.com/en/sdk/about/)
- [Cubism Core documentation](https://docs.live2d.com/en/cubism-sdk-manual/cubism-core/)
- [SDK Release License information](https://www.live2d.com/en/sdk/license/)
- Terms for the Live2D sample assets included in this repository: [`LICENSE-Live2D.md`](LICENSE-Live2D.md)

If you redistribute or publish content using the bundled Live2D sample assets or SDK-based runtimes, review the applicable Live2D terms carefully.

## Bundled Frontend Libraries

This repository also bundles third-party browser libraries in `frontend/lib/`.

- `frontend/lib/pixi.min.js` bundles PixiJS, which is distributed under the MIT License. Source: [PixiJS on GitHub](https://github.com/pixijs/pixijs)
- `frontend/lib/pixi-sound.js` bundles `@pixi/sound`, which is distributed under the MIT License. Source: [Pixi Sound on GitHub](https://github.com/pixijs/sound)
- `frontend/lib/untitled-pixi-live2d-engine_index.min.js` bundles `untitled-pixi-live2d-engine`, which is published with an MIT license. Source: [Untitled Story `untitled-pixi-live2d-engine`](https://github.com/Untitled-Story/untitled-pixi-live2d-engine). Package metadata: [jsDelivr package page](https://www.jsdelivr.com/package/npm/untitled-pixi-live2d-engine)

## Notes

This file is a convenience summary and not a substitute for the original license texts or the upstream projects' terms.
