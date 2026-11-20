import platform
import ctypes
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.project import Project, Scene
from app.models.provider import AIProvider
from app.models.user import Channel
from app.services.hardware_queue import get_system_ram_gb
from app.schemas.stats import DashboardStatsResponse
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/stats", tags=["Dashboard Statistics"])

@router.get("", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    total_projects = len(projects)
    draft_projects = sum(1 for p in projects if p.status == "draft")
    processing_projects = sum(1 for p in projects if p.status in ["scripted", "voiced", "rendering"])
    ready_projects = sum(1 for p in projects if p.status == "ready")
    published_projects = sum(1 for p in projects if p.status == "published")
    
    total_scenes = db.query(Scene).join(Project).filter(Project.user_id == current_user.id).count()
    
    channel = db.query(Channel).filter(Channel.user_id == current_user.id).first()
    quota_used = channel.quota_units_used_today if channel else 0
    
    providers = db.query(AIProvider).all()
    total_providers = len(providers)
    healthy_providers = sum(1 for p in providers if p.is_healthy)
    
    total_ram, free_ram = get_system_ram_gb()

    return DashboardStatsResponse(
        total_projects=total_projects,
        draft_projects=draft_projects,
        processing_projects=processing_projects,
        ready_projects=ready_projects,
        published_projects=published_projects,
        total_scenes_created=total_scenes,
        youtube_quota_used=quota_used,
        youtube_quota_limit=10000,
        healthy_providers_count=healthy_providers,
        total_providers_count=total_providers,
        system_memory_total_gb=total_ram,
        system_memory_free_gb=free_ram,
        system_platform=f"{platform.system()} {platform.release()}"
    )
