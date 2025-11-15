from fastapi import APIRouter

router = APIRouter()

@router.post("/generate")
async def generate_audio_from_script():
    """
    Generate audio files using ElevenLabs TTS
    Input: script array [{t1, c1, s}, ...]
    Output: shot list with timing information
    
    Process:
    1. Loop through each line in script
    2. Call ElevenLabs with text (t1) and voice (s)
    3. Save audio file (line_X.mp3)
    4. Use ffprobe to get exact duration
    5. Build shot list with start/end times
    """
    pass

