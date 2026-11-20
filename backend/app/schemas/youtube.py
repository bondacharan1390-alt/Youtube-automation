from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChannelResponse(BaseModel):
    id: str
    channel_name: str
    youtube_channel_id: Optional[str] = None
    custom_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_connected: bool
    quota_units_used_today: int
    quota_limit_daily: int = 10000
    created_at: Optional[datetime] = None


class OAuthURLResponse(BaseModel):
    auth_url: str
    client_id_configured: bool
    instructions: str


class OAuthCallbackRequest(BaseModel):
    code: str
    channel_name: Optional[str] = "My YouTube Channel"
    state: Optional[str] = None


class VideoUploadRequest(BaseModel):
    project_id: str
    title: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=5000)
    tags: List[str] = []
    privacy_status: str = "private"  # 'private', 'unlisted', 'public' (ALWAYS defaults to 'private')
    scheduled_publish_time: Optional[datetime] = None
    manual_approval_granted: bool = False  # Mandatory approval check before public
    category_id: str = "28"  # Science & Technology
    attach_thumbnail: bool = True
    playlist_id: Optional[str] = None


class PublishJobResponse(BaseModel):
    job_id: str
    project_id: str
    upload_status: str
    privacy_status: str
    youtube_video_id: Optional[str] = None
    scheduled_publish_time: Optional[datetime] = None
    manual_approval_granted: bool
    error_message: Optional[str] = None
    youtube_watch_url: Optional[str] = None
    resumable_upload_url: Optional[str] = None
    bytes_uploaded: int = 0
    total_bytes: int = 0
    retry_count: int = 0
    playlist_id: Optional[str] = None
    thumbnail_attached: bool = False


class ChannelAnalyticsResponse(BaseModel):
    channel_id: str
    channel_name: str
    subscriber_count: Optional[int] = None
    view_count: Optional[int] = None
    video_count: int
    quota_units_used: int
    is_live_data: bool
    metrics_notes: str
    top_videos: List[Dict[str, Any]] = []
    data_mode: str = "not_verified"
    earliest_available_date: Optional[str] = None


class PlaylistCreateRequest(BaseModel):
    channel_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = Field("", max_length=5000)
    privacy_status: str = "private"


class PlaylistResponse(BaseModel):
    id: str
    youtube_playlist_id: str
    title: str
    description: Optional[str] = None
    privacy_status: str
    video_count: int = 0
    created_at: Optional[str] = None


class PlaylistAddVideoRequest(BaseModel):
    channel_id: Optional[str] = None
    playlist_id: str
    video_id: str


class ThumbnailAttachRequest(BaseModel):
    channel_id: Optional[str] = None
    video_id: str
    thumbnail_path: Optional[str] = None
    project_id: Optional[str] = None


class RetryUploadRequest(BaseModel):
    publish_job_id: str
