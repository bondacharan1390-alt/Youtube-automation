"""Video Editor API — timeline, render, scene management."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.v1.deps import get_db, get_current_user
from app.models.project import Project, Scene, Asset, RenderJob
from app.models.user import User
from app.schemas.editor import (
    TimelineScene, TimelineResponse, SceneUpdateRequest,
    RenderRequest, RenderStatusResponse
)
from app.services.video.render_job import RenderJobService
import os

router = APIRouter(prefix="/editor", tags=["editor"])

STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage"))

def _resolve_asset_url(asset_id: Optional[str], asset_type: str, scene_id: str, db: Session) -> Optional[str]:
    if asset_id:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if asset:
            return f"/storage/{asset_type}/{asset.file_name}"
    # Fallback: check by scene_id filename convention
    ext = "mp3" if asset_type == "audio" else "png"
    fname = f"scene_{scene_id}.{ext}"
    fpath = os.path.join(STORAGE_DIR, asset_type, fname)
    if os.path.exists(fpath):
        return f"/storage/{asset_type}/{fname}"
    return None

@router.get("/timeline/{project_id}", response_model=TimelineResponse)
async def get_timeline(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    timeline_scenes = []
    for scene in sorted(project.scenes, key=lambda s: s.scene_order):
        image_url = _resolve_asset_url(scene.visual_asset_id, "images", scene.id, db)
        audio_url = _resolve_asset_url(scene.voice_asset_id, "audio", scene.id, db)
        timeline_scenes.append(TimelineScene(
            scene_id=scene.id,
            scene_order=scene.scene_order,
            script_text=scene.script_text,
            narration_text=scene.narration_text,
            visual_prompt=scene.visual_prompt,
            duration_seconds=scene.duration_seconds or 5.0,
            image_url=image_url,
            audio_url=audio_url,
            transition="fade",
        ))

    return TimelineResponse(
        project_id=project.id,
        title=project.title,
        language=project.language,
        aspect_ratio=project.aspect_ratio,
        target_resolution=project.target_resolution,
        scenes=timeline_scenes,
    )

@router.patch("/scenes/{scene_id}", response_model=dict)
async def update_scene(
    scene_id: str,
    req: SceneUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scene = (
        db.query(Scene)
        .join(Project, Scene.project_id == Project.id)
        .filter(Scene.id == scene_id, Project.user_id == current_user.id)
        .first()
    )
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    if req.scene_order is not None:
        scene.scene_order = req.scene_order
    if req.duration_seconds is not None:
        scene.duration_seconds = req.duration_seconds
    if req.script_text is not None:
        scene.script_text = req.script_text
    if req.narration_text is not None:
        scene.narration_text = req.narration_text
    db.commit()
    return {"scene_id": scene_id, "updated": True}

@router.post("/render", response_model=RenderStatusResponse)
async def start_render(
    req: RenderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == req.project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    job = await RenderJobService.start_render(
        project_id=req.project_id,
        resolution=req.resolution,
        include_subtitles=req.include_subtitles,
        bgm_volume=req.bgm_volume,
        db=db,
        bitrate_kbps=req.bitrate_kbps,
        fps=req.fps,
    )
    return RenderStatusResponse(
        job_id=job.id,
        project_id=job.project_id,
        status=job.status,
        progress_percentage=job.progress_percentage,
        error_log=job.error_log,
        started_at=job.started_at.isoformat() if job.started_at else None,
    )

@router.get("/render-status/{job_id}", response_model=RenderStatusResponse)
async def get_render_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = RenderJobService.get_job_status(job_id, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return RenderStatusResponse(**result)

@router.get("/download/{project_id}")
async def download_rendered_video(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    video_file = os.path.join(STORAGE_DIR, "renders", f"{project_id}.mp4")
    if not os.path.exists(video_file):
        raise HTTPException(status_code=404, detail="Rendered video not found. Please render the project first.")

    safe_title = "".join(c for c in project.title if c.isalnum() or c in (" ", "_", "-")).rstrip()
    filename = f"{safe_title or project_id}.mp4"

    return FileResponse(
        path=video_file,
        media_type="video/mp4",
        filename=filename,
    )
