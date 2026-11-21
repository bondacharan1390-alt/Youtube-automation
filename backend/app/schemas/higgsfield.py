from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class HiggsfieldGenerationRequest(BaseModel):
    model_path: Optional[str] = None
    operation: str = Field(default="image_to_video", min_length=2, max_length=50)
    payload: Dict[str, Any] = Field(default_factory=dict)
    project_id: Optional[str] = None
    scene_id: Optional[str] = None


class HiggsfieldGenerationResponse(BaseModel):
    id: str
    request_id: str
    model_path: str
    operation: str
    status: str
    status_url: Optional[str] = None
    cancel_url: Optional[str] = None
    output_url: Optional[str] = None
    error_message: Optional[str] = None


class HiggsfieldModelResponse(BaseModel):
    provider_key: str
    model_path: str
    operation: str
    officially_documented: bool = True
    credit_warning: str
