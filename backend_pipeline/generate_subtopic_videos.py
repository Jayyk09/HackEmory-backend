#!/usr/bin/env python3
"""
Generate one video per subtopic transcript chunk.

Usage:
    python backend_pipeline/generate_subtopic_videos.py \
        --transcripts assets/subtopics.json \
        --background assets/audio/videos/minecraft.mp4 \
        --output-dir assets/output/subtopics
"""

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List
from save_to_db.save_video import add_video

from backend_pipeline.audio_generation.elevenLabs import (
    generate_audio_from_transcript,
    concatenate_audio_segments,
)
from backend_pipeline.video_assembly.ffMpeg import (
    create_video_with_audio_and_captions,
)


def slugify(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in value.strip())
    return safe[:64] or "subtopic"


def load_subtopics(path: Path) -> List[Dict[str, Any]]:
    with path.open("r") as f:
        data = json.load(f)

    if "subtopic_transcripts" in data:
        return data["subtopic_transcripts"]
    if "transcripts" in data:
        # Treat flat transcripts as single subtopic
        return [{"subtopic_title": "subtopic_1", "dialogue": data["transcripts"]}]
    raise ValueError("JSON must contain 'subtopic_transcripts' or 'transcripts'.")


def generate_videos_from_subtopic_list(
    subtopics: List[Dict[str, Any]],
    background_video: Path | str,
    output_dir: Path | str,
    audio_dir: Path | str,
    user_id: int,
) -> List[Dict[str, str]]:
    background_video = Path(background_video)
    output_dir = Path(output_dir)
    audio_dir = Path(audio_dir)

    if not subtopics:
        raise ValueError("No subtopics found in transcript file.")

    output_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for index, subtopic in enumerate(subtopics, start=1):
        slug = slugify(subtopic["subtopic_title"])
        print(f"\n=== Subtopic {index}/{len(subtopics)}: {subtopic['subtopic_title']} ===")

        transcripts_payload = {"transcripts": subtopic["dialogue"]}

        segment_dir = audio_dir / slug / "segments"
        segment_dir.mkdir(parents=True, exist_ok=True)

        print("🎙️  Generating audio segments…")
        audio_segments = generate_audio_from_transcript(
            transcripts_payload,
            output_dir=str(segment_dir),
        )

        audio_output = audio_dir / f"{slug}_full.mp3"
        print("🔗 Concatenating audio segments…")
        audio_result = concatenate_audio_segments(
            audio_segments,
            output_file=str(audio_output),
        )

        video_output = output_dir / f"{slug}.mp4"
        print("🎥 Creating video…")
        video_path = create_video_with_audio_and_captions(
            background_video=str(background_video),
            audio_file=audio_result["audio_file"],
            caption_timings=audio_result["timings"],
            output_file=str(video_output),
        )

        with video_output.open("rb") as f:
            video_id = add_video(
                user_id=user_id,
                file_obj=f,
                original_filename=video_output.name,
                title=subtopic["subtopic_title"],
                description=f"Subtopic {index}/{len(subtopics)}",
            )

        print(f"✅ Created and uploaded video_id {video_id}")

    return results


def generate_videos_for_subtopics(
    transcripts_path: Path,
    background_video: Path,
    output_dir: Path,
    audio_dir: Path,
    user_id: int,
) -> List[Dict[str, str]]:
    subtopics = load_subtopics(transcripts_path)
    return generate_videos_from_subtopic_list(
        subtopics=subtopics,
        background_video=background_video,
        output_dir=output_dir,
        audio_dir=audio_dir,
        user_id=user_id,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate per-subtopic videos.")
    parser.add_argument(
        "--transcripts",
        type=Path,
        required=True,
        help="Path to JSON file with subtopic_transcripts output.",
    )
    parser.add_argument(
        "--background",
        type=Path,
        required=True,
        help="Background video path (e.g., assets/audio/videos/minecraft.mp4).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("assets/output/subtopics"),
        help="Directory to store generated videos.",
    )
    parser.add_argument(
        "--audio-dir",
        type=Path,
        default=Path("assets/audio/subtopics"),
        help="Directory to store generated audio assets.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.transcripts.exists():
        raise FileNotFoundError(f"Transcript file not found: {args.transcripts}")
    if not args.background.exists():
        raise FileNotFoundError(f"Background video not found: {args.background}")

    user_id = 1
    results = generate_videos_for_subtopics(
        transcripts_path=args.transcripts,
        background_video=args.background,
        output_dir=args.output_dir,
        audio_dir=args.audio_dir,
        user_id=user_id,
    )

    print("\n=== Summary ===")
    for item in results:
        print(f"- {item['subtopic_title']}: {item['video_path']}")


if __name__ == "__main__":
    main()

