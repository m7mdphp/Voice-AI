"""
Tiryaq Voice AI - Production Backend
SaaS-grade Voice Assistant Backend (Najm AI Standard)
Version: 9.0.0 - Dependency Hell Fix
"""

import asyncio
import json
import struct
import math
import time
import wave
import tempfile
import os
import sys
import functools
from typing import Dict, Optional
from contextvars import ContextVar
from pathlib import Path

# Ensure backend directory is in path for imports
BACKEND_DIR = Path(__file__).parent.resolve()
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from openai import OpenAI
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from services.agent_engine import GroqEngine
from services.firestore_memory import MemoryManager
from config import settings

# ================= Logging =================
# Ensure logs directory exists
LOGS_DIR = BACKEND_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger.add(
    str(LOGS_DIR / "tiryaq_{time}.log"),
    rotation="1 day",
    retention="7 days",
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {message}",
    enqueue=True  # Thread-safe logging
)

# ================= App Initialization =================
app = FastAPI(
    title="Tiryaq Voice Elite",
    version="9.0.0",
    description="SaaS-grade Voice Assistant - Najm AI Standard"
)

# Mounting static files for unified deployment
# Priority: /app/frontend -> local frontend directory
STATIC_DIRS = [
    Path("/app/frontend"),
    BACKEND_DIR.parent / "frontend",
]

for static_dir in STATIC_DIRS:
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f"Static files mounted from: {static_dir}")
        break

# ================= Routes =================
@app.get("/")
async def get_index():
    """Elite Guard: Unified Static Discovery with fallback"""
    search_paths = [
        "/app/frontend/voice_assistant_v3.html",
        str(BACKEND_DIR.parent / "frontend" / "voice_assistant_v3.html"),
        "voice_assistant_v3.html",
    ]
    
    for path in search_paths:
        if Path(path).exists():
            return FileResponse(path, media_type="text/html")
    
    return JSONResponse({
        "message": "Tiryaq Elite V9.0 is running",
        "status": "active",
        "docs": "/docs",
        "health": "/health"
    })

@app.get("/health")
async def health():
    """Health check endpoint for deployment validation"""
    return {
        "status": "healthy",
        "service": "Tiryaq Voice AI",
        "version": "9.0.0",
        "env": settings.ENV,
        "python": sys.version.split()[0]
    }

@app.get("/ws/debug")
async def ws_debug():
    """Diagnostic endpoint to check headers and environment."""
    return {
        "env_port": os.getenv("PORT"),
        "settings_port": settings.PORT,
        "app_name": settings.APP_NAME,
        "mode": "Elite V9.0",
        "status": "online",
        "backend_dir": str(BACKEND_DIR),
        "data_exists": (BACKEND_DIR / "data").exists()
    }

@app.websocket("/ws/echo")
async def websocket_echo(ws: WebSocket):
    """Simple echo endpoint to verify WS protocol upgrades."""
    await ws.accept()
    await ws.send_text("HANDSHAKE_SUCCESS")
    await ws.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Note: We don't initialize a global engine here anymore to support multiple tenants dynamically.
# Each tenant will have its own engine instance during the session for proper persona isolation.
memory_manager = MemoryManager()
request_id_var: ContextVar[str] = ContextVar("request_id", default="unknown")

# ================= Audio / VAD Constants (Elite V8.2 Calibrated) =================
SAMPLE_RATE = 16000
VOICE_THRESHOLD = 300   # Elite Sensitivity: Lowered for quiet voices
SILENCE_THRESHOLD = 150
SILENCE_DURATION_LIMIT = 1.5 
MIN_SPEECH_DURATION = 0.5    
MIN_BUFFER_SIZE = 8000   # Minimum 250ms of audio buffer


# ================= Session State Management =================
class SessionState:
    def __init__(self):
        self.processing = False
        self.speaking = False


# ================= Utilities =================
def calculate_rms(chunk: bytes) -> int:
    if not chunk: return 0
    count = len(chunk) // 2
    try:
        shorts = struct.unpack("<" + "h" * count, chunk)
        return int(math.sqrt(sum(s * s for s in shorts) / count))
    except Exception:
        return 0


