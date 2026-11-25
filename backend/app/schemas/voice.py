from typing import Optional, List
from pydantic import BaseModel, Field

class VoiceItemResponse(BaseModel):
    id: str
    name: str
    gender: str
    language: str
    engine: str

class VoiceSynthesizeRequest(BaseModel):
    scene_id: str
    text: str = Field(..., min_length=1)
    voice_id: str = "te-IN-MohanNeural"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-50.0, le=50.0)
    output_format: str = Field(default="mp3", pattern="^(mp3|wav)$")

class VoiceSynthesizeResponse(BaseModel):
    scene_id: str
    asset_id: Optional[str] = None
    file_path: str
    audio_url: str
    file_size_bytes: int
    voice_id: str
    speed: float
    pitch: float
    mime_type: Optional[str] = None
    audio_format: Optional[str] = None

class VoiceProjectSynthesizeRequest(BaseModel):
    voice_id: str = "te-IN-MohanNeural"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-50.0, le=50.0)
    output_format: str = Field(default="mp3", pattern="^(mp3|wav)$")
