# AI Character

Real-time voice AI assistant with a Live2D frontend and FastAPI websocket backend.

## Prerequisites

- Python `3.12`
- `uv` package manager
- macOS (Apple Silicon recommended for `mlx-*` dependencies)

## Setup

1. Install dependencies:
   - `uv sync --dev`
2. Create backend config:
   - `cp backend/config.yaml.example backend/config.yaml`
3. Set required environment variables referenced by `backend/config.yaml`.

## Run Locally

- Start the app:
  - `uv run python backend/main.py`
- Open:
  - `http://localhost:8100/client/index.html`

## Development Commands

- Lint: `uv run ruff check .`
- Format check: `uv run ruff format --check .`
- Type-check: `uv run mypy`
- Tests: `uv run pytest`
- Run all quality gates: `make validate`

## Dependency Management

`pyproject.toml` is the source of truth for dependencies.

- Sync the environment from lock/manifest: `uv sync --dev`
- Regenerate `requirements.txt` when needed:
  - `./scripts/sync_requirements.sh`

## Troubleshooting

- If websocket is offline in UI, verify backend is running on `localhost:8100`.
- If microphone streaming fails, confirm browser mic permission is granted.
- If model loading fails, verify files under `frontend/models/Haru`.

## Credits

Uses the Live2D PIXI Plugin [untitled-pixi-live2d-engine](https://github.com/Untitled-Story/untitled-pixi-live2d-engine).
