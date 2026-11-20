"""Phase 7 persistent automation engine

Revision ID: 7d3f1a2b9c10
Revises: 2c6c99330057
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "7d3f1a2b9c10"
down_revision: Union[str, None] = "2c6c99330057"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workflows",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("definition", sa.JSON()),
        sa.Column("progress_percentage", sa.Integer(), default=0),
        sa.Column("pause_requested", sa.Boolean(), default=False),
        sa.Column("cancel_requested", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_table(
        "workflow_executions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workflow_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("error_log", sa.Text()),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "workflow_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("execution_id", sa.String(36), nullable=False),
        sa.Column("task_key", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("depends_on", sa.JSON()),
        sa.Column("progress_percentage", sa.Integer(), default=0),
        sa.Column("output_json", sa.JSON()),
        sa.Column("error_log", sa.Text()),
        sa.Column("attempt_count", sa.Integer(), default=0),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_table(
        "job_queue",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_id", sa.String(36)),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("payload", sa.JSON()),
        sa.Column("priority", sa.Integer(), nullable=False, default=100),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("attempt_count", sa.Integer(), default=0),
        sa.Column("max_attempts", sa.Integer(), default=3),
        sa.Column("next_run_at", sa.DateTime()),
        sa.Column("progress_percentage", sa.Integer(), default=0),
        sa.Column("error_log", sa.Text()),
        sa.Column("worker_id", sa.String(100)),
        sa.Column("cancelled", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_table(
        "job_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("error_log", sa.Text()),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
    )
    op.create_table(
        "approval_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), nullable=False),
        sa.Column("workflow_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("approval_type", sa.String(50), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("review_snapshot", sa.JSON()),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "scheduled_publishings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), nullable=False),
        sa.Column("workflow_id", sa.String(36), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("timezone_name", sa.String(100), nullable=False),
        sa.Column("privacy_status", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("youtube_video_id", sa.String(100)),
        sa.Column("error_log", sa.Text()),
        sa.Column("retry_count", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("project_id", sa.String(36)),
        sa.Column("workflow_id", sa.String(36)),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("level", sa.String(20)),
        sa.Column("read", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(128), nullable=False, unique=True),
        sa.Column("operation", sa.String(100), nullable=False),
        sa.Column("result_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "recovery_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scope", sa.String(100), nullable=False),
        sa.Column("scope_id", sa.String(36)),
        sa.Column("event", sa.String(100), nullable=False),
        sa.Column("details", sa.Text()),
        sa.Column("created_at", sa.DateTime()),
    )


def downgrade() -> None:
    for table in (
        "recovery_logs", "idempotency_records", "notifications",
        "scheduled_publishings", "approval_records", "job_attempts",
        "job_queue", "workflow_tasks", "workflow_executions", "workflows",
    ):
        op.drop_table(table)
