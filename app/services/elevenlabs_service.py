"""
ElevenLabs Service
Handles text-to-speech and timing generation
"""

class ElevenLabsService:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def generate_audio(self, text: str, voice_id: str, output_path: str) -> dict:
        """
        Generate audio from text and return timing info
        Returns: {duration, file_path, start_time, end_time}
        """
        pass
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration using ffprobe"""
        pass

