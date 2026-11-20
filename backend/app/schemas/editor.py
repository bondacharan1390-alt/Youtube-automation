from pydantic import BaseModel
from typing import List, Optional, Any

class TimelineScene(BaseModel):
    scene_id: str
    scene_order: int
    script_text: Optional[str] = None
    narration_text: Optional[str] = None
    visual_prompt: Optional[str] = None
    duration_seconds: float = 5.0
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    transition: str = "fade"

class TimelineResponse(BaseModel):
    project_id: str
    title: str
    language: str
    aspect_ratio: str
    target_resolution: str
    scenes: List[TimelineScene]

class SceneUpdateRequest(BaseModel):
    scene_order: Optional[int] = None
    duration_seconds: Optional[float] = None
    transition: Optional[str] = None
    script_text: Optional[str] = None
    narration_text: Optional[str] = None

class RenderRequest(BaseModel):
    project_id: str
    resolution: str = "1080p"
    include_subtitles: bool = True
    bgm_volume: float = 0.15
    include_bgm: bool = False
    bitrate_kbps: int = 5000
    fps: int = 25

class RenderStatusResponse(BaseModel):
    job_id: str
    project_id: str
    status: str
    progress_percentage: int
    output_url: Optional[str] = None
    error_log: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
