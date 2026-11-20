"""YouTube API — OAuth, Channel Management, Upload & Scheduling, Analytics, Playlists & Resumable Retries."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from io import BytesIO
from datetime import date
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from app.api.v1.deps import get_db, get_current_user
from app.models.user import User, Channel
from app.models.project import Project, PublishJob
from app.schemas.youtube import (
    ChannelResponse, OAuthURLResponse, OAuthCallbackRequest,
    VideoUploadRequest, PublishJobResponse, ChannelAnalyticsResponse,
    PlaylistCreateRequest, PlaylistResponse, PlaylistAddVideoRequest,
    ThumbnailAttachRequest, RetryUploadRequest,
)
from app.services.youtube.youtube_service import YouTubeService
from app.services.youtube.playlist_service import PlaylistService

router = APIRouter(prefix="/youtube", tags=["YouTube"])


def _format_publish_job(j: PublishJob) -> PublishJobResponse:
    watch_url = f"https://youtu.be/{j.youtube_video_id}" if j.youtube_video_id else None
    return PublishJobResponse(
        job_id=j.id,
        project_id=j.project_id,
        upload_status=j.upload_status,
        privacy_status=j.privacy_status,
        youtube_video_id=j.youtube_video_id,
        scheduled_publish_time=j.scheduled_publish_time,
        manual_approval_granted=j.manual_approval_granted,
        error_message=j.error_message,
        youtube_watch_url=watch_url,
        resumable_upload_url=j.resumable_upload_url,
        bytes_uploaded=j.bytes_uploaded or 0,
        total_bytes=j.total_bytes or 0,
        retry_count=j.retry_count or 0,
        playlist_id=j.playlist_id,
        thumbnail_attached=bool(j.thumbnail_attached),
    )


@router.get("/channels", response_model=List[ChannelResponse])
def list_user_channels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    channels = db.query(Channel).filter(Channel.user_id == current_user.id).all()
    return [
        ChannelResponse(
            id=c.id,
            channel_name=c.channel_name,
            youtube_channel_id=c.youtube_channel_id,
            custom_url=c.custom_url,
            thumbnail_url=c.thumbnail_url,
            is_connected=bool(c.encrypted_access_token or c.encrypted_refresh_token),
            quota_units_used_today=c.quota_units_used_today,
            created_at=c.created_at,
        )
        for c in channels
    ]


@router.get("/oauth/url", response_model=OAuthURLResponse)
def get_oauth_authorization_url(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = YouTubeService.get_oauth_url(db, current_user.id)
    return OAuthURLResponse(**data)


@router.post("/oauth/callback", response_model=ChannelResponse)
def handle_oauth_callback(
    req: OAuthCallbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not req.state:
        raise HTTPException(status_code=400, detail="OAuth state is required")
    from app.core.security import decode_oauth_state
    if not decode_oauth_state(req.state, current_user.id):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    try:
        channel = YouTubeService.exchange_code_for_tokens(
            code=req.code,
            user_id=current_user.id,
            channel_name=req.channel_name or "My YouTube Channel",
            db=db,
        )
        return ChannelResponse(
            id=channel.id,
            channel_name=channel.channel_name,
            youtube_channel_id=channel.youtube_channel_id,
            custom_url=channel.custom_url,
            thumbnail_url=channel.thumbnail_url,
            is_connected=True,
            quota_units_used_today=channel.quota_units_used_today,
            created_at=channel.created_at,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload", response_model=PublishJobResponse)
def upload_or_schedule_video(
    req: VideoUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == req.project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        job = YouTubeService.upload_video(
            project_id=req.project_id,
            user=current_user,
            title=req.title,
            description=req.description or project.topic or "",
            tags=req.tags,
            privacy_status=req.privacy_status,
            scheduled_publish_time=req.scheduled_publish_time,
            manual_approval_granted=req.manual_approval_granted,
            db=db,
            attach_thumbnail=req.attach_thumbnail,
            playlist_id=req.playlist_id,
        )
        return _format_publish_job(job)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/{channel_id}", response_model=ChannelAnalyticsResponse)
def get_channel_analytics(
    channel_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    channel = db.query(Channel).filter(Channel.id == channel_id, Channel.user_id == current_user.id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    data = YouTubeService.get_authorized_channel_analytics(channel_id, db)
    return ChannelAnalyticsResponse(**data)


@router.get("/publish-jobs/{project_id}", response_model=List[PublishJobResponse])
def get_project_publish_jobs(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    jobs = db.query(PublishJob).filter(PublishJob.project_id == project_id).order_by(PublishJob.created_at.desc()).all()
    return [_format_publish_job(j) for j in jobs]


@router.get("/analytics/{channel_id}/history")
def get_channel_analytics_history(
    channel_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    channel = db.query(Channel).filter(Channel.id == channel_id, Channel.user_id == current_user.id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    from app.services.analytics_service import YouTubeAnalyticsService
    try:
        return YouTubeAnalyticsService.retrieve_daily_history(channel, start_date, end_date, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/analytics/{channel_id}/videos/{video_id}/retention")
def get_video_audience_retention(
    channel_id: str,
    video_id: str,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    channel = db.query(Channel).filter(Channel.id == channel_id, Channel.user_id == current_user.id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    from app.services.analytics_service import YouTubeAnalyticsService
    return YouTubeAnalyticsService.retrieve_video_retention(
        channel, video_id, start_date, end_date
    )


@router.post("/analytics/{channel_id}/insights")
def generate_channel_analytics_insights(
    channel_id: str,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    channel = db.query(Channel).filter(Channel.id == channel_id, Channel.user_id == current_user.id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    from app.services.analytics_service import YouTubeAnalyticsService
    try:
        report = YouTubeAnalyticsService.retrieve_daily_history(channel, start_date, end_date, db)
        return YouTubeAnalyticsService.generate_ai_insights(channel, report, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/analytics/{channel_id}/export/csv")
def export_channel_analytics_csv(
    channel_id: str,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    channel = db.query(Channel).filter(Channel.id == channel_id, Channel.user_id == current_user.id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    from app.services.analytics_service import YouTubeAnalyticsService
    try:
        report = YouTubeAnalyticsService.retrieve_daily_history(channel, start_date, end_date, db)
        csv_text = YouTubeAnalyticsService.export_csv(channel, report)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return StreamingResponse(
        BytesIO(csv_text.encode("utf-8")),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=channel-{channel_id}-{start_date}-to-{end_date}.csv"
        },
    )


@router.get("/analytics/{channel_id}/export/pdf")
def export_channel_analytics_pdf(
    channel_id: str,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    channel = db.query(Channel).filter(Channel.id == channel_id, Channel.user_id == current_user.id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    from app.services.analytics_service import YouTubeAnalyticsService
    try:
        report = YouTubeAnalyticsService.retrieve_daily_history(channel, start_date, end_date, db)
        pdf_bytes = YouTubeAnalyticsService.export_pdf(channel, report)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=channel-{channel_id}-{start_date}-to-{end_date}.pdf"
        },
    )


# --- Phase 6: Playlists & Resumable Upload Retries & Thumbnail Attachment ---

@router.get("/playlists", response_model=List[PlaylistResponse])
def list_playlists(
    channel_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List playlists for a channel (or user's default active channel)."""
    channel = None
    if channel_id:
        channel = db.query(Channel).filter(Channel.id == channel_id, Channel.user_id == current_user.id).first()
    else:
        channel = db.query(Channel).filter(Channel.user_id == current_user.id, Channel.is_active == True).first()

    if not channel:
        # If no channel yet, return empty list
        return []

    playlists = PlaylistService.list_playlists(channel.id, db)
    return [PlaylistResponse(**p) for p in playlists]