class LatencyTracker:
    def __init__(self, phase: str):
        self.phase = phase
        self.start = None

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args):
        duration = (time.time() - self.start) * 1000
        logger.bind(request_id=request_id_var.get()).info(
            f"{self.phase}: {duration:.2f}ms"
        )


# ================= Speech-to-Text (STT) =================
def _transcribe_sync(audio: bytes, api_key: str) -> str:
    path = None
    try:
        # Najm Standard: Anti-Hallucination Padding
        # Add 200ms of silence at start/end to ground Whisper
        silence_padding = b'\x00' * (SAMPLE_RATE // 5 * 2) # 200ms * 2 bytes/sample
        processed_audio = silence_padding + audio + silence_padding
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
            with wave.open(path, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(SAMPLE_RATE)
                w.writeframes(processed_audio)

        client = OpenAI(api_key=api_key)
        with open(path, "rb") as audio_file:
            res = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ar"
            )
        return res.text or ""
    except Exception as e:
        logger.error(f"Whisper error: {e}")
        return ""
    finally:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except:
                pass


async def transcribe_audio(audio: bytearray) -> str:
    with LatencyTracker("Whisper_STT"):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            functools.partial(
                _transcribe_sync,
                bytes(audio),
                settings.OPENAI_API_KEY
            )
        )


# ================= WebSocket Outbound Queue =================
async def websocket_sender(ws: WebSocket, queue: asyncio.Queue):
    try:
        while True:
            msg = await queue.get()
            
            # Use appropriate send method based on message type
            if isinstance(msg, bytes):
                await ws.send_bytes(msg)
            else:
                await ws.send_json(msg)
                
            queue.task_done()
    except (WebSocketDisconnect, asyncio.CancelledError):
        logger.debug("Sender task cancelled")
    except Exception as e:
        logger.error(f"Sender error: {e}")


# ================= Core AI Pipeline =================
# ================= Core AI Pipeline =================
async def process_audio_buffer(
    send_queue: asyncio.Queue,
    audio: bytearray,
    context: Dict,
    state: SessionState,
    tenant_engine: GroqEngine
):
    """
    Najm AI Standard: Non-blocking audio pipeline.
    Processing transcription -> LLM RAG -> TTS PCM Streaming.
    """
    # GATING: Ensure we don't process if already thinking or IF AI is still playing audio
    if state.processing or state.speaking:
        return

    state.processing = True
    start_time = time.time()
    request_id = request_id_var.get()

    try:
        # 1. Start thinking state
        await send_queue.put({"type": "state", "state": "thinking"})

        # 2. Transcription (OpenAI Whisper via Executor)
        text = await transcribe_audio(audio)
        if not text.strip():
            logger.bind(request_id=request_id).debug("Empty transcription, skipping.")
            state.processing = False
            await send_queue.put({"type": "state", "state": "listening"})
            return

        # 3. Visual Feedback (User Text)
        await send_queue.put({"type": "user_text", "content": text})
        logger.bind(request_id=request_id).info(f"User: {text}")

        # 4. Process Request via RAG Engine
        collected_text = ""
        first_audio = True

        async for event in tenant_engine.process_request(text, context):
            if event["type"] == "audio":
                if first_audio:
                    state.speaking = True
                    await send_queue.put({"type": "audio_start"})
                    first_audio = False
                await send_queue.put(event["content"]) # Raw PCM_16000 bytes

            elif event["type"] == "text":
                collected_text += event["content"]
                await send_queue.put({"type": "text", "content": event["content"]})

        # 5. Context Persistence
        if "history" not in context:
            context["history"] = []
        context["history"].append({"role": "user", "content": text})
        context["history"].append({"role": "assistant", "content": collected_text})
        context["history"] = context["history"][-6:] # Rolling memory

        # 6. Finalize Interaction
        await send_queue.put({"type": "audio_end"})
        
        duration = (time.time() - start_time) * 1000
        logger.bind(request_id=request_id).success(f"Interaction Complete: {duration:.2f}ms")

    except Exception as e:
        logger.bind(request_id=request_id).error(f"Pipeline Error: {e}")
        state.speaking = False
    finally:
        state.processing = False


