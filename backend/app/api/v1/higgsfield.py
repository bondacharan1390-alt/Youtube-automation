from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decrypt_secret
from app.models.project import HiggsfieldGeneration, Project, Scene
from app.models.provider import AIProvider
from app.schemas.higgsfield import (
    HiggsfieldGenerationRequest,
    HiggsfieldGenerationResponse,
    HiggsfieldModelResponse,
)
from app.services.higgsfield.client import HiggsfieldAPIError, HiggsfieldClient

router = APIRouter(prefix="/higgsfield", tags=["Higgsfield AI"])

SUPPORTED_MODELS = {
    "kling-video/v4.0/image-to-video": "image_to_video",
    "minimax/hailuo-2.3/standard/image-to-video": "image_to_video",
}


def _validate_generation(model_path: str, operation: str, payload: Dict[str, Any]) -> None:
    expected_operation = SUPPORTED_MODELS.get(model_path)
    if not expected_operation or expected_operation != operation:
        raise HTTPException(status_code=422, detail="Model path is not in the verified Higgsfield allowlist")

    image_url = payload.get("image_url")
    if not isinstance(image_url, str) or not image_url.startswith(("https://", "http://")):
        raise HTTPException(status_code=422, detail="A publicly reachable image_url is required")

    duration = payload.get("duration")
    if not isinstance(duration, int):
        raise HTTPException(status_code=422, detail="duration must be an integer")
    if model_path.startswith("kling-video/") and not 3 <= duration <= 30:
        raise HTTPException(status_code=422, detail="Kling duration must be between 3 and 30 seconds")
    if model_path.startswith("minimax/") and duration not in (6, 10):
        raise HTTPException(status_code=422, detail="Hailuo duration must be 6 or 10 seconds")

    resolution = payload.get("resolution")
    if resolution is not None and resolution not in ("720p", "1080p"):
        raise HTTPException(status_code=422, detail="resolution must be 720p or 1080p")


def _provider(db: Session) -> AIProvider:
    provider = db.query(AIProvider).filter(AIProvider.provider_key == "higgsfield").first()
    if not provider or not provider.is_active:
        raise HTTPException(status_code=503, detail="Higgsfield provider is not active")
    credential = decrypt_secret(provider.encrypted_api_key or "")
    if not credential:
        raise HTTPException(status_code=503, detail="Higgsfield API credential is not configured")
    return provider


def _response(job: HiggsfieldGeneration) -> HiggsfieldGenerationResponse:
    return HiggsfieldGenerationResponse(
        id=job.id,
        request_id=job.request_id,
        model_path=job.model_path,
        operation=job.operation,
        status=job.status,
        status_url=job.status_url,
        cancel_url=job.cancel_url,
        output_url=job.output_url,
        error_message=job.error_message,
    )


@router.get("/models", response_model=list[HiggsfieldModelResponse])
def list_models(db: Session = Depends(get_db), _=Depends(get_current_user)):
    provider = db.query(AIProvider).filter(AIProvider.provider_key == "higgsfield").first()
    configured = (provider.settings_json or {}) if provider else {}
    model_path = configured.get("model_path", "kling-video/v4.0/image-to-video")
    operation = configured.get("operation", "image_to_video")
    if model_path not in SUPPORTED_MODELS:
        model_path = "kling-video/v4.0/image-to-video"
        operation = SUPPORTED_MODELS[model_path]
    return [HiggsfieldModelResponse(
        provider_key="higgsfield",
        model_path=model_path,
        operation=operation,
        credit_warning="Every generation may consume prepaid Higgsfield API balance; verify model pricing before submitting.",
    )]


@router.post("/generations", response_model=HiggsfieldGenerationResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_generation(
    req: HiggsfieldGenerationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    provider = _provider(db)
    provider_settings = provider.settings_json or {}
    model_path = req.model_path or provider_settings.get("model_path")
    if not model_path:
        raise HTTPException(status_code=422, detail="A documented Higgsfield model path is required")
    _validate_generation(model_path, req.operation, req.payload)

    if req.project_id:
        project = db.query(Project).filter(Project.id == req.project_id, Project.user_id == current_user.id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    if req.scene_id:
        scene = db.query(Scene).join(Project, Scene.project_id == Project.id).filter(
            Scene.id == req.scene_id,
            Project.user_id == current_user.id,
        ).first()
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")

    credential = decrypt_secret(provider.encrypted_api_key or "")
    client = HiggsfieldClient(credential, settings.HIGGSFIELD_API_BASE_URL)
    try:
        result = await client.submit(model_path, req.payload)
    except HiggsfieldAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    request_id = result.get("request_id")
    if not request_id:
        raise HTTPException(status_code=502, detail="Higgsfield response did not include request_id")

    job = HiggsfieldGeneration(
        user_id=current_user.id,
        project_id=req.project_id,
        scene_id=req.scene_id,
        request_id=str(request_id),
        model_path=model_path,
        operation=req.operation,
        status=str(result.get("status") or "queued"),
        status_url=result.get("status_url"),
        cancel_url=result.get("cancel_url"),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return _response(job)


@router.get("/generations/{job_id}", response_model=HiggsfieldGenerationResponse)
async def poll_generation(job_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    job = db.query(HiggsfieldGeneration).filter(
        HiggsfieldGeneration.id == job_id,
        HiggsfieldGeneration.user_id == current_user.id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Higgsfield generation not found")
    provider = _provider(db)
    client = HiggsfieldClient(decrypt_secret(provider.encrypted_api_key or ""), settings.HIGGSFIELD_API_BASE_URL)
    try:
        result = await client.status(job.status_url or "", job.request_id)
    except HiggsfieldAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    job.status = str(result.get("status") or job.status)
    job.error_message = str(result.get("error")) if result.get("error") else None
    video = result.get("video") if isinstance(result.get("video"), dict) else {}
    images = result.get("images") if isinstance(result.get("images"), list) else []
    job.output_url = video.get("url") or (images[0].get("url") if images and isinstance(images[0], dict) else None)
    if job.status in {"completed", "failed", "nsfw", "canceled"}:
        job.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return _response(job)


@router.post("/generations/{job_id}/cancel", response_model=HiggsfieldGenerationResponse)
async def cancel_generation(job_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    job = db.query(HiggsfieldGeneration).filter(
        HiggsfieldGeneration.id == job_id,
        HiggsfieldGeneration.user_id == current_user.id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Higgsfield generation not found")
    provider = _provider(db)
    client = HiggsfieldClient(decrypt_secret(provider.encrypted_api_key or ""), settings.HIGGSFIELD_API_BASE_URL)
    try:
        result = await client.cancel(job.cancel_url or "", job.request_id)
    except HiggsfieldAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    job.status = str(result.get("status") or "canceled")
    job.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return _response(job)
