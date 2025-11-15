from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    GEMINI_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    
    # File paths
    UPLOAD_DIR: str = "uploads"
    AUDIO_DIR: str = "audio"
    VIDEO_DIR: str = "videos"
    
    # App settings
    APP_NAME: str = "Video Generation API"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()

