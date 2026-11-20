"""Subtitle generation and download API."""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.api.v1.deps import get_db, get_current_user
from app.models.project import Project
from app.models.user import User
from app.services.video.subtitle_generator import generate_srt, generate_vtt

router = APIRouter(prefix="/subtitles", tags=["subtitles"])

STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage"))

@router.post("/generate/{project_id}")
async def generate_subtitles(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    subtitles_dir = os.path.join(STORAGE_DIR, "subtitles")
    os.makedirs(subtitles_dir, exist_ok=True)

    scenes_data = [
        {
            "scene_order": s.scene_order,
            "narration_text": s.narration_text,
            "script_text": s.script_text,
            "duration_seconds": s.duration_seconds or 5.0,
        }
        for s in sorted(project.scenes, key=lambda s: s.scene_order)
    ]

    srt = generate_srt(scenes_data)
    vtt = generate_vtt(scenes_data)

    srt_path = os.path.join(subtitles_dir, f"{project_id}.srt")
    vtt_path = os.path.join(subtitles_dir, f"{project_id}.vtt")

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt)
    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write(vtt)

    return {
        "project_id": project_id,
        "srt_url": f"/storage/subtitles/{project_id}.srt",
        "vtt_url": f"/storage/subtitles/{project_id}.vtt",
        "cue_count": srt.count("-->"),
        "message": "Subtitles generated successfully",
    }

@router.get("/download/{project_id}")
async def download_subtitles(
    project_id: str,
    format: str = "srt",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ext = "vtt" if format.lower() == "vtt" else "srt"
    subtitles_dir = os.path.join(STORAGE_DIR, "subtitles")
    file_path = os.path.join(subtitles_dir, f"{project_id}.{ext}")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Subtitle file not found. Generate first via POST /subtitles/generate/{project_id}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    media_type = "text/vtt" if ext == "vtt" else "application/x-subrip"
    return Response(
        content=content.encode("utf-8"),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={project_id}.{ext}"}
    )
