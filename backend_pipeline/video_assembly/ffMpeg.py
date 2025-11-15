import subprocess
import os
import json

def create_video_with_audio_and_captions(
    background_video,
    audio_file,
    caption_timings,
    output_file="assets/output/final_video.mp4",
    video_size=(1080, 1920)  # Portrait 9:16 for TikTok/Reels
):
    """
    Create a video with looping background, audio, and caption overlays.
    
    Args:
        background_video: Path to background video (minecraft.mp4)
        audio_file: Path to audio file
        caption_timings: List of timing dictionaries with start, end, caption, speaker
        output_file: Output video file path
        video_size: Tuple of (width, height) for output video
    
    Returns:
        Path to output video
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Get audio duration
    duration_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_file
    ]
    result = subprocess.run(duration_cmd, capture_output=True, text=True)
    audio_duration = float(result.stdout.strip())
    
    print(f"🎬 Creating video with duration: {audio_duration:.2f}s")
    
    # Build ffmpeg filter for captions
    caption_filters = []
    for timing in caption_timings:
        # Escape special characters in caption text
        caption_text = timing["caption"].replace("'", "'\\\\\\''").replace(":", "\\:")
        speaker = timing["speaker"]
        
        # Style for captions
        if speaker == "PETER":
            color = "white"
            bg_color = "0x00000080"  # Semi-transparent black
        else:
            color = "yellow"
            bg_color = "0x0000FF80"  # Semi-transparent blue
        
        # Create drawtext filter for this caption with word wrapping
        caption_filter = (
            f"drawtext=text='{caption_text}':"
            f"fontfile=/System/Library/Fonts/Supplemental/Arial Bold.ttf:"
            f"fontsize=48:"
            f"fontcolor={color}:"
            f"box=1:boxcolor={bg_color}:boxborderw=10:"
            f"x=(w-text_w)/2:"
            f"y=h-200:"
            f"enable='between(t,{timing['start']},{timing['end']})':"
            f"line_spacing=10:"
            f"text_w=min(w-40\\,text_w)"
        )
        caption_filters.append(caption_filter)
    
    # Combine all caption filters
    all_captions = ",".join(caption_filters) if caption_filters else ""
    
    # Build ffmpeg command
    cmd = [
        "ffmpeg", "-y",
        # Input: Loop background video
        "-stream_loop", "-1",
        "-i", background_video,
        # Input: Audio
        "-i", audio_file,
        # Video filters: scale, loop, and add captions
        "-filter_complex",
        f"[0:v]scale={video_size[0]}:{video_size[1]}:force_original_aspect_ratio=decrease,"
        f"pad={video_size[0]}:{video_size[1]}:(ow-iw)/2:(oh-ih)/2,"
        f"{all_captions}[v]",
        # Map outputs
        "-map", "[v]",
        "-map", "1:a",
        # Set duration to match audio
        "-t", str(audio_duration),
        # Output settings
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        # Metadata
        "-movflags", "+faststart",
        output_file
    ]
    
    print(f"🎥 Rendering video with {len(caption_timings)} caption overlays...")
    print(f"   Background: {background_video}")
    print(f"   Audio: {audio_file}")
    
    # Run ffmpeg
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Video created successfully: {output_file}")
        return output_file
    else:
        print(f"❌ Error creating video:")
        print(result.stderr)
        raise Exception(f"FFmpeg failed with return code {result.returncode}")

def get_video_info(video_path):
    """Get video duration and other info using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration:stream=width,height,codec_name",
        "-of", "json",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

if __name__ == "__main__":
    # Example usage
    print("FFmpeg video assembly module ready!")
    print("Use create_video_with_audio_and_captions() to generate videos.")

