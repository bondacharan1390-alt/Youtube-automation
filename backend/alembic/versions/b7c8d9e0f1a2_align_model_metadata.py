"""Align migration-created schema with current model metadata.

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
"""

from collections import defaultdict
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEXES = [
    ("ix_analytics_insights_channel_id", "analytics_insights", ["channel_id"], False),
    ("ix_approval_records_project_id", "approval_records", ["project_id"], False),
    ("ix_channel_analytics_daily_channel_id", "channel_analytics_daily", ["channel_id"], False),
    ("ix_channel_analytics_daily_report_date", "channel_analytics_daily", ["report_date"], False),
    ("ix_channels_youtube_channel_id", "channels", ["youtube_channel_id"], False),
    ("ix_job_attempts_job_id", "job_attempts", ["job_id"], False),
    ("ix_job_queue_status", "job_queue", ["status"], False),
    ("ix_job_queue_task_id", "job_queue", ["task_id"], False),
    ("ix_notifications_user_id", "notifications", ["user_id"], False),
    ("ix_playlists_youtube_playlist_id", "playlists", ["youtube_playlist_id"], False),
    ("ix_projects_title", "projects", ["title"], False),
    ("ix_scheduled_publishings_project_id", "scheduled_publishings", ["project_id"], False),
    ("ix_video_analytics_daily_channel_id", "video_analytics_daily", ["channel_id"], False),
    ("ix_video_analytics_daily_youtube_video_id", "video_analytics_daily", ["youtube_video_id"], False),
    ("ix_video_analytics_daily_report_date", "video_analytics_daily", ["report_date"], False),
    ("ix_workflow_executions_workflow_id", "workflow_executions", ["workflow_id"], False),
    ("ix_workflow_executions_status", "workflow_executions", ["status"], False),
    ("ix_workflow_tasks_execution_id", "workflow_tasks", ["execution_id"], False),
    ("ix_workflow_tasks_status", "workflow_tasks", ["status"], False),
    ("ix_workflows_project_id", "workflows", ["project_id"], False),
    ("ix_workflows_status", "workflows", ["status"], False),
    ("ix_workflows_user_id", "workflows", ["user_id"], False),
]


FOREIGN_KEYS = [
    ("fk_analytics_insights_channel", "analytics_insights", ["channel_id"], "channels", ["id"], "CASCADE"),
    ("fk_approval_records_project", "approval_records", ["project_id"], "projects", ["id"], "CASCADE"),
    ("fk_approval_records_workflow", "approval_records", ["workflow_id"], "workflows", ["id"], "CASCADE"),
    ("fk_approval_records_user", "approval_records", ["user_id"], "users", ["id"], "CASCADE"),
    ("fk_channel_analytics_channel", "channel_analytics_daily", ["channel_id"], "channels", ["id"], "CASCADE"),
    ("fk_job_attempts_job", "job_attempts", ["job_id"], "job_queue", ["id"], "CASCADE"),
    ("fk_job_queue_task", "job_queue", ["task_id"], "workflow_tasks", ["id"], "CASCADE"),
    ("fk_notifications_user", "notifications", ["user_id"], "users", ["id"], "CASCADE"),
    ("fk_notifications_project", "notifications", ["project_id"], "projects", ["id"], "CASCADE"),
    ("fk_notifications_workflow", "notifications", ["workflow_id"], "workflows", ["id"], "CASCADE"),
    ("fk_scheduled_publishings_project", "scheduled_publishings", ["project_id"], "projects", ["id"], "CASCADE"),
    ("fk_scheduled_publishings_workflow", "scheduled_publishings", ["workflow_id"], "workflows", ["id"], "CASCADE"),
    ("fk_video_analytics_channel", "video_analytics_daily", ["channel_id"], "channels", ["id"], "CASCADE"),
    ("fk_workflow_executions_workflow", "workflow_executions", ["workflow_id"], "workflows", ["id"], "CASCADE"),
    ("fk_workflow_tasks_execution", "workflow_tasks", ["execution_id"], "workflow_executions", ["id"], "CASCADE"),
    ("fk_workflows_project", "workflows", ["project_id"], "projects", ["id"], "CASCADE"),
    ("fk_workflows_user", "workflows", ["user_id"], "users", ["id"], "CASCADE"),
]

