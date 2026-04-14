"""FastAPI entrypoint: static frontend, MLX pipeline, and realtime websocket."""

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pipeline import Pipeline
from session import WebSocketSession

HOST = "localhost"
PORT = 8100

# This controls whether to stream LLM responses, and subsequently TTS responses
STREAM_LLM_RESPONSES = True

# Get the absolute path of the directory where main.py is located
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# Define paths relative to the script location
# If the directory structure is:
# project/backend/main.py
# project/frontend/
FRONTEND_DIR = os.path.join(BACKEND_DIR, "..", "frontend")

pipeline = Pipeline(config_path=os.path.join(BACKEND_DIR, "config.yaml"))
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start MCP tool sessions on startup and tear them down on shutdown."""
    print("Initializing Pipeline and MCP servers...")
    await pipeline.initialize_mcp()
    print("AI and MCP ready.")

    yield  # The application runs here

    print("Shutting down. Closing MCP connections...")
    await pipeline.close_mcp()
    print("Cleanup complete")


app = FastAPI(lifespan=lifespan)

# Enable CORS so the browser doesn't block requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend files (index.html, main.js, models)
# This makes the app available at http://{HOST}:{PORT}/client/index.html
if not os.path.exists(FRONTEND_DIR):
    print(f"ERROR: Frontend directory not found at {FRONTEND_DIR}")
else:
    app.mount(
        "/client", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend"
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Browser websocket: PCM uplink, JSON downlink, and client control messages."""
    await websocket.accept()
    logger.info("Frontend connected to websocket")
    session = WebSocketSession(
        pipeline=pipeline,
        stream_llm_responses=STREAM_LLM_RESPONSES,
        logger=logger,
    )

    try:
        while True:
            data = await websocket.receive()
            await session.handle_message(websocket, data)

    except WebSocketDisconnect:
        logger.info("Frontend disconnected from websocket")
    except RuntimeError as e:
        logger.info("Server shutting down: %s", e)
    except Exception as e:
        logger.exception("Unexpected websocket error: %s", e)
    finally:
        logger.info("Cleaning up websocket resources")


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