@router.post("/playlists", response_model=PlaylistResponse)
def create_playlist(
    req: PlaylistCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new playlist on YouTube and save in DB."""
    channel = None
    if req.channel_id:
        channel = db.query(Channel).filter(Channel.id == req.channel_id, Channel.user_id == current_user.id).first()
    else:
        channel = db.query(Channel).filter(Channel.user_id == current_user.id, Channel.is_active == True).first()

    if not channel:
        raise HTTPException(status_code=404, detail="Active YouTube channel not found for this user.")

    try:
        p = PlaylistService.create_playlist(
            channel_id=channel.id,
            title=req.title,
            description=req.description or "",
            privacy_status=req.privacy_status,
            db=db,
        )
        return PlaylistResponse(**p)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playlists/add-video")
def add_video_to_playlist(
    req: PlaylistAddVideoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add an uploaded video to a YouTube playlist."""
    channel = None
    if req.channel_id:
        channel = db.query(Channel).filter(Channel.id == req.channel_id, Channel.user_id == current_user.id).first()
    else:
        channel = db.query(Channel).filter(Channel.user_id == current_user.id, Channel.is_active == True).first()

    if not channel:
        raise HTTPException(status_code=404, detail="Active YouTube channel not found.")

    try:
        res = PlaylistService.add_video_to_playlist(
            channel_id=channel.id,
            playlist_id=req.playlist_id,
            youtube_video_id=req.video_id,
            db=db,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry/{publish_job_id}", response_model=PublishJobResponse)
def retry_failed_upload(
    publish_job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retry an interrupted or failed video upload with deduplication and bounded retries."""
    try:
        job = YouTubeService.retry_upload(
            publish_job_id=publish_job_id,
            user=current_user,
            db=db,
        )
        return _format_publish_job(job)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/thumbnails/attach")
def attach_thumbnail(
    req: ThumbnailAttachRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Attach thumbnail image to an existing YouTube video."""
    channel = None
    if req.channel_id:
        channel = db.query(Channel).filter(Channel.id == req.channel_id, Channel.user_id == current_user.id).first()
    else:
        channel = db.query(Channel).filter(Channel.user_id == current_user.id, Channel.is_active == True).first()

    if not channel:
        raise HTTPException(status_code=404, detail="Active YouTube channel not found.")

    thumb_path = req.thumbnail_path
    if not thumb_path and req.project_id:
        project = db.query(Project).filter(Project.id == req.project_id, Project.user_id == current_user.id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage"))
        thumb_path = os.path.join(storage_dir, "thumbnails", f"{req.project_id}.png")

    if not thumb_path or not os.path.exists(thumb_path):
        raise HTTPException(status_code=400, detail="Thumbnail file not found.")

    res = YouTubeService.attach_thumbnail_to_video(
        channel=channel,
        youtube_video_id=req.video_id,
        thumbnail_path=thumb_path,
        db=db,
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Thumbnail attachment failed"))
    return res
