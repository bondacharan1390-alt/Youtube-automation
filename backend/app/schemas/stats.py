from typing import List, Dict, Any
from pydantic import BaseModel

class DashboardStatsResponse(BaseModel):
    total_projects: int
    draft_projects: int
    processing_projects: int
    ready_projects: int
    published_projects: int
    total_scenes_created: int
    youtube_quota_used: int
    youtube_quota_limit: int = 10000
    healthy_providers_count: int
    total_providers_count: int
    system_memory_total_gb: float
    system_memory_free_gb: float
    system_platform: str
