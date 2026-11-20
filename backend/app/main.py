import os
import time
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.api.v1 import api_router
from app.models.user import User, Channel
from app.models.project import Project, Scene
from app.models.provider import AIProvider
from app.models.automation import (
    Workflow, WorkflowExecution, WorkflowTask, JobQueue, JobAttempt,
    ApprovalRecord, ScheduledPublishing, Notification, IdempotencyRecord, RecoveryLog
)
from app.models.analytics import ChannelAnalyticsDaily, VideoAnalyticsDaily, AnalyticsInsight
from app.core.security import get_password_hash

def seed_initial_data(db: Session):
    # 1. Seed Default Providers if not present
    default_providers = [
        {
            "provider_key": "ollama",
            "name": "Ollama (Local LLM)",
            "category": "llm",
            "execution_mode": "local",
            "base_url": "http://localhost:11434",
            "settings_json": {"model": "llama3.2:3b-instruct-q4_K_M", "temperature": 0.7},
            "is_active": True,
            "is_healthy": False,
            "health_status_message": "Local daemon"
        },
        {
            "provider_key": "kokoro",
            "name": "Kokoro TTS (82M Local)",
            "category": "tts",
            "execution_mode": "local",
            "base_url": "local://onnx",
            "settings_json": {"voice": "af_heart", "speed": 1.0},
            "is_active": True,
            "is_healthy": True,
            "health_status_message": "Local ONNX engine ready"
        },
        {
            "provider_key": "edge_tts",
            "name": "Edge-TTS (Telugu & English Neural)",
            "category": "tts",
            "execution_mode": "local",
            "base_url": "local://python-stream",
            "settings_json": {"telugu_voice": "te-IN-MohanNeural", "english_voice": "en-US-ChristopherNeural"},
            "is_active": True,
            "is_healthy": True,
            "health_status_message": "Zero-RAM Neural TTS ready"
        },
        {
            "provider_key": "faster_whisper",
            "name": "faster-whisper (CTranslate2 INT8)",
            "category": "stt",
            "execution_mode": "local",
            "base_url": "local://ctranslate2",
            "settings_json": {"model_size": "base", "compute_type": "int8"},
            "is_active": True,
            "is_healthy": True,
            "health_status_message": "INT8 word-level alignment ready"
        },
        {
            "provider_key": "comfyui",
            "name": "ComfyUI (Local Image Gen)",
            "category": "image",
            "execution_mode": "local",
            "base_url": "http://localhost:8188",
            "settings_json": {"checkpoint": "v1-5-pruned-emaonly.safetensors", "steps": 20},
            "is_active": True,
            "is_healthy": False,
            "health_status_message": "Local image generator"
        },
        {
            "provider_key": "gemini",
            "name": "Google Gemini 1.5 Flash (Cloud LLM)",
            "category": "llm",
            "execution_mode": "cloud",
            "base_url": "https://generativelanguage.googleapis.com",
            "settings_json": {"model": "gemini-1.5-flash"},
            "is_active": True,
            "is_healthy": False,
            "health_status_message": "Needs API Key"
        },
        {
            "provider_key": "elevenlabs",
            "name": "ElevenLabs Voice API (Cloud TTS)",
            "category": "tts",
            "execution_mode": "cloud",
            "base_url": "https://api.elevenlabs.io",
            "settings_json": {"voice_id": "21m00Tcm4TlvDq8ikWAM"},
            "is_active": False,
            "is_healthy": False,
            "health_status_message": "Optional Cloud Fallback"
        },
        {
            "provider_key": "youtube",
            "name": "YouTube Data API v3",
            "category": "youtube",
            "execution_mode": "cloud",
            "base_url": "https://www.googleapis.com/youtube/v3",
            "settings_json": {"daily_quota_limit": 10000},
            "is_active": True,
            "is_healthy": False,
            "health_status_message": "Awaiting Channel Link"
        }
    ]

    for p in default_providers:
        existing = db.query(AIProvider).filter(AIProvider.provider_key == p["provider_key"]).first()
        if not existing:
            provider = AIProvider(**p)
            db.add(provider)
    db.commit()

    # 2. Seed Default User & Demo Channel
    user = db.query(User).filter(User.email == "creator@youtube-studio.ai").first()
    if not user:
        user = User(
            email="creator@youtube-studio.ai",
            full_name="AI Studio Creator",
            hashed_password=get_password_hash("creator12345"),
            is_active=True,
            is_superuser=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        channel = Channel(
            user_id=user.id,
            channel_name="AI Cinema Telugu & Global",
            quota_units_used_today=150
        )
        db.add(channel)
        db.commit()

        # 3. Seed initial bilingual demo projects
        demo_projects = [
            {
                "title": "5 Mind-Blowing AI Breakthroughs in 2026",
                "topic": "Latest humanoid robotics, autonomous agents, and biological discoveries",
                "language": "en",
                "aspect_ratio": "16:9",
                "target_resolution": "1080p",
                "status": "ready",
                "target_scene_count": 5,
                "scenes": [
                    ("Opening hook: The world changed faster this year than in the past decade.", "What if machines could outthink whole teams of engineers? Welcome to the 2026 AI revolution.", "Futuristic cityscape with floating holographic blueprints"),
                    ("Breakthrough 1: Quantum-accelerated drug discovery.", "Scientists just designed a miracle molecule in 48 hours instead of 5 years.", "Microscopic molecular simulation glowing in neon cyan"),
                    ("Breakthrough 2: Everyday Autonomous Agents.", "From editing your videos to booking your travels, AI agents now execute complex jobs without human oversight.", "An elegant desktop screen orchestrating workflows in high speed"),
                    ("Breakthrough 3: Neuromorphic Computing chips.", "Chips that consume 90% less energy while processing neural nets in real-time.", "Silicon microchip pulsing with electric golden light"),
                    ("Outro: Are you ready for what comes next?", "Subscribe for weekly deep dives into the future of artificial intelligence.", "YouTube subscribe button animation with glowing particles")
                ]
            },
            {
                "title": "అద్భుతమైన అంతరిక్ష రహస్యాలు (Space Mysteries)",
                "topic": "జేమ్స్ వెబ్ టెలిస్కోప్ కనుగొన్న తాజా నల్ల రంధ్రాలు మరియు రహస్యాలు",
                "language": "te",
                "aspect_ratio": "9:16",
                "target_resolution": "1080p",
                "status": "scripted",
                "target_scene_count": 4,
                "scenes": [
                    ("ప్రారంభం: అంతరిక్షంలో అతిపెద్ద రహస్యం ఏమిటి?", "మనకు తెలిసిన విశ్వం కంటే తెలియని రహస్యాలే ఎక్కువ. జేమ్స్ వెబ్ టెలిస్కోప్ ఏమి చూసిందో తెలుసా?", "Deep space nebula showing a swirling golden galaxy"),
                    ("రహస్యం 1: పురాతన కాలం నాటి భారీ బ్లాక్ హోల్స్.", "విశ్వం పుట్టిన కొద్ది కాలంలోనే ఇంతటి భారీ కృష్ణబిలాలు ఎలా ఏర్పడ్డాయి? శాస్త్రవేత్తలకే అంతుచిక్కడం లేదు.", "Massive black hole with gravitational lensing in 4k"),
                    ("రహస్యం 2: నీటి ఆవిరి ఉన్న కొత్త గ్రహాలు.", "భూమికి వేల కాంతి సంవత్సరాల దూరంలో జీవం ఉండే అవకాశాలు ఉన్న గ్రహాన్ని కనుగొన్నారు.", "Exoplanet with blue atmospheres orbiting two suns"),
                    ("ముగింపు: మరిన్ని ఆసక్తికరమైన విషయాల కోసం సబ్‌స్క్రైబ్ చేసుకోండి!", "ఈ రహస్యాలపై మీ అభిప్రాయాన్ని కామెంట్‌లో తెలియజేయండి. ఇప్పుడే సబ్‌స్క్రైబ్ చేయండి!", "Dramatic space vortex with Telugu call to action text")
                ]
            }
        ]

        for p_data in demo_projects:
            scenes_data = p_data.pop("scenes")
            proj = Project(user_id=user.id, channel_id=channel.id, **p_data)
            db.add(proj)
            db.commit()
            db.refresh(proj)

            for idx, (script, narr, prompt) in enumerate(scenes_data, 1):
                scene = Scene(
                    project_id=proj.id,
                    scene_order=idx,
                    script_text=script,
                    narration_text=narr,
                    visual_prompt=prompt,
                    duration_seconds=6.0
                )
                db.add(scene)
            db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure SQLite DB and tables exist
    Base.metadata.create_all(bind=engine)
    
    # Auto-migrate SQLite schema for Phase 6 columns on publish_jobs
    from sqlalchemy import text
    with engine.connect() as conn:
        for col, col_def in [
            ("resumable_upload_url", "VARCHAR"),
            ("bytes_uploaded", "INTEGER DEFAULT 0"),
            ("total_bytes", "INTEGER DEFAULT 0"),
            ("retry_count", "INTEGER DEFAULT 0"),
            ("playlist_id", "VARCHAR"),
            ("thumbnail_attached", "BOOLEAN DEFAULT 0"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE publish_jobs ADD COLUMN {col} {col_def};"))
                conn.commit()
            except Exception:
                pass
    
    # Ensure storage directories exist
    storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../storage"))
    os.makedirs(os.path.join(storage_dir, "audio"), exist_ok=True)
    os.makedirs(os.path.join(storage_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(storage_dir, "subtitles"), exist_ok=True)
    os.makedirs(os.path.join(storage_dir, "renders"), exist_ok=True)
    os.makedirs(os.path.join(storage_dir, "thumbnails"), exist_ok=True)

    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()

    from app.services.automation_service import AutomationService
    AutomationService.start_worker()
    yield
    await AutomationService.stop_worker()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

_login_attempts = {}
_login_attempts_lock = threading.Lock()

@app.middleware("http")
async def bounded_authentication_rate_limit(request, call_next):
    if request.url.path in (
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/dev-token",
    ):
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        with _login_attempts_lock:
            window = _login_attempts.setdefault(client, [])
            window[:] = [timestamp for timestamp in window if now - timestamp < 60]
            if len(window) >= 300:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many authentication attempts. Try again later."},
                )
            window.append(now)
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-N8n-Secret"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

storage_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../storage"))
os.makedirs(os.path.join(storage_path, "audio"), exist_ok=True)
os.makedirs(os.path.join(storage_path, "images"), exist_ok=True)
os.makedirs(os.path.join(storage_path, "subtitles"), exist_ok=True)
os.makedirs(os.path.join(storage_path, "renders"), exist_ok=True)
@app.get("/storage/{asset_type}/{filename}")
def download_private_storage(
    asset_type: str,
    filename: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.models.project import Asset, Project
    if asset_type not in ("audio", "images", "subtitles", "renders", "thumbnails"):
        raise HTTPException(status_code=404, detail="Asset not found")
    if "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid asset name")
    file_path = os.path.abspath(os.path.join(storage_path, asset_type, filename))
    storage_root = os.path.abspath(storage_path)
    if os.path.commonpath([file_path, storage_root]) != storage_root:
        raise HTTPException(status_code=400, detail="Invalid asset path")
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Asset not found")

    asset = db.query(Asset).filter(Asset.file_name == filename).first()
    if asset:
        project = db.query(Project).filter(Project.id == asset.project_id, Project.user_id == current_user.id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Asset not found")
    else:
        stem = os.path.splitext(filename)[0]
        project = db.query(Project).filter(Project.id == stem, Project.user_id == current_user.id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Asset not found")
    media_type = "application/octet-stream"
    if filename.lower().endswith(".mp4"):
        media_type = "video/mp4"
    elif filename.lower().endswith(".png"):
        media_type = "image/png"
    elif filename.lower().endswith(".mp3"):
        media_type = "audio/mpeg"
    elif filename.lower().endswith(".wav"):
        media_type = "audio/wav"
    elif filename.lower().endswith(".srt"):
        media_type = "application/x-subrip"
    elif filename.lower().endswith(".vtt"):
        media_type = "text/vtt"
    return FileResponse(path=file_path, media_type=media_type, filename=filename)

@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.PROJECT_NAME, "version": settings.VERSION}
