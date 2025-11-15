from fastapi import FastAPI

app = FastAPI(
    title="Video Generation API",
    description="API for generating videos from slides",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "message": "Video Generation API",
        "status": "running",
        "pipeline": {
            "frontend": ["OCR", "Script Generation"],
            "backend": ["Audio Generation", "Video Assembly"]
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

