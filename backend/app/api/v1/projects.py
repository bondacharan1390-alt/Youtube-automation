from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.project import Asset, Project, Scene
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse,
    SceneCreate, SceneUpdate, SceneResponse
)
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/projects", tags=["Projects"])


def _scene_response(scene: Scene, db: Session) -> SceneResponse:
    response = SceneResponse.model_validate(scene)
    if scene.voice_asset_id:
        asset = db.query(Asset).filter(Asset.id == scene.voice_asset_id, Asset.asset_type == "audio").first()
        if asset:
            response.audio_url = f"/storage/audio/{asset.file_name}"
    return response

@router.get("", response_model=List[ProjectResponse])
def list_projects(
    language: Optional[str] = Query(None, description="Filter by language: en or te"),
    aspect_ratio: Optional[str] = Query(None, description="Filter by aspect ratio: 16:9 or 9:16"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by title or topic"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Project).filter(Project.user_id == current_user.id)
    
    if language:
        query = query.filter(Project.language == language)
    if aspect_ratio:
        query = query.filter(Project.aspect_ratio == aspect_ratio)
    if status:
        query = query.filter(Project.status == status)
    if search:
        search_filter = f"%{search}%"
        query = query.filter((Project.title.ilike(search_filter)) | (Project.topic.ilike(search_filter)))
        
    projects = query.order_by(Project.created_at.desc()).all()
    
    # Calculate scenes_count dynamically
    result = []
    for p in projects:
        resp = ProjectResponse.model_validate(p)
        resp.scenes_count = len(p.scenes)
        result.append(resp)
    return result

@router.post("", response_model=ProjectDetailResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = Project(
        user_id=current_user.id,
        channel_id=project_in.channel_id,
        title=project_in.title,
        topic=project_in.topic,
        language=project_in.language,
        aspect_ratio=project_in.aspect_ratio,
        target_resolution=project_in.target_resolution,
        target_scene_count=project_in.target_scene_count,
        status="draft",
        estimated_duration_seconds=float(project_in.target_scene_count * 6.0),
        metadata_json=project_in.metadata_json or {}
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Initialize empty starter scenes based on target_scene_count
    for i in range(1, project_in.target_scene_count + 1):
        scene = Scene(
            project_id=project.id,
            scene_order=i,
            script_text=f"Scene {i} outline for: {project.title}",
            narration_text="",
            visual_prompt=f"Cinematic frame depicting {project.topic or project.title}, shot {i}",
            duration_seconds=6.0,
            subtitle_cues=[]
        )
        db.add(scene)
    
    db.commit()
    db.refresh(project)
    
    resp = ProjectDetailResponse.model_validate(project)
    resp.scenes = [_scene_response(scene, db) for scene in project.scenes]
    resp.scenes_count = len(project.scenes)
    return resp

@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    resp = ProjectDetailResponse.model_validate(project)
    resp.scenes = [_scene_response(scene, db) for scene in project.scenes]
    resp.scenes_count = len(project.scenes)
    return resp

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
        
    db.commit()
    db.refresh(project)
    
    resp = ProjectResponse.model_validate(project)
    resp.scenes_count = len(project.scenes)
    return resp

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return None

@router.post("/{project_id}/scenes", response_model=SceneResponse, status_code=status.HTTP_201_CREATED)
def add_scene(
    project_id: str,
    scene_in: SceneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    highest_order = len(project.scenes) + 1
    scene = Scene(
        project_id=project.id,
        scene_order=scene_in.scene_order or highest_order,
        script_text=scene_in.script_text,
        narration_text=scene_in.narration_text,
        visual_prompt=scene_in.visual_prompt,
        duration_seconds=scene_in.duration_seconds,
        subtitle_cues=scene_in.subtitle_cues
    )
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return _scene_response(scene, db)
