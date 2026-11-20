from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.image import (
    ImageGenerateRequest,
    ImageGenerateResponse,
    ImageProjectGenerateRequest,
    ImageRegenerateRequest,
)
from app.services.image.image_service import ImageService
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/images", tags=["AI Image Studio"])

@router.post("/generate", response_model=ImageGenerateResponse)
async def generate_image(
    req: ImageGenerateRequest,
    db: Session = Depends(get_db),
    _ = Depends(get_current_user),
):
    try:
        res = await ImageService.generate_scene_image(
            scene_id=req.scene_id,
            prompt=req.prompt,
            aspect_ratio=req.aspect_ratio,
            character_tokens=req.character_tokens,
            negative_prompt=req.negative_prompt,
            seed=req.seed,
            db=db,
        )
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image generation failed: {str(e)}",
        )

@router.post("/generate-all/{project_id}", response_model=List[ImageGenerateResponse])
async def generate_all_images(
    project_id: str,
    req: ImageProjectGenerateRequest,
    db: Session = Depends(get_db),
    _ = Depends(get_current_user),
):
    try:
        res = await ImageService.generate_project_images(
            project_id=project_id,
            character_tokens=req.character_tokens,
            negative_prompt=req.negative_prompt,
            db=db,
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch image generation failed: {str(e)}",
        )

@router.post("/regenerate/{scene_id}", response_model=ImageGenerateResponse)
async def regenerate_image(
    scene_id: str,
    req: ImageRegenerateRequest,
    db: Session = Depends(get_db),
    _ = Depends(get_current_user),
):
    try:
        res = await ImageService.regenerate_scene_image(
            scene_id=scene_id,
            custom_prompt=req.custom_prompt,
            db=db,
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image regeneration failed: {str(e)}",
        )
