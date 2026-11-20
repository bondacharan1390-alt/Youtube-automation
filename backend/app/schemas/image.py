from typing import Optional, List
from pydantic import BaseModel, Field

class ImageGenerateRequest(BaseModel):
    scene_id: str
    prompt: str = Field(..., min_length=2)
    aspect_ratio: str = Field(default="16:9", pattern="^(16:9|9:16)$")
    character_tokens: Optional[str] = None
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None

class ImageGenerateResponse(BaseModel):
    scene_id: str
    asset_id: Optional[str] = None
    file_path: str
    image_url: str
    file_size_bytes: int
    aspect_ratio: str
    seed: int
    prompt: str

class ImageProjectGenerateRequest(BaseModel):
    character_tokens: Optional[str] = None
    negative_prompt: Optional[str] = None

class ImageRegenerateRequest(BaseModel):
    custom_prompt: Optional[str] = None
