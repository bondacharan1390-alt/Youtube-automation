from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class SceneBase(BaseModel):
    scene_order: int = 1
    script_text: Optional[str] = ""
    narration_text: Optional[str] = ""
    visual_prompt: Optional[str] = ""
    duration_seconds: float = 5.0
    subtitle_cues: List[Dict[str, Any]] = Field(default_factory=list)

class SceneCreate(SceneBase):
    pass

class SceneUpdate(BaseModel):
    scene_order: Optional[int] = None
    script_text: Optional[str] = None
    narration_text: Optional[str] = None
    visual_prompt: Optional[str] = None
    duration_seconds: Optional[float] = None
    subtitle_cues: Optional[List[Dict[str, Any]]] = None

class SceneResponse(SceneBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ProjectBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    topic: Optional[str] = ""
    language: str = Field(default="en", pattern="^(en|te)$")
    aspect_ratio: str = Field(default="16:9", pattern="^(16:9|9:16)$")
    target_resolution: str = Field(default="1080p", pattern="^(720p|1080p)$")
    target_scene_count: int = Field(default=5, ge=1, le=50)

class ProjectCreate(ProjectBase):
    channel_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    topic: Optional[str] = None
    language: Optional[str] = None
    aspect_ratio: Optional[str] = None
    target_resolution: Optional[str] = None
    status: Optional[str] = None
    target_scene_count: Optional[int] = None
    estimated_duration_seconds: Optional[float] = None
    metadata_json: Optional[Dict[str, Any]] = None

class ProjectResponse(ProjectBase):
    id: str
    user_id: str
    channel_id: Optional[str] = None
    status: str
    estimated_duration_seconds: float
    metadata_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    scenes_count: Optional[int] = 0
    model_config = ConfigDict(from_attributes=True)

class ProjectDetailResponse(ProjectResponse):
    scenes: List[SceneResponse] = []
