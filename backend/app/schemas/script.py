from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ScriptSceneItem(BaseModel):
    scene_order: int
    script_text: str
    narration_text: str
    visual_prompt: str
    duration_seconds: float = 6.0
    character_name: Optional[str] = None

class ScriptGenerateRequest(BaseModel):
    project_id: Optional[str] = None
    title: str = Field(..., min_length=2, max_length=255)
    topic: Optional[str] = ""
    language: str = Field(default="en", pattern="^(en|te)$")
    aspect_ratio: str = Field(default="16:9", pattern="^(16:9|9:16)$")
    target_scene_count: int = Field(default=5, ge=2, le=20)
    tone: Optional[str] = "engaging"

class ScriptGenerateResponse(BaseModel):
    title: str
    language: str
    aspect_ratio: str
    estimated_total_duration: float
    scenes: List[ScriptSceneItem]

class CharacterProfile(BaseModel):
    name: str
    role: str
    voice_style: str
    visual_prompt: str

class DialogueScene(BaseModel):
    speaker: str
    line: str
    visual_prompt: str
    duration_seconds: float = 5.5

class StoryGenerateRequest(BaseModel):
    premise: str = Field(..., min_length=5, max_length=1000)
    language: str = Field(default="en", pattern="^(en|te)$")
    character_count: int = Field(default=2, ge=1, le=4)
    tone: Optional[str] = "dramatic"

class StoryGenerateResponse(BaseModel):
    story_title: str
    language: str
    characters: List[CharacterProfile]
    dialogue_scenes: List[DialogueScene]

class StoryboardExportResponse(BaseModel):
    project_id: str
    title: str
    language: str
    aspect_ratio: str
    target_resolution: str
    total_scenes: int
    total_duration_seconds: float
    scenes: List[ScriptSceneItem]
    metadata: Dict[str, Any]
