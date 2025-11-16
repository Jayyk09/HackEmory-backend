import asyncio
import re
from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Query

from save_to_db.save_video import get_user_videos
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from frontend_pipeline.script_generation.transcripts import extract_transcripts
from backend_pipeline.generate_subtopic_videos import (
    generate_videos_from_subtopic_list,
)
import save_to_db.account_service as account_service

BACKGROUND_VIDEO = Path("assets/videos/minecraft.mp4")
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

# CORS settings so React (localhost:3000) can talk to this API
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # or ["*"] during dev if you want to be lazy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


def _is_youtube_url(text: str) -> bool:
    """Check if a string is a YouTube URL."""
    if not text:
        return False
    youtube_patterns = [
        r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/',
        r'youtube\.com/watch\?v=',
        r'youtu\.be/',
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in youtube_patterns)


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
    input_type: str = Form("auto", description="audio|text|youtube|auto (auto-detects from content)"),
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
    supported = {"audio", "text", "youtube", "auto"}
    if input_type not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"input_type must be one of {', '.join(sorted(supported))}",
        )

    temp_audio_path = None
    transcript_source = None
    transcript_type = None

    try:
        # Auto-detect input type
        if input_type == "auto":
            if file:
                input_type = "audio"
            elif content and _is_youtube_url(content):
                input_type = "youtube"
            elif content:
                input_type = "text"
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Unable to auto-detect input type. Please provide either a file or content."
                )
        
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




def get_current_user_id() -> int:
    # TODO: replace with your real auth
    return 1


@app.get("/videos")
async def list_user_videos(
    start: int = Query(0, ge=0, description="Index into the user's video list"),
    user_id: int = Depends(get_current_user_id),
):
    """
    Return up to 5 videos for the current user, starting at index `start`.
    Each video includes a presigned_url usable by the frontend.
    """
    try:
        videos = await _run_blocking(
            get_user_videos,
            user_id,
            start,
            5,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # get_user_videos already returns: id, title, description, presigned_url
    return {
        "start": start,
        "count": len(videos),
        "videos": videos,
    }


# ============ Account CRUD Endpoints ============

class UserCreate(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserUpdatePassword(BaseModel):
    new_password: str


@app.post("/accounts")
async def register_account(user: UserCreate):
    """Create a new user account."""
    result = await _run_blocking(account_service.create_user, user.email, user.password)
    if result is None:
        raise HTTPException(status_code=400, detail="Email already exists")
    return {"message": "Account created", "user": result}


@app.post("/accounts/login")
async def login_account(credentials: UserLogin):
    """Authenticate user and return user info."""
    result = await _run_blocking(account_service.authenticate_user, credentials.email, credentials.password)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful", "user": result}


@app.get("/accounts/{user_id}")
async def get_account(user_id: int):
    """Get user account by ID."""
    result = await _run_blocking(account_service.get_user_by_id, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@app.get("/accounts")
async def list_accounts():
    """List all user accounts."""
    users = await _run_blocking(account_service.list_all_users)
    return {"count": len(users), "users": users}
