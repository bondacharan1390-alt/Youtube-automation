"""Add asynchronous Higgsfield generation records."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8e4f6b7c1d22"
down_revision: Union[str, None] = "7d3f1a2b9c10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "higgsfield_generations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("scene_id", sa.String(36)),
        sa.Column("request_id", sa.String(255), nullable=False, unique=True),
        sa.Column("model_path", sa.String(255), nullable=False),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, default="queued"),
        sa.Column("status_url", sa.Text()),
        sa.Column("cancel_url", sa.Text()),
        sa.Column("output_url", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
    )
    op.create_index("ix_higgsfield_generations_user_id", "higgsfield_generations", ["user_id"])
    op.create_index("ix_higgsfield_generations_project_id", "higgsfield_generations", ["project_id"])
    op.create_index("ix_higgsfield_generations_scene_id", "higgsfield_generations", ["scene_id"])
    op.create_index("ix_higgsfield_generations_request_id", "higgsfield_generations", ["request_id"])
    op.create_index("ix_higgsfield_generations_status", "higgsfield_generations", ["status"])


def downgrade() -> None:
    op.drop_table("higgsfield_generations")
