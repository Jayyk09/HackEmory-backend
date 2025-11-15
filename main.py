import asyncio
from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from frontend_pipeline.script_generation.transcripts import extract_transcripts
from backend_pipeline.generate_subtopic_videos import (
    generate_videos_from_subtopic_list,
)

BACKGROUND_VIDEO = Path("assets/audio/videos/minecraft.mp4")
OUTPUT_DIR = Path("assets/output")
TEMP_UPLOAD_DIR = Path("tmp/uploads")
GENERATED_AUDIO_DIR = Path("assets/audio/generated")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class DialogueLine(BaseModel):
    caption: str
    speaker: str


class SubtopicPayload(BaseModel):
    subtopic_title: str
    dialogue: List[DialogueLine]


class SubtopicRequest(BaseModel):
    subtopic_transcripts: List[SubtopicPayload]


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


def _move_upload_to_disk(upload: UploadFile, destination: Path):
    with destination.open("wb") as buffer:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            buffer.write(chunk)
    upload.file.close()


async def _generate_videos(user_id, subtopics, prefix: str):
    session_id = uuid4().hex
    video_output_dir = OUTPUT_DIR / f"{prefix}_{session_id}"
    audio_output_dir = GENERATED_AUDIO_DIR / f"{prefix}_{session_id}"
    return await _run_blocking(
        generate_videos_from_subtopic_list,
        subtopics,
        str(BACKGROUND_VIDEO),
        str(video_output_dir),
        str(audio_output_dir),
        user_id,
    )

async def generate_video_from_subtopics(payload: SubtopicRequest, user_id: int = 1):
    _validate_background_video()

    if not payload.subtopic_transcripts:
        raise HTTPException(status_code=400, detail="subtopic_transcripts cannot be empty.")

    session_id = uuid4().hex
    video_results = await _generate_videos(
        user_id,
        [subtopic.model_dump() for subtopic in payload.subtopic_transcripts],
        prefix="direct",
    )

    return {
        "count": len(video_results),
        "results": video_results,
    }

@app.post("/generate-video")
async def generate_video(
    input_type: str = Form(..., description="audio|text|youtube"),
    user_id: int = Form(1, description="User ID for video ownership"),
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

        subtopics = await _run_blocking(
            extract_transcripts,
            transcript_source,
            transcript_type,
        )
        
        if not subtopics:
            detail = {
                "error": "model_returned_no_subtopics",
                "input_type": input_type,
                "content_preview": (transcript_source or "")[:280],
            }
            raise HTTPException(status_code=502, detail=detail)

        video_results = await _generate_videos(
            user_id,
            [subtopic.model_dump() for subtopic in subtopics],
            prefix="session",
        )

        return {
            "count": len(video_results),
            "results": video_results,
        }
    finally:
        if temp_audio_path and temp_audio_path.exists():
            temp_audio_path.unlink()