"""Phase 5 analytics history and insight persistence

Revision ID: 9b4e2c1a7d33
Revises: 7d3f1a2b9c10
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "9b4e2c1a7d33"
down_revision: Union[str, None] = "7d3f1a2b9c10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "channel_analytics_daily",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("channel_id", sa.String(36), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("views", sa.Integer(), default=0),
        sa.Column("estimated_minutes_watched", sa.Float(), default=0),
        sa.Column("average_view_duration", sa.Float(), nullable=True),
        sa.Column("subscribers_gained", sa.Integer(), default=0),
        sa.Column("subscribers_lost", sa.Integer(), default=0),
        sa.Column("likes", sa.Integer(), default=0),
        sa.Column("comments", sa.Integer(), default=0),
        sa.Column("shares", sa.Integer(), default=0),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("retrieved_at", sa.DateTime()),
    )
    op.create_index(
        "ix_channel_analytics_channel_date",
        "channel_analytics_daily",
        ["channel_id", "report_date"],
        unique=True,
    )

    op.create_table(
        "video_analytics_daily",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("channel_id", sa.String(36), nullable=False),
        sa.Column("youtube_video_id", sa.String(100), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("views", sa.Integer(), default=0),
        sa.Column("estimated_minutes_watched", sa.Float(), default=0),
        sa.Column("average_view_duration", sa.Float(), nullable=True),
        sa.Column("average_percentage_viewed", sa.Float(), nullable=True),
        sa.Column("subscribers_gained", sa.Integer(), default=0),
        sa.Column("subscribers_lost", sa.Integer(), default=0),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("retrieved_at", sa.DateTime()),
    )
    op.create_index(
        "ix_video_analytics_video_date",
        "video_analytics_daily",
        ["channel_id", "youtube_video_id", "report_date"],
        unique=True,
    )

    op.create_table(
        "analytics_insights",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("channel_id", sa.String(36), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("is_live_data", sa.Boolean(), nullable=False),
        sa.Column("provider_name", sa.String(100)),
        sa.Column("factual_summary", sa.JSON()),
        sa.Column("recommendations", sa.JSON()),
        sa.Column("created_at", sa.DateTime()),
    )


def downgrade() -> None:
    op.drop_table("analytics_insights")
    op.drop_index("ix_video_analytics_video_date", "video_analytics_daily")
    op.drop_table("video_analytics_daily")
    op.drop_index("ix_channel_analytics_channel_date", "channel_analytics_daily")
    op.drop_table("channel_analytics_daily")
