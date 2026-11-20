from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.research import (
    TopicAnalysisRequest,
    TopicAnalysisResponse,
    VideoIdeasRequest,
    VideoIdeasResponse,
)
from app.services.research_service import ResearchService
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/research", tags=["AI Research Studio"])

@router.post("/analyze", response_model=TopicAnalysisResponse)
def analyze_topic(
    req: TopicAnalysisRequest,
    db: Session = Depends(get_db),
    _ = Depends(get_current_user)
):
    try:
        return ResearchService.analyze_topic(topic=req.topic, language=req.language, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Topic analysis failed: {str(e)}"
        )

@router.post("/ideas", response_model=VideoIdeasResponse)
def generate_ideas(
    req: VideoIdeasRequest,
    db: Session = Depends(get_db),
    _ = Depends(get_current_user)
):
    try:
        return ResearchService.generate_ideas(seed_keyword=req.seed_keyword, language=req.language, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video idea generation failed: {str(e)}"
        )
