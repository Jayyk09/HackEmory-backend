from pathlib import Path
from uuid import uuid4
import mimetypes
from typing import Dict, Any, List

import boto3

from main import get_db_conn  # <-- shared DB connection

BUCKET_NAME = "emory-hacks-video-bucket"

# Reuse one S3 client for the whole program
s3 = boto3.client("s3")  # uses your aws configure creds


def upload_video_to_s3(local_path: str, user_id: int) -> str:
    """
    Upload a local file to S3 under {user_id}/{uuid}{ext}
    and return the S3 key to store in your DB.
    """
    path = Path(local_path).expanduser()

    # Get extension (.mp4, .mov, .pdf, etc.). Default to .mp4 if none.
    ext = path.suffix or ".mp4"

    # Guess MIME type, fallback to binary
    content_type, _ = mimetypes.guess_type(str(path))
    if content_type is None:
        content_type = "application/octet-stream"

    # Generate a unique video id
    video_id = uuid4().hex

    # This is the S3 key (like a path inside the bucket)
    key = f"{user_id}/{video_id}{ext}"

    # Upload the file
    s3.upload_file(
        Filename=str(path),
        Bucket=BUCKET_NAME,
        Key=key,
        ExtraArgs={"ContentType": content_type},
    )

    return key


def add_video(
    user_id: int,
    local_path: str,
    title: str | None = None,
    description: str | None = None,
) -> int:
    """
    High-level function:
    - uploads file to S3
    - inserts row into videos table
    Returns the new video id.
    """
    s3_key = upload_video_to_s3(local_path, user_id)

    conn = get_db_conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO videos (user_id, s3_key, video_title, video_description)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
                """,
                (user_id, s3_key, title, description),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("INSERT INTO videos RETURNING id returned no row")
            video_id = row[0]
    finally:
        conn.close()

    return int(video_id)


def get_video(user_id: int, video_id: int) -> Dict[str, Any]:
    """
    Retrieve a video row by user_id and video_id, then:
    - look up its s3_key
    - generate a presigned S3 URL
    Returns a dict with DB fields + 'presigned_url'.
    Raises ValueError if not found.
    """
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, s3_key, video_title, video_description, created_at
                FROM videos
                WHERE id = %s AND user_id = %s;
                """,
                (video_id, user_id),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        raise ValueError("Video not found for given user_id and video_id")

    vid_id, user_id_db, s3_key, title, desc, created_at = row

    presigned_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET_NAME, "Key": s3_key},
        ExpiresIn=3600,  # valid for 1 hour
    )

    return {
        "id": vid_id,
        "user_id": user_id_db,
        "s3_key": s3_key,
        "video_title": title,
        "video_description": desc,
        "created_at": created_at,
        "presigned_url": presigned_url,
    }


def get_user_videos(
    user_id: int,
    offset: int = 0,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Return up to `limit` videos for a given user, starting at `offset`,
    each with a presigned URL.

    Ordered by newest first (created_at DESC, id DESC).
    """
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, s3_key, video_title, video_description, created_at
                FROM videos
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
                OFFSET %s
                LIMIT %s;
                """,
                (user_id, offset, limit),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    videos: List[Dict[str, Any]] = []
    for vid_id, s3_key, title, desc, created_at in rows:
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": s3_key},
            ExpiresIn=3600,  # 1 hour
        )
        videos.append(
            {
                "id": vid_id,
                "title": title,
                "description": desc,
                "presigned_url": presigned_url,
            }
        )

    return videos
