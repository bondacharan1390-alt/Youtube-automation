from typing import List, Optional
from pydantic import BaseModel, Field

class TopicAnalysisRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=500, description="Seed topic or question")
    language: str = Field(default="en", pattern="^(en|te)$", description="Target language: en or te")

class TopicAnalysisResponse(BaseModel):
    topic: str
    language: str
    virality_score: int
    audience_persona: str
    search_intent: str
    hook_angles: List[str]
    primary_keywords: List[str]
    long_tail_keywords: List[str]
    recommended_video_length: str

class VideoIdeasRequest(BaseModel):
    seed_keyword: str = Field(..., min_length=2, max_length=255)
    language: str = Field(default="en", pattern="^(en|te)$")

class VideoIdeaItem(BaseModel):
    title: str
    angle: str
    hook: str
    estimated_ctr: str
    format: str

class VideoIdeasResponse(BaseModel):
    seed_keyword: str
    language: str
    ideas: List[VideoIdeaItem]
