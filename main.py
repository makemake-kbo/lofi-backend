from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import pyaudio
import subprocess
from fastapi.middleware.cors import CORSMiddleware

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

def audio_streamer(file_path: str):
    process = subprocess.Popen(
        ["ffmpeg", "-re", "-i", file_path, "-f", "mp3", "-"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )
    
    try:
        while True:
            data = process.stdout.read(1024)
            if not data:
                break
            yield data
    except GeneratorExit:
        process.terminate()

@app.get("/stream")
async def stream_audio():
    file_path = "./the-flower-called-nowhere.m4a"
    return StreamingResponse(audio_streamer(file_path), media_type="audio/mp4")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)