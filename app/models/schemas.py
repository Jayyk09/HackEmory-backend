from pydantic import BaseModel
from typing import List, Optional

class ScriptLine(BaseModel):
    """Single line in the script"""
    t: str  # Full line for speaker to say
    c: str  # Short caption for screen
    s: str  # Speaker ID

class Script(BaseModel):
    """Complete script"""
    lines: List[ScriptLine]

class ShotListItem(BaseModel):
    """Single shot with timing information"""
    line: ScriptLine
    audio_file: str
    duration: float
    start_time: float
    end_time: float

class ShotList(BaseModel):
    """Complete shot list with timing"""
    shots: List[ShotListItem]
    total_duration: float

class VideoRequest(BaseModel):
    """Request to generate final video"""
    shot_list: ShotList
    background_video: str
    output_path: str

