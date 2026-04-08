import json
import os
from contextlib import asynccontextmanager

import numpy as np
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pipeline import Pipeline

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


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    await websocket.accept()
    print("Frontend connected to WebSocket")
    current_state = "IDLE"
    audio_buffer = []
    chat_history = []

    try:
        while True:
            data = await websocket.receive()
            if "bytes" in data:
                if current_state not in ["IDLE", "LISTENING"]:
                    # AI is busy (THINKING or SPEAKING).
                    # Ignore these bytes and don't add them to the buffer.
                    continue

                chunk = data["bytes"]
                samples = np.frombuffer(chunk, dtype=np.int16)
                if samples.size == 0:
                    continue

                is_silent = pipeline.is_silent(samples)
                if current_state == "IDLE" and not is_silent:
                    current_state = "LISTENING"
                    await websocket.send_json({"state": "LISTENING"})
                audio_buffer.append(samples)

                if pipeline.is_user_speech_finalized(audio_buffer):
                    current_state = "THINKING"
                    await websocket.send_json({"state": "THINKING"})
                    full_audio_bytes = (
                        np.concatenate(audio_buffer).astype(np.int16).tobytes()
                    )
                    if STREAM_LLM_RESPONSES:
                        audio_buffer.clear()
                        async for pipeline_result in pipeline.orchestrate_streaming(
                            full_audio_bytes, chat_history
                        ):
                            if not pipeline_result:
                                continue

                            chat_history = pipeline_result.get("updated_history", [])
                            user_text = pipeline_result.get("user_text", "")
                            llm_response = pipeline_result.get("llm_response_text", "")
                            tts_audio_bytes = pipeline_result.get(
                                "tts_audio_bytes", b""
                            )

                            current_state = "SPEAKING"
                            await websocket.send_json(
                                {
                                    "state": "SPEAKING",
                                    "userText": user_text,
                                    "llmResponse": llm_response,
                                }
                            )
                            await websocket.send_bytes(tts_audio_bytes)
                    else:
                        pipeline_result = await pipeline.orchestrate(
                            full_audio_bytes, chat_history
                        )
                        if not pipeline_result:
                            continue

                        chat_history = pipeline_result.get("updated_history", [])
                        user_text = pipeline_result.get("user_text", "")
                        llm_response = pipeline_result.get("llm_response_text", "")
                        tts_audio_bytes = pipeline_result.get("tts_audio_bytes", b"")

                        current_state = "SPEAKING"
                        audio_buffer.clear()
                        await websocket.send_json(
                            {
                                "state": "SPEAKING",
                                "userText": user_text,
                                "llmResponse": llm_response,
                            }
                        )
                        await websocket.send_bytes(tts_audio_bytes)

            # Handle JSON Commands (like AUDIO_DONE)
            elif "text" in data:
                data = json.loads(data["text"])
                if data.get("type") == "AUDIO_DONE":
                    current_state = "IDLE"
                    await websocket.send_json({"state": "IDLE"})
                if data.get("type") == "MIC_STOPPED" and current_state == "LISTENING":
                    audio_buffer.clear()
                    current_state = "IDLE"
                    await websocket.send_json({"state": "IDLE"})

    except WebSocketDisconnect:
        print("Frontend disconnected")
    except RuntimeError as e:
        print(f"Server shutting down: {e}")
    except Exception as e:
        print(f"Unexpected error in WebSocket: {e}")
    finally:
        print("Cleaning up WebSocket resources")


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
