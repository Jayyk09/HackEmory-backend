import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, UploadFile, File, Form, HTTPException

from frontend_pipeline.script_generation.transcripts import extract_transcripts
from backend_pipeline.audio_generation.elevenLabs import (
    generate_audio_from_transcript,
    concatenate_audio_segments,
)
from backend_pipeline.video_assembly.ffMpeg import (
    create_video_with_audio_and_captions,
)

app = FastAPI(
    title="Video Generation API",
    description="API for generating videos from slides",
    version="1.0.0"
)

BACKGROUND_VIDEO = Path("assets/audio/videos/minecraft.mp4")
OUTPUT_DIR = Path("assets/output")
TEMP_UPLOAD_DIR = Path("tmp/uploads")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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


async def _run_blocking(func, *args, **kwargs):
    return await asyncio.to_thread(func, *args, **kwargs)


def _validate_background_video():
    if not BACKGROUND_VIDEO.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Background video not found at {BACKGROUND_VIDEO}",
        )


def _build_transcript_payload(transcripts):
    if not transcripts:
        raise HTTPException(status_code=502, detail="No transcripts returned from model")
    return {"transcripts": transcripts}


def _move_upload_to_disk(upload: UploadFile, destination: Path):
    with destination.open("wb") as buffer:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            buffer.write(chunk)
    upload.file.close()


@app.post("/generate-video")
async def generate_video(
    input_type: str = Form(..., description="audio|text|youtube"),
    content: str | None = Form(
        None,
        description="Text, YouTube URL, or other string content depending on input_type",
    ),
    file: UploadFile | None = File(
        None,
        description="Used when input_type is audio (MP3 upload).",
    ),
):
    input_type = input_type.lower()
    supported = {"audio", "text", "youtube"}
    if input_type not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"input_type must be one of {', '.join(sorted(supported))}",
        )

    temp_audio_path = None
    transcript_source = None
    transcript_type = None

    try:
        if input_type == "audio":
            if not file:
                raise HTTPException(status_code=400, detail="Audio file is required.")
            suffix = Path(file.filename or "").suffix or ".mp3"
            temp_audio_path = TEMP_UPLOAD_DIR / f"{uuid4().hex}{suffix}"
            _move_upload_to_disk(file, temp_audio_path)
            transcript_source = str(temp_audio_path)
            transcript_type = "audio/mp3"
        elif input_type == "text":
            if not content:
                raise HTTPException(status_code=400, detail="content is required for text input_type.")
            transcript_source = content
            transcript_type = "text"
        elif input_type == "youtube":
            if not content:
                raise HTTPException(status_code=400, detail="YouTube URL is required in content field.")
            transcript_source = content
            transcript_type = "youtube"

        transcripts = await _run_blocking(extract_transcripts, transcript_source, transcript_type)
        transcript_payload = _build_transcript_payload(transcripts)

        audio_segments = await _run_blocking(generate_audio_from_transcript, transcript_payload)
        audio_result = await _run_blocking(concatenate_audio_segments, audio_segments)

        _validate_background_video()
        output_path = OUTPUT_DIR / f"video_{uuid4().hex}.mp4"
        video_path = await _run_blocking(
            create_video_with_audio_and_captions,
            str(BACKGROUND_VIDEO),
            audio_result["audio_file"],
            audio_result["timings"],
            str(output_path),
        )

        return {
            "video_path": video_path,
            "audio_file": audio_result["audio_file"],
            "duration_seconds": audio_result["total_duration"],
            "segments": len(audio_result["timings"]),
        }
    finally:
        if temp_audio_path and temp_audio_path.exists():
            temp_audio_path.unlink()

