from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router
from app.api.v1.providers import router as providers_router
from app.api.v1.stats import router as stats_router
from app.api.v1.research import router as research_router
from app.api.v1.scripts import router as scripts_router
from app.api.v1.voice import router as voice_router
from app.api.v1.images import router as images_router
from app.api.v1.editor import router as editor_router
from app.api.v1.subtitles import router as subtitles_router
from app.api.v1.thumbnails import router as thumbnails_router
from app.api.v1.youtube import router as youtube_router
from app.api.v1.automation import router as automation_router
from app.api.v1.higgsfield import router as higgsfield_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(providers_router)
api_router.include_router(stats_router)
api_router.include_router(research_router)
api_router.include_router(scripts_router)
api_router.include_router(voice_router)
api_router.include_router(images_router)
api_router.include_router(editor_router)
api_router.include_router(subtitles_router)
api_router.include_router(thumbnails_router)
api_router.include_router(youtube_router)
api_router.include_router(automation_router)
api_router.include_router(higgsfield_router)