# ================= WebSocket Endpoint =================
@app.websocket("/ws/session/{tenant_id}/{user_id}")
async def websocket_endpoint(ws: WebSocket, tenant_id: str, user_id: str):
    # Enhanced Handshake Logging
    headers = dict(ws.headers)
    logger.info(f"WS Handshake Start | Path: {ws.url.path} | Protocol: {headers.get('x-forwarded-proto')} | Host: {headers.get('host')}")
    
    try:
        await ws.accept()
        logger.success(f"WS Accepted | {tenant_id} | {user_id}")
    except Exception as e:
        logger.error(f"WS Accept Failed: {e}")
        return

    session_id = f"{tenant_id}-{user_id}-{int(time.time())}"
    token = request_id_var.set(session_id)

    # DYNAMIC: Create engine instance for THIS tenant and session
    # This ensures correct persona config.json is loaded!
    try:
        tenant_engine = GroqEngine(tenant_id=tenant_id)
        logger.info(f"Initialized dynamic engine for tenant: {tenant_id}")
    except Exception as e:
        logger.error(f"Failed to load engine for tenant {tenant_id}: {e}")
        await ws.close(code=4001)
        return

    logger.info(f"Connected {session_id}")

    context = await memory_manager.get_user_context(tenant_id, user_id)
    context.update({"tenant_id": tenant_id, "user_id": user_id})

    send_queue = asyncio.Queue()
    sender_task = asyncio.create_task(websocket_sender(ws, send_queue))

    state = SessionState()

    # Audio context is managed via 'playback_done' signal for VAD gating

    buffer = bytearray()
    silence_start = None
    is_speaking = False

    try:
        while True:
            # استقبال الرسالة بأمان لمنع الـ RuntimeError
            message = await ws.receive()
            
            if message["type"] == "websocket.disconnect":
                break

            # معالجة بيانات الصوت الخام (Binary)
            if "bytes" in message and not state.speaking:
                chunk = message["bytes"]
                rms = calculate_rms(chunk)

                if rms > VOICE_THRESHOLD:
                    is_speaking = True
                    silence_start = None
                    buffer.extend(chunk)

                elif rms <= SILENCE_THRESHOLD and is_speaking:
                    if silence_start is None:
                        silence_start = time.time()
                        
                    if time.time() - silence_start >= SILENCE_DURATION_LIMIT:
                        if len(buffer) >= MIN_BUFFER_SIZE:
                            # معالجة الصوت في تاسك منفصلة لضمان استمرارية الاستقبال
                            asyncio.create_task(process_audio_buffer(
                                send_queue,
                                buffer[:],
                                context,
                                state,
                                tenant_engine # Pass the dynamically loaded engine
                            ))
                        buffer.clear()
                        is_speaking = False
                        silence_start = None

            # معالجة الرسائل النصية
            elif "text" in message:
                try:
                    data = json.loads(message["text"])
                    if data.get("type") == "playback_done":
                        logger.debug("Client finished playback, reopening mic")
                        state.speaking = False
                        await send_queue.put({"type": "state", "state": "listening"})
                    elif data.get("type") == "ping":
                        await send_queue.put({"type": "pong"})
                except Exception as e:
                    logger.warning(f"Failed to parse text message: {e}")

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket Loop Error for {session_id}: {e}")
    finally:
        sender_task.cancel()
        request_id_var.reset(token)
        logger.info(f"Finalized session {session_id}")


# ================= Health Check =================
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "Tiryaq Voice AI",
        "version": "2.2.0"
    }


# ================= Execution =================
if __name__ == "__main__":
    import uvicorn
    
    # Priority: Command line argument -> Environment variable -> Default settings
    port = settings.PORT
    if "--port" in sys.argv:
        try:
            port = int(sys.argv[sys.argv.index("--port") + 1])
        except (ValueError, IndexError):
            pass
    elif os.getenv("PORT"):
        port = int(os.getenv("PORT"))

    logger.info(f"Starting {settings.APP_NAME} on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)