from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import pyaudio
import subprocess
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

# Dictionary to keep track of listening time
clients_listening_time = {}

def audio_streamer(file_path: str, client_ip: str):
    process = subprocess.Popen(
        ["ffmpeg", "-re", "-i", file_path, "-f", "mp3", "-"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )
    
    start_time = datetime.now()
    
    try:
        while True:
            data = process.stdout.read(1024)
            if not data:
                break
            yield data
            
            # Update listening time
            elapsed_time = datetime.now() - start_time
            clients_listening_time[client_ip] = elapsed_time.total_seconds()
    except GeneratorExit:
        process.terminate()

@app.get("/stream")
async def stream_audio(request: Request):
    client_ip = request.client.host
    file_path = "./the-flower-called-nowhere.m4a"
    return StreamingResponse(audio_streamer(file_path, client_ip), media_type="audio/mp4")

@app.get("/listening-times")
async def get_listening_times():
    return clients_listening_time

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
