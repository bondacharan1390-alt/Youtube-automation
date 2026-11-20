"""initial_schema

Revision ID: 2c6c99330057
Revises: 
Create Date: 2026-11-20 13:08:04.723384

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c6c99330057'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255)), sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True), sa.Column("is_superuser", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime()), sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "channels", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel_name", sa.String(255), nullable=False), sa.Column("youtube_channel_id", sa.String(255)),
        sa.Column("custom_url", sa.String(255)), sa.Column("thumbnail_url", sa.String(512)),
        sa.Column("encrypted_access_token", sa.Text()), sa.Column("encrypted_refresh_token", sa.Text()),
        sa.Column("token_expiry", sa.DateTime()), sa.Column("quota_units_used_today", sa.Integer(), default=0),
        sa.Column("quota_reset_at", sa.DateTime()), sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime()), sa.Column("updated_at", sa.DateTime()),
    )
    op.create_table(
        "projects", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel_id", sa.String(36), sa.ForeignKey("channels.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(255), nullable=False), sa.Column("topic", sa.Text()),
        sa.Column("language", sa.String(10), default="en"), sa.Column("aspect_ratio", sa.String(10), default="16:9"),
        sa.Column("target_resolution", sa.String(10), default="1080p"), sa.Column("status", sa.String(50), default="draft"),
        sa.Column("target_scene_count", sa.Integer(), default=5), sa.Column("estimated_duration_seconds", sa.Float(), default=60),
        sa.Column("metadata_json", sa.JSON()), sa.Column("created_at", sa.DateTime()), sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_projects_status", "projects", ["status"])
    op.create_table(
        "scenes", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scene_order", sa.Integer(), nullable=False, default=1), sa.Column("script_text", sa.Text()),
        sa.Column("narration_text", sa.Text()), sa.Column("visual_prompt", sa.Text()), sa.Column("duration_seconds", sa.Float(), default=5),
        sa.Column("subtitle_cues", sa.JSON()), sa.Column("voice_asset_id", sa.String(36)), sa.Column("visual_asset_id", sa.String(36)),
        sa.Column("created_at", sa.DateTime()), sa.Column("updated_at", sa.DateTime()),
    )
    op.create_table(
        "assets", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_type", sa.String(50), nullable=False), sa.Column("storage_provider", sa.String(50), default="local"),
        sa.Column("file_path", sa.String(512), nullable=False), sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100)), sa.Column("file_size_bytes", sa.Integer(), default=0),
        sa.Column("checksum_sha256", sa.String(64)), sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "render_jobs", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), default="queued"), sa.Column("progress_percentage", sa.Integer(), default=0),
        sa.Column("output_file_path", sa.String(512)), sa.Column("error_log", sa.Text()),
        sa.Column("started_at", sa.DateTime()), sa.Column("completed_at", sa.DateTime()),
    )
    op.create_table(
        "publish_jobs", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("youtube_video_id", sa.String(100)), sa.Column("privacy_status", sa.String(20), default="private"),
        sa.Column("scheduled_publish_time", sa.DateTime()), sa.Column("manual_approval_granted", sa.Boolean(), default=False),
        sa.Column("approved_by", sa.String(255)), sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()), sa.Column("tags", sa.JSON()), sa.Column("upload_status", sa.String(50), default="pending"),
        sa.Column("error_message", sa.Text()), sa.Column("resumable_upload_url", sa.Text()), sa.Column("bytes_uploaded", sa.Integer(), default=0),
        sa.Column("total_bytes", sa.Integer(), default=0), sa.Column("retry_count", sa.Integer(), default=0),
        sa.Column("playlist_id", sa.String(100)), sa.Column("thumbnail_attached", sa.Boolean(), default=False), sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "playlists", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("channel_id", sa.String(36), sa.ForeignKey("channels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("youtube_playlist_id", sa.String(100)), sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()), sa.Column("privacy_status", sa.String(20), default="private"),
        sa.Column("video_count", sa.Integer(), default=0), sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "providers", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider_key", sa.String(50), nullable=False, unique=True), sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=False), sa.Column("execution_mode", sa.String(20), default="local"),
        sa.Column("is_active", sa.Boolean(), default=True), sa.Column("is_healthy", sa.Boolean(), default=False),
        sa.Column("encrypted_api_key", sa.Text()), sa.Column("base_url", sa.String(255)), sa.Column("settings_json", sa.JSON()),
        sa.Column("last_health_check", sa.DateTime()), sa.Column("health_status_message", sa.String(255)),
        sa.Column("created_at", sa.DateTime()), sa.Column("updated_at", sa.DateTime()),
    )
    op.create_table(
        "audit_logs", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36)),
        sa.Column("action", sa.String(100), nullable=False), sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(36)), sa.Column("details", sa.JSON()), sa.Column("timestamp", sa.DateTime()),
    )


def downgrade() -> None:
    for table in (
        "audit_logs", "providers", "playlists", "publish_jobs", "render_jobs",
        "assets", "scenes", "projects", "channels", "users",
    ):
        op.drop_table(table)
