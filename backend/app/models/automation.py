import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    status = Column(String(30), nullable=False, default="draft", index=True)
    definition = Column(JSON, default=dict)
    progress_percentage = Column(Integer, default=0)
    pause_requested = Column(Boolean, default=False)
    cancel_requested = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="queued", index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_log = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    workflow = relationship("Workflow", back_populates="executions")
    tasks = relationship("WorkflowTask", back_populates="execution", cascade="all, delete-orphan")


class WorkflowTask(Base):
    __tablename__ = "workflow_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    execution_id = Column(String(36), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    task_key = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False, default="pending", index=True)
    position = Column(Integer, nullable=False)
    depends_on = Column(JSON, default=list)
    progress_percentage = Column(Integer, default=0)
    output_json = Column(JSON, default=dict)
    error_log = Column(Text, nullable=True)
    attempt_count = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    execution = relationship("WorkflowExecution", back_populates="tasks")
    job = relationship("JobQueue", back_populates="task", uselist=False, cascade="all, delete-orphan")


class JobQueue(Base):
    __tablename__ = "job_queue"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("workflow_tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    job_type = Column(String(50), nullable=False)
    payload = Column(JSON, default=dict)
    priority = Column(Integer, nullable=False, default=100)
    status = Column(String(30), nullable=False, default="queued", index=True)
    idempotency_key = Column(String(128), nullable=False, unique=True, index=True)
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    next_run_at = Column(DateTime, nullable=True)
    progress_percentage = Column(Integer, default=0)
    error_log = Column(Text, nullable=True)
    worker_id = Column(String(100), nullable=True)
    cancelled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    task = relationship("WorkflowTask", back_populates="job")
    attempts = relationship("JobAttempt", back_populates="job", cascade="all, delete-orphan")


class JobAttempt(Base):
    __tablename__ = "job_attempts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("job_queue.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_number = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False)
    error_log = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    job = relationship("JobQueue", back_populates="attempts")


class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    approval_type = Column(String(50), nullable=False)
    approved = Column(Boolean, nullable=False, default=False)
    review_snapshot = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ScheduledPublishing(Base):
    __tablename__ = "scheduled_publishings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    timezone_name = Column(String(100), nullable=False)
    privacy_status = Column(String(20), nullable=False, default="private")
    status = Column(String(30), nullable=False, default="scheduled")
    youtube_video_id = Column(String(100), nullable=True)
    error_log = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=True)
    notification_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String(20), default="info")
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    key = Column(String(128), nullable=False, unique=True, index=True)
    operation = Column(String(100), nullable=False)
    result_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class RecoveryLog(Base):
    __tablename__ = "recovery_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scope = Column(String(100), nullable=False)
    scope_id = Column(String(36), nullable=True)
    event = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
