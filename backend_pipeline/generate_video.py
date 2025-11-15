#!/usr/bin/env python3
"""
Complete video generation pipeline:
1. Load transcript from JSON
2. Generate audio using ElevenLabs
3. Create video with looping background, audio, and captions
"""

import json
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend_pipeline.audio_generation.elevenLabs import (
    generate_audio_from_transcript,
    concatenate_audio_segments
)
from backend_pipeline.video_assembly.ffMpeg import (
    create_video_with_audio_and_captions
)

def generate_complete_video(
    transcript_json_path,
    background_video_path,
    output_video_path="assets/output/final_video.mp4"
):
    """
    Complete pipeline to generate a video from transcript JSON.
    
    Args:
        transcript_json_path: Path to JSON file with transcripts
        background_video_path: Path to background video (e.g., minecraft.mp4)
        output_video_path: Path for final output video
    
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
    
    # Step 2: Generate audio
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

if __name__ == "__main__":
    # Default paths
    TRANSCRIPT_JSON = "assets/sample.json"
    BACKGROUND_VIDEO = "assets/audio/videos/minecraft.mp4"
    OUTPUT_VIDEO = "assets/output/final_video.mp4"
    
    # Check if files exist
    if not os.path.exists(TRANSCRIPT_JSON):
        print(f"❌ Error: Transcript file not found: {TRANSCRIPT_JSON}")
        sys.exit(1)
    
    if not os.path.exists(BACKGROUND_VIDEO):
        print(f"❌ Error: Background video not found: {BACKGROUND_VIDEO}")
        sys.exit(1)
    
    # Generate video
    try:
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

