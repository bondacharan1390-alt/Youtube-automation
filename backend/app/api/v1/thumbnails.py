"""Thumbnail Studio API — Generate, preview, and download YouTube thumbnails."""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.v1.deps import get_db, get_current_user
from app.models.project import Project, Asset
from app.models.user import User
from app.schemas.thumbnail import ThumbnailGenerateRequest, ThumbnailResponse, ThumbnailThemeInfo
from app.services.thumbnail.thumbnail_service import ThumbnailService, STORAGE_DIR

router = APIRouter(prefix="/thumbnails", tags=["Thumbnails"])


@router.get("/themes", response_model=List[ThumbnailThemeInfo])
def get_thumbnail_themes():
    return [
        ThumbnailThemeInfo(
            id="viral_punch",
            name="Viral Punch",
            description="High contrast golden yellow with crimson badge for maximum click-through rate",
            accent_color="#FFD700",
        ),
        ThumbnailThemeInfo(
            id="cinematic_dark",
            name="Cinematic Glow",
            description="Deep obsidian backdrop with electric cyan highlights and purple accents",
            accent_color="#00E5FF",
        ),
        ThumbnailThemeInfo(
            id="tech_minimal",
            name="Tech Minimalist",
            description="Clean modern emerald aesthetic with sleek typography",
            accent_color="#10B981",
        ),
        ThumbnailThemeInfo(
            id="breaking_news",
            name="Breaking Alert",
            description="Urgent high-impact red & bright yellow for news and breaking discoveries",
            accent_color="#FFEB3B",
        ),
    ]


@router.post("/generate", response_model=ThumbnailResponse)
def generate_thumbnail(
    req: ThumbnailGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == req.project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    aspect_ratio = req.aspect_ratio or project.aspect_ratio or "16:9"

    # Resolve background image if specified or pick first scene image
    bg_image_path = None
    if req.bg_image_asset_id:
        asset = db.query(Asset).filter(Asset.id == req.bg_image_asset_id).first()
        if asset and os.path.exists(asset.file_path):
            bg_image_path = asset.file_path
    if not bg_image_path:
        images_dir = os.path.join(STORAGE_DIR, "images")
        for s in project.scenes:
            cand = os.path.join(images_dir, f"scene_{s.id}.png")
            if os.path.exists(cand):
                bg_image_path = cand
                break

    headline = req.headline or project.title
    result = ThumbnailService.generate_thumbnail(
        project_id=project.id,
        headline=headline,
        subtitle=req.subtitle,
        badge_text=req.badge_text,
        theme_name=req.theme_name,
        aspect_ratio=aspect_ratio,
        bg_image_path=bg_image_path,
        db=db,
    )

    return ThumbnailResponse(**result)


@router.get("/{project_id}", response_model=ThumbnailResponse)
def get_thumbnail(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    thumbnail_path = os.path.join(STORAGE_DIR, "thumbnails", f"{project_id}.png")
    if not os.path.exists(thumbnail_path):
        raise HTTPException(status_code=404, detail="Thumbnail not yet generated for this project")

    file_size = os.path.getsize(thumbnail_path)
    aspect_ratio = project.aspect_ratio or "16:9"
    width, height = (1280, 720) if aspect_ratio == "16:9" else (720, 1280)

    asset = db.query(Asset).filter(Asset.project_id == project_id, Asset.asset_type == "thumbnail").order_by(Asset.created_at.desc()).first()

    return ThumbnailResponse(
        project_id=project_id,
        asset_id=asset.id if asset else None,
        thumbnail_url=f"/storage/thumbnails/{project_id}.png",
        width=width,
        height=height,
        aspect_ratio=aspect_ratio,
        theme="viral_punch",
        file_size_bytes=file_size,
    )


@router.get("/download/{project_id}")
def download_thumbnail(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    thumbnail_path = os.path.join(STORAGE_DIR, "thumbnails", f"{project_id}.png")
    if not os.path.exists(thumbnail_path):
        raise HTTPException(status_code=404, detail="Thumbnail file not found")

    safe_title = "".join(c for c in project.title if c.isalnum() or c in (" ", "_", "-")).rstrip()
    filename = f"{safe_title or project_id}_thumbnail.png"

    return FileResponse(
        path=thumbnail_path,
        media_type="image/png",
        filename=filename,
    )
