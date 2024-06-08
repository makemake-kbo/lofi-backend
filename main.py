import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import subprocess
from fastapi.middleware.cors import CORSMiddleware
from threading import Thread, Event
import time
from collections import deque
from datetime import datetime, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
CHUNK_SIZE = 1024
FILE_PATH = "./the-flower-called-nowhere.m4a"

# Shared buffer and synchronization primitives
buffer = deque()
buffer_event = Event()

# Dictionary to keep track of listening time and points
clients_listening_time = {}
clients_points = {}
clients_last_update = {}

# Configure logging
logging.basicConfig(level=logging.INFO)

def audio_streamer():
    while True:
        process = subprocess.Popen(
            ["ffmpeg", "-re", "-i", FILE_PATH, "-f", "mp3", "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        while True:
            data = process.stdout.read(CHUNK_SIZE)
            if not data:
                break
            buffer.append(data)
            if len(buffer) > 10 * CHUNK_SIZE:  # Limit buffer size to 10 chunks
                buffer.popleft()
            buffer_event.set()
        process.terminate()

def client_streamer():
    while True:
        if buffer:
            data = buffer.popleft()
            for client in clients:
                try:
                    client.write(data)
                except Exception as e:
                    logging.info(f"Removing client due to error: {e}")
                    clients.remove(client)
            buffer_event.clear()
        else:
            buffer_event.wait()

@app.on_event("startup")
async def startup_event():
    logging.info("Starting audio streamer thread...")
    streamer_thread = Thread(target=audio_streamer, daemon=True)
    streamer_thread.start()

@app.get("/stream")
async def stream_audio(request: Request):
    uuid = request.query_params.get("uuid")
    if not uuid:
        raise HTTPException(status_code=400, detail="UUID is required")

    logging.info(f"Client connected: {uuid}")

    def generate():
        start_time = datetime.now()
        clients_last_update[uuid] = start_time
        while True:
            if buffer:
                data = buffer.popleft()
                yield data

                # Update listening time and points
                elapsed_time = datetime.now() - start_time
                clients_listening_time[uuid] = elapsed_time.total_seconds()

                # Check if 30 seconds have passed to update points
                if datetime.now() - clients_last_update[uuid] >= timedelta(seconds=30):
                    clients_points[uuid] = clients_points.get(uuid, 0) + 1
                    clients_last_update[uuid] = datetime.now()
            else:
                buffer_event.wait()
    
    return StreamingResponse(generate(), media_type="audio/mpeg")

@app.get("/points")
async def get_points(uuid: str):
    if uuid not in clients_points:
        raise HTTPException(status_code=404, detail="Client not found")
    return JSONResponse({"points": clients_points[uuid]})

@app.get("/listening-times")
async def get_listening_times():
    return clients_listening_time

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
