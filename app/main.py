from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routes
from app.api.routes import ocr, script, audio, video

app = FastAPI(
    title="Video Generation API",
    description="API for generating videos from slides using OCR, Gemini, ElevenLabs, and FFmpeg",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ocr.router, prefix="/api/ocr", tags=["OCR"])
app.include_router(script.router, prefix="/api/script", tags=["Script Generation"])
app.include_router(audio.router, prefix="/api/audio", tags=["Audio Generation"])
app.include_router(video.router, prefix="/api/video", tags=["Video Assembly"])

@app.get("/")
async def root():
    return {
        "message": "Video Generation API",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