TRACKING_TABLE = "alembic_b7c8d9e0f1a2_objects"


def _has_index(bind, table_name, index_name):
    inspector = sa.inspect(bind)
    return any(item["name"] == index_name for item in inspector.get_indexes(table_name))


def _matching_foreign_key(
    bind,
    table_name,
    columns,
    referred_table,
    referred_columns,
    ondelete,
):
    inspector = sa.inspect(bind)
    for item in inspector.get_foreign_keys(table_name):
        options = item.get("options") or {}
        if (
            item.get("constrained_columns") == columns
            and item.get("referred_table") == referred_table
            and item.get("referred_columns") == referred_columns
            and options.get("ondelete") == ondelete
        ):
            return item
    return None


def _group_foreign_keys():
    grouped = defaultdict(list)
    for item in FOREIGN_KEYS:
        grouped[item[1]].append(item)
    return grouped


def _tracking_table():
    return sa.table(
        TRACKING_TABLE,
        sa.column("object_type", sa.String(20)),
        sa.column("table_name", sa.String(128)),
        sa.column("object_name", sa.String(255)),
    )


def _record_created(bind, object_type, table_name, object_name):
    bind.execute(
        _tracking_table().insert().values(
            object_type=object_type,
            table_name=table_name,
            object_name=object_name,
        )
    )


def upgrade() -> None:
    bind = op.get_bind()

    if TRACKING_TABLE not in sa.inspect(bind).get_table_names():
        op.create_table(
            TRACKING_TABLE,
            sa.Column("object_type", sa.String(20), nullable=False),
            sa.Column("table_name", sa.String(128), nullable=False),
            sa.Column("object_name", sa.String(255), nullable=False),
            sa.PrimaryKeyConstraint("object_type", "table_name", "object_name"),
        )

    for index_name, table_name, columns, unique in INDEXES:
        if not _has_index(bind, table_name, index_name):
            op.create_index(index_name, table_name, columns, unique=unique)
            _record_created(bind, "index", table_name, index_name)

    for table_name, table_foreign_keys in _group_foreign_keys().items():
        missing = []
        for (
            constraint_name,
            _table_name,
            columns,
            referred_table,
            referred_columns,
            ondelete,
        ) in table_foreign_keys:
            if not _matching_foreign_key(
                bind,
                table_name,
                columns,
                referred_table,
                referred_columns,
                ondelete,
            ):
                missing.append(
                    (constraint_name, columns, referred_table, referred_columns, ondelete)
                )

        if not missing:
            continue

        with op.batch_alter_table(table_name, recreate="always") as batch_op:
            for (
                constraint_name,
                columns,
                referred_table,
                referred_columns,
                ondelete,
            ) in missing:
                batch_op.create_foreign_key(
                    constraint_name,
                    referred_table,
                    columns,
                    referred_columns,
                    ondelete=ondelete,
                )
                _record_created(bind, "foreign_key", table_name, constraint_name)


def downgrade() -> None:
    bind = op.get_bind()

    if TRACKING_TABLE not in sa.inspect(bind).get_table_names():
        return

    tracking = _tracking_table()
    rows = bind.execute(
        sa.select(
            tracking.c.object_type,
            tracking.c.table_name,
            tracking.c.object_name,
        )
    ).mappings().all()

    foreign_keys_by_table = defaultdict(list)
    for row in rows:
        if row["object_type"] == "foreign_key":
            foreign_keys_by_table[row["table_name"]].append(row["object_name"])

    for table_name, constraint_names in foreign_keys_by_table.items():
        existing_names = {
            item.get("name")
            for item in sa.inspect(bind).get_foreign_keys(table_name)
        }
        removable = [name for name in constraint_names if name in existing_names]

        if removable:
            with op.batch_alter_table(table_name, recreate="always") as batch_op:
                for constraint_name in removable:
                    batch_op.drop_constraint(constraint_name, type_="foreignkey")

    for row in reversed(rows):
        if row["object_type"] == "index" and _has_index(
            bind,
            row["table_name"],
            row["object_name"],
        ):
            op.drop_index(row["object_name"], table_name=row["table_name"])

    op.drop_table(TRACKING_TABLE)
