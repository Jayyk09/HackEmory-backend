"""
Gemini Service
Handles script generation using Gemini API
"""

class GeminiService:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def generate_script(self, transcript: str) -> list:
        """
        Generate structured script from transcript
        Returns: [{t1, c1, s}, {t2, c2, s}, ...]
        """
        pass

