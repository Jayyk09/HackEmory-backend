import os
from pathlib import Path
from uuid import uuid4
import mimetypes
from typing import BinaryIO

import boto3
import psycopg2
from dotenv import load_dotenv  # pip install python-dotenv

BUCKET_NAME = "emory-hacks-video-bucket"

# ---- Load env (.env is one level up from this file) ----
BASE_DIR = Path(__file__).resolve().parent.parent  # HackEmory-backend/
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in environment/.env")

# Reuse one S3 client for the whole program
s3 = boto3.client("s3")  # uses your aws configure creds


def get_db_conn():
    """Create a new DB connection."""
    return psycopg2.connect(DATABASE_URL)


def upload_video_to_s3(file_obj: BinaryIO, original_filename: str, user_id: int) -> str:
    """
    Upload a file-like object to S3 under {user_id}/{uuid}{ext}
    and return the S3 key to store in your DB.
    """
    # Get extension from original filename (.mp4, .mov, .jpg, etc.)
    ext = Path(original_filename).suffix or ".mp4"

    # Guess MIME type, fallback to binary
    content_type, _ = mimetypes.guess_type(original_filename)
    if content_type is None:
        content_type = "application/octet-stream"

    # Generate a unique video id
    video_id = uuid4().hex

    # This is the S3 key (like a path inside the bucket)
    key = f"{user_id}/{video_id}{ext}"

    # Make sure we're at the start of the file
    file_obj.seek(0)

    # Upload the file object
    s3.upload_fileobj(
        Fileobj=file_obj,
        Bucket=BUCKET_NAME,
        Key=key,
        ExtraArgs={"ContentType": content_type},
    )

    return key


def add_video(
    user_id: int,
    file_obj: BinaryIO,
    original_filename: str,
    title: str | None = None,
    description: str | None = None,
) -> int:
    """
    High-level function:
    - uploads file object to S3
    - inserts row into videos table
    Returns the new video id.
    """
    s3_key = upload_video_to_s3(file_obj, original_filename, user_id)

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
            # row is a 1-tuple: (id,)
            video_id = row[0]
    finally:
        conn.close()

    return int(video_id)


def get_video_url(user_id: int, video_id: int) -> str:
    """
    Given a user_id and video_id:
    - look up the video's s3_key (ensuring it belongs to that user)
    - generate and return a presigned S3 URL
    """
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s3_key
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

    s3_key = row[0]

    # Generate a presigned URL to access the object
    presigned_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET_NAME, "Key": s3_key},
        ExpiresIn=3600,  # valid for 1 hour
    )

    return presigned_url


def main():
    # Demo only: open a local file as a file object
    user_id = 1  # replace with real user id in your app
    local_path = "~/Downloads/139-1398964_regions-bank-logo-png.jpg"
    local_path = Path(local_path).expanduser()
    original_filename = local_path.name

    with open(local_path, "rb") as f:
        # 1) Add video (upload + DB insert)
        video_id = add_video(
            user_id=user_id,
            file_obj=f,
            original_filename=original_filename,
            title="Test upload",
            description="Test video for user 1",
        )

    print("New video id:", video_id)

    # 2) Get ONLY the presigned URL using user_id + video_id
    url = get_video_url(user_id=user_id, video_id=video_id)
    print("Presigned URL to send to frontend:")
    print(url)


if __name__ == "__main__":
    main()
