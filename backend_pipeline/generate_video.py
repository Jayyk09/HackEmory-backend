#!/usr/bin/env python3
"""
Complete video generation pipeline:
1. Load transcript from JSON
2. Generate audio using ElevenLabs
3. Create video with looping background, audio, and captions
"""

import json
import os
import random
import sys
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend_pipeline.audio_generation.elevenLabs import (
    generate_audio_from_transcript,
    concatenate_audio_segments
)
from backend_pipeline.video_assembly.ffMpeg import (
    create_video_with_audio_and_captions
)
from backend_pipeline.generate_subtopic_videos import (
    generate_videos_from_subtopic_list,
)


def get_random_background_video(videos_dir="assets/videos"):
    """
    Randomly select a background video from the videos directory.
    Returns the path to the selected video.
    """
    videos_path = Path(videos_dir)
    
    if not videos_path.exists():
        raise FileNotFoundError(f"Background videos directory not found at {videos_dir}")
    
    # Get all .mp4 files from the videos directory
    video_files = list(videos_path.glob("*.mp4"))
    
    if not video_files:
        raise FileNotFoundError(f"No background videos found in {videos_dir}")
    
    # Randomly select one video
    selected_video = random.choice(video_files)
    print(f"🎥 Selected background video: {selected_video.name}")
    
    return str(selected_video)


def generate_complete_video(
    transcript_json_path,
    background_video_path,
    output_video_path="assets/output/final_video.mp4",
    skip_audio_generation=True
):
    """
    Complete pipeline to generate a video from transcript JSON.
    
    Args:
        transcript_json_path: Path to JSON file with transcripts
        background_video_path: Path to background video (e.g., minecraft.mp4)
        output_video_path: Path for final output video
        skip_audio_generation: If True, use existing audio segments if available
    
    Returns:
        Path to final video file
    """
    print("=" * 60)
    print("🎬 VIDEO GENERATION PIPELINE")
    print("=" * 60)
    
    # Step 1: Load transcript
    print("\n📖 Step 1: Loading transcript...")
    with open(transcript_json_path, "r") as f:
        transcript_data = json.load(f)
    print(f"   Loaded {len(transcript_data['transcripts'])} transcript segments")
    
    # Step 2: Generate audio or use existing
    segments_dir = "assets/audio/segments"
    existing_segments = []
    
    if skip_audio_generation and os.path.exists(segments_dir):
        # Check for existing audio segments
        segment_files = sorted([f for f in os.listdir(segments_dir) if f.startswith("segment_") and f.endswith(".mp3")])
        if segment_files:
            print(f"\n🎙️  Step 2: Found {len(segment_files)} existing audio segments, skipping generation...")
            for idx, segment in enumerate(transcript_data['transcripts']):
                speaker = segment["speaker"]
                segment_file = os.path.join(segments_dir, f"segment_{idx:03d}_{speaker.lower()}.mp3")
                if os.path.exists(segment_file):
                    existing_segments.append({
                        "index": idx,
                        "file": segment_file,
                        "caption": segment["caption"],
                        "speaker": segment["speaker"]
                    })
            audio_segments = existing_segments
            print(f"   ✅ Using {len(audio_segments)} existing segments")
        else:
            print("\n🎙️  Step 2: No existing segments found, generating audio from transcripts...")
            audio_segments = generate_audio_from_transcript(transcript_data)
    else:
        print("\n🎙️  Step 2: Generating audio from transcripts...")
        audio_segments = generate_audio_from_transcript(transcript_data)
    
    # Step 3: Concatenate audio
    print("\n🔗 Step 3: Concatenating audio segments...")
    audio_result = concatenate_audio_segments(audio_segments)
    
    # Save timing data for reference
    timing_file = "assets/audio/caption_timings.json"
    with open(timing_file, "w") as f:
        json.dump(audio_result, f, indent=2)
    print(f"   📄 Saved timing data: {timing_file}")
    
    # Step 4: Create video with captions
    print("\n🎥 Step 4: Creating video with audio and captions...")
    final_video = create_video_with_audio_and_captions(
        background_video=background_video_path,
        audio_file=audio_result["audio_file"],
        caption_timings=audio_result["timings"],
        output_file=output_video_path
    )
    
    print("\n" + "=" * 60)
    print("✨ VIDEO GENERATION COMPLETE!")
    print("=" * 60)
    print(f"📹 Output: {final_video}")
    print(f"⏱️  Duration: {audio_result['total_duration']:.2f} seconds")
    print(f"📝 Segments: {len(audio_result['timings'])}")
    print("=" * 60)
    
    return final_video


def generate_multi_videos(
    subtopics,
    background_video_path,
    output_base_dir="assets/output/subtopics",
    audio_base_dir="assets/audio/subtopics"
):
    print("=" * 60)
    print("🎬 MULTI VIDEO GENERATION PIPELINE")
    print("=" * 60)

    session_id = uuid4().hex
    video_dir = Path(output_base_dir) / f"batch_{session_id}"
    audio_dir = Path(audio_base_dir) / f"batch_{session_id}"

    video_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)

    results = generate_videos_from_subtopic_list(
        subtopics=subtopics,
        background_video=background_video_path,
        output_dir=str(video_dir),
        audio_dir=str(audio_dir),
    )

    print("\n" + "=" * 60)
    print("✨ MULTI VIDEO GENERATION COMPLETE!")
    print("=" * 60)
    print(f"📂 Video directory: {video_dir}")
    for item in results:
        print(f"- {item['subtopic_title']}: {item['video_path']}")
    print("=" * 60)

    return results

if __name__ == "__main__":
    # Default paths
    TRANSCRIPT_JSON = os.environ.get("TRANSCRIPT_JSON", "assets/sample.json")
    
    # If BACKGROUND_VIDEO is not set, randomly select one
    if "BACKGROUND_VIDEO" in os.environ:
        BACKGROUND_VIDEO = os.environ.get("BACKGROUND_VIDEO")
    else:
        try:
            BACKGROUND_VIDEO = get_random_background_video()
        except FileNotFoundError as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    OUTPUT_VIDEO = os.environ.get("OUTPUT_VIDEO", "assets/output/final_video.mp4")
    
    # Check if files exist
    if not os.path.exists(TRANSCRIPT_JSON):
        print(f"❌ Error: Transcript file not found: {TRANSCRIPT_JSON}")
        sys.exit(1)
    
    if not os.path.exists(BACKGROUND_VIDEO):
        print(f"❌ Error: Background video not found: {BACKGROUND_VIDEO}")
        sys.exit(1)
    
    with open(TRANSCRIPT_JSON, "r") as f:
        transcript_json = json.load(f)
    
    try:
        if "subtopic_transcripts" in transcript_json:
            results = generate_multi_videos(
                subtopics=transcript_json["subtopic_transcripts"],
                background_video_path=BACKGROUND_VIDEO,
            )
            print(f"\n🎉 Success! Generated {len(results)} videos.")
        else:
            final_video = generate_complete_video(
                transcript_json_path=TRANSCRIPT_JSON,
                background_video_path=BACKGROUND_VIDEO,
                output_video_path=OUTPUT_VIDEO
            )
            print(f"\n🎉 Success! Watch your video at: {final_video}")
    except Exception as e:
        print(f"\n❌ Error during video generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

