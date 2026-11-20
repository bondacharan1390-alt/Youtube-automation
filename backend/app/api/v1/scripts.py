from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.script import (
    ScriptGenerateRequest,
    ScriptGenerateResponse,
    ScriptSceneItem,
    StoryGenerateRequest,
    StoryGenerateResponse,
    StoryboardExportResponse,
)
from app.services.script_service import ScriptService
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/scripts", tags=["AI Script Studio"])

@router.post("/generate", response_model=ScriptGenerateResponse)
def generate_script(
    req: ScriptGenerateRequest,
    db: Session = Depends(get_db),
    _ = Depends(get_current_user)
):
    try:
        return ScriptService.generate_script(req=req, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Script generation failed: {str(e)}"
        )

@router.post("/story", response_model=StoryGenerateResponse)
def generate_story(
    req: StoryGenerateRequest,
    db: Session = Depends(get_db),
    _ = Depends(get_current_user)
):
    try:
        return ScriptService.generate_story(req=req, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Story generation failed: {str(e)}"
        )

@router.post("/{project_id}/save", response_model=StoryboardExportResponse)
def save_scenes(
    project_id: str,
    scenes: List[ScriptSceneItem],
    db: Session = Depends(get_db),
    _ = Depends(get_current_user)
):
    try:
        ScriptService.save_scenes_to_project(project_id=project_id, scenes=scenes, db=db)
        return ScriptService.export_storyboard(project_id=project_id, db=db)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save scenes: {str(e)}"
        )

@router.get("/{project_id}/export", response_model=StoryboardExportResponse)
def export_storyboard(
    project_id: str,
    db: Session = Depends(get_db),
    _ = Depends(get_current_user)
):
    try:
        return ScriptService.export_storyboard(project_id=project_id, db=db)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export storyboard: {str(e)}"
        )
