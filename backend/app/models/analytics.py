import uuid
from datetime import date, datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, Date, DateTime, ForeignKey, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class ChannelAnalyticsDaily(Base):
    __tablename__ = "channel_analytics_daily"
    __table_args__ = (UniqueConstraint("channel_id", "report_date", name="uq_channel_analytics_channel_date"),)

    id = Column(String(36), primary_key=True, default=generate_uuid)
    channel_id = Column(String(36), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    report_date = Column(Date, nullable=False, index=True)
    views = Column(Integer, default=0)
    estimated_minutes_watched = Column(Float, default=0)
    average_view_duration = Column(Float, nullable=True)
    subscribers_gained = Column(Integer, default=0)
    subscribers_lost = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    source = Column(String(50), nullable=False, default="youtube_analytics")
    retrieved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class VideoAnalyticsDaily(Base):
    __tablename__ = "video_analytics_daily"
    __table_args__ = (UniqueConstraint("channel_id", "youtube_video_id", "report_date", name="uq_video_analytics_video_date"),)

    id = Column(String(36), primary_key=True, default=generate_uuid)
    channel_id = Column(String(36), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    youtube_video_id = Column(String(100), nullable=False, index=True)
    report_date = Column(Date, nullable=False, index=True)
    views = Column(Integer, default=0)
    estimated_minutes_watched = Column(Float, default=0)
    average_view_duration = Column(Float, nullable=True)
    average_percentage_viewed = Column(Float, nullable=True)
    subscribers_gained = Column(Integer, default=0)
    subscribers_lost = Column(Integer, default=0)
    source = Column(String(50), nullable=False, default="youtube_analytics")
    retrieved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AnalyticsInsight(Base):
    __tablename__ = "analytics_insights"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    channel_id = Column(String(36), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_live_data = Column(Boolean, nullable=False, default=False)
    provider_name = Column(String(100), nullable=True)
    factual_summary = Column(JSON, default=dict)
    recommendations = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
