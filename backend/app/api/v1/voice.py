from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.voice import (
    VoiceItemResponse,
    VoiceSynthesizeRequest,
    VoiceSynthesizeResponse,
    VoiceProjectSynthesizeRequest,
)
from app.services.voice.voice_service import VoiceService
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/voice", tags=["AI Voice Studio"])

@router.get("/voices", response_model=List[VoiceItemResponse])
def get_voices(
    language: Optional[str] = Query(None, description="Filter by language: en or te"),
    gender: Optional[str] = Query(None, description="Filter by gender: male or female"),
):
    return VoiceService.get_all_voices(language=language, gender=gender)

@router.post("/synthesize", response_model=VoiceSynthesizeResponse)
async def synthesize_voice(
    req: VoiceSynthesizeRequest,
    db: Session = Depends(get_db),
    _ = Depends(get_current_user),
):
    try:
        res = await VoiceService.synthesize_scene(
            scene_id=req.scene_id,
            text=req.text,
            voice_id=req.voice_id,
            speed=req.speed,
            pitch=req.pitch,
            output_format=req.output_format,
            db=db,
        )
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice synthesis failed: {str(e)}",
        )

@router.post("/synthesize-all/{project_id}", response_model=List[VoiceSynthesizeResponse])
async def synthesize_all_scenes(
    project_id: str,
    req: VoiceProjectSynthesizeRequest,
    db: Session = Depends(get_db),
    _ = Depends(get_current_user),
):
    try:
        res = await VoiceService.synthesize_project_scenes(
            project_id=project_id,
            voice_id=req.voice_id,
            speed=req.speed,
            pitch=req.pitch,
            output_format=req.output_format,
            db=db,
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch voice synthesis failed: {str(e)}",
        )
