from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ThumbnailGenerateRequest(BaseModel):
    project_id: str
    headline: str
    subtitle: Optional[str] = None
    badge_text: Optional[str] = "NEW"
    theme_name: str = "viral_punch"
    aspect_ratio: Optional[str] = None
    bg_image_asset_id: Optional[str] = None


class ThumbnailResponse(BaseModel):
    project_id: str
    asset_id: Optional[str] = None
    thumbnail_url: str
    width: int
    height: int
    aspect_ratio: str
    theme: str
    file_size_bytes: int


class ThumbnailThemeInfo(BaseModel):
    id: str
    name: str
    description: str
    accent_color: str
