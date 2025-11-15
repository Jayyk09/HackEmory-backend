import subprocess
import os
import json
import textwrap

def wrap_caption_text(text, max_chars=32):
    """Wrap caption text to a maximum characters per line (word-aware)."""
    wrapped_lines = textwrap.wrap(text, width=max_chars)
    return "\n".join(wrapped_lines) if wrapped_lines else text


def create_video_with_audio_and_captions(
    background_video,
    audio_file,
    caption_timings,
    output_file="assets/output/final_video.mp4",
    video_size=(1080, 1920),  # Portrait 9:16 for TikTok/Reels
    peter_image="assets/characters/peter.png",
    stewie_image="assets/characters/stewie.png"
):
    """
    Create a video with looping background, audio, caption overlays, and character images.
    
    Args:
        background_video: Path to background video (minecraft.mp4)
        audio_file: Path to audio file
        caption_timings: List of timing dictionaries with start, end, caption, speaker
        output_file: Output video file path
        video_size: Tuple of (width, height) for output video
        peter_image: Path to Peter character image
        stewie_image: Path to Stewie character image
    
    Returns:
        Path to output video
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Check if audio file exists
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"Audio file not found: {audio_file}")
    
    # Check if character images exist
    if not os.path.exists(peter_image):
        print(f"⚠️  Warning: Peter image not found: {peter_image}")
        peter_image = None
    
    if not os.path.exists(stewie_image):
        print(f"⚠️  Warning: Stewie image not found: {stewie_image}")
        stewie_image = None
    
    # Get audio duration
    duration_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_file
    ]
    result = subprocess.run(duration_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ ffprobe error: {result.stderr}")
        raise Exception(f"Failed to get audio duration: {result.stderr}")
    
    if not result.stdout.strip():
        print(f"❌ ffprobe returned empty output for: {audio_file}")
        print(f"   Command: {' '.join(duration_cmd)}")
        print(f"   stderr: {result.stderr}")
        raise ValueError(f"Could not determine audio duration for {audio_file}")
    
    audio_duration = float(result.stdout.strip())
    
    print(f"🎬 Creating video with duration: {audio_duration:.2f}s")
    
    # Group timings by speaker for character overlay enable expressions
    peter_timings = [t for t in caption_timings if t["speaker"] == "PETER"]
    stewie_timings = [t for t in caption_timings if t["speaker"] == "STEWIE"]
    
    # Create enable expressions for each character
    def create_enable_expr(timings):
        if not timings:
            return "0"  # Never show
        conditions = [f"between(t,{t['start']},{t['end']})" for t in timings]
        return "+".join(conditions)
    
    peter_enable = create_enable_expr(peter_timings)
    stewie_enable = create_enable_expr(stewie_timings)
    
    # Build ffmpeg filter for captions
    caption_filters = []
    for timing in caption_timings:
        # Wrap and escape caption text
        wrapped_text = wrap_caption_text(timing["caption"])
        caption_text = (
            wrapped_text
            .replace("\\", "\\\\")
            .replace("'", "'\\\\\\''")
            .replace(":", "\\:")
            .replace("\n", "\\n")
        )
        speaker = timing["speaker"]
        
        # Style for captions
        if speaker == "PETER":
            color = "white"
            bg_color = "0x00000080"  # Semi-transparent black
        else:
            color = "yellow"
            bg_color = "0x0000FF80"  # Semi-transparent blue
        
        # Create drawtext filter for this caption with manual wrapping
        caption_filter = (
            f"drawtext=text='{caption_text}':"
            f"fontfile=/System/Library/Fonts/Supplemental/Arial Bold.ttf:"
            f"fontsize=54:"
            f"fontcolor={color}:"
            f"box=1:boxcolor={bg_color}:boxborderw=10:"
            f"x=(w-tw)/2:"  # Center horizontally
            f"y=h-320:"  # Position near bottom
            f"enable='between(t,{timing['start']},{timing['end']})':"
            f"line_spacing=18"
        )
        caption_filters.append(caption_filter)
    
    # Combine all caption filters
    all_captions = ",".join(caption_filters) if caption_filters else ""
    
    # Build filter_complex chain
    # Start with background video scaling
    filter_parts = [
        f"[0:v]scale={video_size[0]}:{video_size[1]}:force_original_aspect_ratio=decrease,"
        f"pad={video_size[0]}:{video_size[1]}:(ow-iw)/2:(oh-ih)/2[bg]"
    ]
    
    current_stream = "[bg]"
    input_index = 2  # 0=background, 1=audio, 2+=character images
    
    # Add character overlays if images exist
    character_height = 320
    margin = 40
    
    if stewie_image:
        # Scale and overlay Stewie on bottom left
        filter_parts.append(
            f"[{input_index}:v]scale=-1:{character_height}[stewie]"
        )
        filter_parts.append(
            f"{current_stream}[stewie]overlay={margin}:H-h-{margin}:enable='{stewie_enable}'[tmp{input_index}]"
        )
        current_stream = f"[tmp{input_index}]"
        input_index += 1
    
    if peter_image:
        # Scale and overlay Peter on bottom right
        filter_parts.append(
            f"[{input_index}:v]scale=-1:{character_height}[peter]"
        )
        filter_parts.append(
            f"{current_stream}[peter]overlay=W-w-{margin}:H-h-{margin}:enable='{peter_enable}'[tmp{input_index}]"
        )
        current_stream = f"[tmp{input_index}]"
        input_index += 1
    
    # Add captions on top
    if all_captions:
        filter_parts.append(f"{current_stream}{all_captions}[v]")
    else:
        filter_parts.append(f"{current_stream}split[v]")
    
    filter_complex = ";".join(filter_parts)
    
    # Build ffmpeg command
    cmd = [
        "ffmpeg", "-y",
        # Input: Loop background video
        "-stream_loop", "-1",
        "-i", background_video,
        # Input: Audio
        "-i", audio_file,
    ]
    
    # Add character image inputs
    if stewie_image:
        cmd.extend(["-loop", "1", "-i", stewie_image])
    if peter_image:
        cmd.extend(["-loop", "1", "-i", peter_image])
    
    # Add filter complex and output settings
    cmd.extend([
        # Video filters: scale, overlays, and captions
        "-filter_complex", filter_complex,
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
    ])
    
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

