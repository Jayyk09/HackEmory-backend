import boto3
from uuid import uuid4
from pathlib import Path
import mimetypes

BUCKET_NAME = "emory-hacks-video-bucket"

# Reuse one client for the whole program
s3 = boto3.client("s3")  # uses your aws configure creds


def upload_video(local_path: str, user_id: str) -> str:
    """
    Upload a local file to S3 under videos/{user_id}/{uuid}{ext}
    and return the S3 key to store in your DB.
    """
    # Expand ~ to home directory
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
        ExtraArgs={
            "ContentType": content_type,
        },
    )

    return key


def main():
    user_id = "user_123"
    local_file = "~/Downloads/august_resume.pdf"  # test file

    key = upload_video(local_file, user_id)

    print("Uploaded to bucket:", BUCKET_NAME)
    print("S3 key (save this in DB):", key)


if __name__ == "__main__":
    main()
