import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, JSON, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel_id = Column(String(36), ForeignKey("channels.id", ondelete="SET NULL"), nullable=True)
    
    title = Column(String(255), nullable=False, index=True)
    topic = Column(Text, nullable=True)
    language = Column(String(10), default="en") # 'en' or 'te'
    aspect_ratio = Column(String(10), default="16:9") # '16:9' or '9:16'
    target_resolution = Column(String(10), default="1080p") # '720p' or '1080p'
    
    # Workflow Status: 'draft', 'scripted', 'voiced', 'rendered', 'ready', 'published'
    status = Column(String(50), default="draft", index=True)
    target_scene_count = Column(Integer, default=5)
    estimated_duration_seconds = Column(Float, default=60.0)
    
    # JSON metadata for tags, tone, and extra settings
    metadata_json = Column(JSON, default=dict)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="projects")
    channel = relationship("Channel", back_populates="projects")
    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan", order_by="Scene.scene_order")
    assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")
    render_jobs = relationship("RenderJob", back_populates="project", cascade="all, delete-orphan")
    publish_jobs = relationship("PublishJob", back_populates="project", cascade="all, delete-orphan")

class Scene(Base):
    __tablename__ = "scenes"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    scene_order = Column(Integer, nullable=False, default=1)
    
    script_text = Column(Text, nullable=True)
    narration_text = Column(Text, nullable=True)
    visual_prompt = Column(Text, nullable=True)
    duration_seconds = Column(Float, default=5.0)
    
    # Subtitle cues with word-level or phrase-level timestamps
    subtitle_cues = Column(JSON, default=list)
    
    # Asset references
    voice_asset_id = Column(String(36), nullable=True)
    visual_asset_id = Column(String(36), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="scenes")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    # 'audio', 'image', 'video', 'subtitle', 'thumbnail'
    asset_type = Column(String(50), nullable=False)
    storage_provider = Column(String(50), default="local") # 'local', 'r2', 'supabase'
    file_path = Column(String(512), nullable=False)
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_size_bytes = Column(Integer, default=0)
    checksum_sha256 = Column(String(64), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="assets")

class RenderJob(Base):
    __tablename__ = "render_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    # 'queued', 'rendering', 'completed', 'failed'
    status = Column(String(50), default="queued")
    progress_percentage = Column(Integer, default=0)
    output_file_path = Column(String(512), nullable=True)
    error_log = Column(Text, nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="render_jobs")

class PublishJob(Base):
    __tablename__ = "publish_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    youtube_video_id = Column(String(100), nullable=True)
    privacy_status = Column(String(20), default="private") # 'private', 'unlisted', 'public'
    scheduled_publish_time = Column(DateTime, nullable=True)
    manual_approval_granted = Column(Boolean, default=False)
    approved_by = Column(String(255), nullable=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    upload_status = Column(String(50), default="pending") # 'pending', 'uploading', 'uploaded', 'failed'
    error_message = Column(Text, nullable=True)
    
    # Resumable upload & tracking
    resumable_upload_url = Column(Text, nullable=True)
    bytes_uploaded = Column(Integer, default=0)
    total_bytes = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    playlist_id = Column(String(100), nullable=True)
    thumbnail_attached = Column(Boolean, default=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="publish_jobs")


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    channel_id = Column(String(36), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    youtube_playlist_id = Column(String(100), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    privacy_status = Column(String(20), default="private")
    video_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
