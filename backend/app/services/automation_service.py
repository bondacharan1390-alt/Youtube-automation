import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.automation import (
    ApprovalRecord,
    IdempotencyRecord,
    JobAttempt,
    JobQueue,
    Notification,
    RecoveryLog,
    ScheduledPublishing,
    Workflow,
    WorkflowExecution,
    WorkflowTask,
)
from app.models.project import Asset, Project, PublishJob
from app.models.user import User
from app.services.hardware_queue import HardwareTaskQueue
from app.services.research_service import ResearchService
from app.services.script_service import ScriptService
from app.services.voice.voice_service import VoiceService
from app.services.image.image_service import ImageService
from app.services.video.render_job import RenderJobService
from app.services.thumbnail.thumbnail_service import ThumbnailService
from app.schemas.script import ScriptGenerateRequest
from app.schemas.thumbnail import ThumbnailGenerateRequest

logger = logging.getLogger(__name__)


TASK_SEQUENCE = [
    ("research", "Research"),
    ("script", "Script"),
    ("storyboard", "Storyboard"),
    ("voice", "Voice"),
    ("images", "Images"),
    ("subtitles", "Subtitles"),
    ("video", "Video"),
    ("editing", "Editing"),
    ("thumbnail", "Thumbnail"),
    ("seo_metadata", "SEO Metadata"),
    ("quality_check", "Quality Check"),
    ("approval", "User Approval"),
    ("upload", "YouTube Upload"),
]


class AutomationService:
    _worker_task: Optional[asyncio.Task] = None
    _worker_id = f"automation-{uuid.uuid4()}"

    @staticmethod
    def add_notification(db: Session, user_id: str, project_id: str, workflow_id: str,
                         notification_type: str, title: str, message: str, level: str = "info") -> Notification:
        item = Notification(
            user_id=user_id,
            project_id=project_id,
            workflow_id=workflow_id,
            notification_type=notification_type,
            title=title,
            message=message,
            level=level,
        )
        db.add(item)
        db.commit()
        return item

    @staticmethod
    def create_workflow(project: Project, user_id: str, settings: Dict[str, Any], db: Session,
                        idempotency_key: Optional[str] = None) -> Workflow:
        key = idempotency_key or f"create-workflow:{project.id}:{uuid.uuid4()}"
        existing = db.query(IdempotencyRecord).filter(IdempotencyRecord.key == key).first()
        if existing:
            workflow = db.query(Workflow).filter(Workflow.id == existing.result_json.get("workflow_id")).first()
            if workflow:
                return workflow

        workflow = Workflow(
            project_id=project.id,
            user_id=user_id,
            name=f"Automation: {project.title}",
            status="draft",
            definition={"tasks": TASK_SEQUENCE, "settings": settings},
        )
        db.add(workflow)
        db.flush()

        execution = WorkflowExecution(workflow_id=workflow.id, status="draft")
        db.add(execution)
        db.flush()

        previous = []
        for position, (task_key, name) in enumerate(TASK_SEQUENCE):
            task = WorkflowTask(
                execution_id=execution.id,
                task_key=task_key,
                name=name,
                position=position,
                status="pending",
                depends_on=list(previous),
            )
            db.add(task)
            previous = [task_key]
        db.commit()
        db.refresh(workflow)

        record = IdempotencyRecord(
            key=key,
            operation="create_workflow",
            result_json={"workflow_id": workflow.id, "execution_id": execution.id},
        )
        db.add(record)
        db.commit()
        return workflow

    @staticmethod
    def start_workflow(workflow_id: str, db: Session) -> WorkflowExecution:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError("Workflow not found")
        execution = db.query(WorkflowExecution).filter(WorkflowExecution.workflow_id == workflow_id).order_by(
            WorkflowExecution.created_at.desc()
        ).first()
        if not execution:
            raise ValueError("Workflow execution not found")
        if execution.status in ("running", "queued"):
            return execution

        execution.status = "queued"
        execution.started_at = datetime.now(timezone.utc)
        execution.error_log = None
        execution.completed_at = None
        workflow.status = "queued"
        workflow.pause_requested = False
        workflow.cancel_requested = False

        for task in execution.tasks:
            if task.status not in ("completed",):
                task.status = "pending"
                task.error_log = None
                task.progress_percentage = 0
                db.flush()
                if task.job:
                    task.job.status = "queued"
                    task.job.cancelled = False
                    task.job.error_log = None

        approval_task = next((t for t in execution.tasks if t.task_key == "approval"), None)
        if approval_task:
            approval_task.status = "waiting_approval"

        db.commit()
        db.refresh(execution)
        AutomationService.add_notification(
            db, workflow.user_id, workflow.project_id, workflow.id,
            "workflow_started", "Workflow started",
            f"Automation workflow '{workflow.name}' has started.",
        )
        return execution

    @staticmethod
    def ensure_jobs(db: Session) -> int:
        created = 0
        executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.status.in_(["queued", "running", "paused"])
        ).all()
        for execution in executions:
            workflow = execution.workflow
            if workflow.pause_requested or workflow.cancel_requested:
                continue
            if execution.status == "paused":
                continue
            if execution.status == "queued":
                execution.status = "running"
            for task in sorted(execution.tasks, key=lambda t: t.position):
                if task.status not in ("pending", "failed", "waiting_schedule"):
                    continue
                if task.task_key == "approval":
                    task.status = "waiting_approval"
                    continue
                if task.task_key == "upload":
                    approval = db.query(ApprovalRecord).filter(
                        ApprovalRecord.project_id == workflow.project_id,
                        ApprovalRecord.workflow_id == workflow.id,
                        ApprovalRecord.approved == True,
                        ApprovalRecord.approval_type == "publish",
                    ).first()
                    quality = next((t for t in execution.tasks if t.task_key == "quality_check"), None)
                    if not approval or not quality or quality.status != "completed":
                        task.status = "blocked"
                        continue
                    schedule = db.query(ScheduledPublishing).filter(
                        ScheduledPublishing.project_id == workflow.project_id,
                        ScheduledPublishing.workflow_id == workflow.id,
                    ).order_by(ScheduledPublishing.created_at.desc()).first()
                    if schedule:
                        schedule_at = schedule.scheduled_at
                        if schedule_at.tzinfo is None:
                            schedule_at = schedule_at.replace(tzinfo=timezone.utc)
                        if schedule.status != "uploaded_private" and schedule_at > datetime.now(timezone.utc):
                            task.status = "waiting_schedule"
                            continue
                previous_keys = task.depends_on or []
                previous = {t.task_key: t.status for t in execution.tasks if t.task_key in previous_keys}
                if previous and any(status != "completed" for status in previous.values()):
                    continue
                key = f"{execution.id}:{task.task_key}"
                job = db.query(JobQueue).filter(JobQueue.idempotency_key == key).first()
                if not job:
                    job = JobQueue(
                        task_id=task.id,
                        job_type=f"workflow:{task.task_key}",
                        payload={"workflow_id": workflow.id, "execution_id": execution.id,
                                 "project_id": workflow.project_id, "task_key": task.task_key},
                        priority=100 - task.position,
                        idempotency_key=key,
                        status="queued",
                        max_attempts=3,
                    )
                    db.add(job)
                    db.flush()
                    created += 1
                elif job.status in ("completed", "cancelled", "failed"):
                    if task.status == "failed":
                        job.status = "queued"
                        job.cancelled = False
                        job.error_log = None
                task.status = "queued"
        db.commit()
        return created

    @staticmethod
    async def execute_task(task: WorkflowTask, workflow: Workflow, project: Project, db: Session) -> Dict[str, Any]:
        settings = workflow.definition.get("settings", {}) if workflow.definition else {}
        task_key = task.task_key

        if task_key == "research":
            return ResearchService.analyze_topic(project.topic or project.title, project.language, db).model_dump()

        if task_key == "script":
            req = ScriptGenerateRequest(
                project_id=project.id,
                title=project.title,
                topic=project.topic or project.title,
                language=project.language,
                aspect_ratio=project.aspect_ratio,
                target_scene_count=settings.get("target_scene_count", project.target_scene_count),
                tone=settings.get("tone", "engaging"),
            )
            result = ScriptService.generate_script(req=req, db=db)
            return result.model_dump()

        if task_key == "storyboard":
            return ScriptService.export_storyboard(project.id, db).model_dump()

        if task_key == "voice":
            results = await VoiceService.synthesize_project_scenes(
                project.id,
                voice_id=settings.get("voice_id", "te-IN-MohanNeural" if project.language == "te" else "en-US-ChristopherNeural"),
                speed=float(settings.get("voice_speed", 1.0)),
                pitch=float(settings.get("voice_pitch", 0.0)),
                db=db,
            )
            return {"scene_count": len(results), "assets": results}

        if task_key == "images":
            results = await ImageService.generate_project_images(project.id, db=db)
            return {"scene_count": len(results), "assets": results}

        if task_key == "subtitles":
            from app.services.video.subtitle_generator import generate_srt, generate_vtt
            scenes = [{"scene_order": s.scene_order, "narration_text": s.narration_text,
                       "script_text": s.script_text, "duration_seconds": s.duration_seconds or 5.0}
                      for s in sorted(project.scenes, key=lambda s: s.scene_order)]
            subtitle_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage/subtitles"))
            os.makedirs(subtitle_dir, exist_ok=True)
            srt_path = os.path.join(subtitle_dir, f"{project.id}.srt")
            vtt_path = os.path.join(subtitle_dir, f"{project.id}.vtt")
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(generate_srt(scenes))
            with open(vtt_path, "w", encoding="utf-8") as f:
                f.write(generate_vtt(scenes))
            return {"srt": srt_path, "vtt": vtt_path}

        if task_key == "video":
            render_job = await RenderJobService.start_render(
                project_id=project.id,
                resolution=settings.get("target_resolution", project.target_resolution),
                include_subtitles=settings.get("include_subtitles", True),
                bgm_volume=float(settings.get("bgm_volume", 0.15)),
                db=db,
            )
            for _ in range(600):
                db.expire_all()
                current = db.query(type(render_job)).filter(type(render_job).id == render_job.id).first()
                if current and current.status == "completed":
                    return {"render_job_id": render_job.id, "output_file_path": current.output_file_path}
                if current and current.status == "failed":
                    raise RuntimeError(current.error_log or "Video render failed")
                if current and current.status == "cancelled":
                    raise RuntimeError("Video render cancelled")
                await asyncio.sleep(1)
            raise RuntimeError("Video render timed out")

        if task_key == "editing":
            video_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage/renders", f"{project.id}.mp4"))
            if not os.path.exists(video_path):
                raise RuntimeError("Final MP4 is missing after video rendering")
            return {"final_mp4": video_path, "edited": True}

        if task_key == "thumbnail":
            bg = None
            for scene in project.scenes:
                candidate = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage/images", f"scene_{scene.id}.png"))
                if os.path.exists(candidate):
                    bg = candidate
                    break
            result = ThumbnailService.generate_thumbnail(
                project_id=project.id,
                headline=settings.get("thumbnail_headline", project.title),
                subtitle=settings.get("thumbnail_subtitle"),
                badge_text=settings.get("thumbnail_badge", "NEW"),
                theme_name=settings.get("thumbnail_theme", "viral_punch"),
                aspect_ratio=project.aspect_ratio,
                bg_image_path=bg,
                db=db,
            )
            return result

        if task_key == "seo_metadata":
            tags = project.metadata_json.get("tags", []) if project.metadata_json else []
            if not tags:
                tags = [project.topic or project.title, project.language, "YouTube"]
            description = settings.get("description") or f"{project.topic or project.title}\n\nCreated with AI YouTube Automation Studio."
            result = {
                "title": settings.get("title", project.title)[:100],
                "description": description[:5000],
                "tags": tags[:500],
                "privacy_status": "private",
            }
            project.metadata_json = {**(project.metadata_json or {}), "seo": result}
            db.commit()
            return result

        if task_key == "quality_check":
            video_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage/renders", f"{project.id}.mp4"))
            thumb_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage/thumbnails", f"{project.id}.png"))
            if not os.path.exists(video_path) or os.path.getsize(video_path) < 100:
                raise RuntimeError("Quality check failed: final MP4 is missing or empty")
            if not os.path.exists(thumb_path):
                raise RuntimeError("Quality check failed: thumbnail is missing")
            seo = (project.metadata_json or {}).get("seo", {})
            if not seo.get("title") or not seo.get("description"):
                raise RuntimeError("Quality check failed: SEO metadata is incomplete")
            return {"passed": True, "video_bytes": os.path.getsize(video_path),
                    "thumbnail_bytes": os.path.getsize(thumb_path)}

        if task_key == "approval":
            return {"status": "waiting_for_explicit_user_approval"}

        if task_key == "upload":
            scheduled = db.query(ScheduledPublishing).filter(
                ScheduledPublishing.project_id == project.id,
                ScheduledPublishing.workflow_id == workflow.id,
            ).order_by(ScheduledPublishing.created_at.desc()).first()
            if scheduled:
                schedule_at = scheduled.scheduled_at
                if schedule_at.tzinfo is None:
                    schedule_at = schedule_at.replace(tzinfo=timezone.utc)
                if schedule_at > datetime.now(timezone.utc):
                    return {"status": "waiting_schedule", "scheduled_at": schedule_at.isoformat()}
            approval = db.query(ApprovalRecord).filter(
                ApprovalRecord.project_id == project.id,
                ApprovalRecord.workflow_id == workflow.id,
                ApprovalRecord.approved == True,
                ApprovalRecord.approval_type == "publish",
            ).first()
            if not approval:
                raise RuntimeError("Publishing blocked: explicit user approval is required")

            scheduled = db.query(ScheduledPublishing).filter(
                ScheduledPublishing.project_id == project.id,
                ScheduledPublishing.workflow_id == workflow.id,
            ).order_by(ScheduledPublishing.created_at.desc()).first()
            privacy = approval.review_snapshot.get("privacy_status", "private")
            if privacy not in ("private", "unlisted", "public"):
                privacy = "private"
            if privacy == "public" and not approval.review_snapshot.get("public_publish_confirmed", False):
                raise RuntimeError("Public publishing requires explicit public-publish confirmation")

            seo = (project.metadata_json or {}).get("seo", {})
            from app.services.youtube.youtube_service import YouTubeService
            user = db.query(User).filter(User.id == workflow.user_id).first()
            if not user:
                raise RuntimeError("Publishing blocked: workflow user not found")
            publish_job = YouTubeService.upload_video(
                project_id=project.id,
                user=user,
                title=approval.review_snapshot.get("title") or seo.get("title", project.title),
                description=approval.review_snapshot.get("description") or seo.get("description", project.topic or ""),
                tags=seo.get("tags", []),
                privacy_status=privacy,
                scheduled_publish_time=scheduled.scheduled_at if scheduled else None,
                manual_approval_granted=True,
                db=db,
                attach_thumbnail=True,
            )
            if publish_job.upload_status != "uploaded":
                raise RuntimeError(publish_job.error_message or "YouTube upload did not complete")
            if scheduled:
                scheduled.status = "published" if privacy != "private" else "uploaded_private"
                scheduled.youtube_video_id = publish_job.youtube_video_id
                db.commit()
            return {
                "youtube_video_id": publish_job.youtube_video_id,
                "upload_status": publish_job.upload_status,
                "privacy_status": publish_job.privacy_status,
            }

        raise RuntimeError(f"Unknown workflow task: {task_key}")

    @staticmethod
    def pause_workflow(workflow_id: str, db: Session) -> Workflow:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError("Workflow not found")
        workflow.pause_requested = True
        workflow.status = "paused"
        for execution in workflow.executions:
            if execution.status in ("running", "queued"):
                execution.status = "paused"
        db.commit()
        db.refresh(workflow)
        return workflow

    @staticmethod
    def resume_workflow(workflow_id: str, db: Session) -> Workflow:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError("Workflow not found")
        workflow.pause_requested = False
        workflow.status = "running"
        for execution in workflow.executions:
            if execution.status == "paused":
                execution.status = "queued"
        db.commit()
        db.refresh(workflow)
        return workflow

    @staticmethod
    def cancel_workflow(workflow_id: str, db: Session) -> Workflow:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError("Workflow not found")
        workflow.cancel_requested = True
        workflow.status = "cancelled"
        for execution in workflow.executions:
            if execution.status not in ("completed", "failed", "cancelled"):
                execution.status = "cancelled"
                execution.completed_at = datetime.now(timezone.utc)
            for task in execution.tasks:
                if task.status not in ("completed",):
                    task.status = "cancelled"
                if task.job:
                    task.job.status = "cancelled"
                    task.job.cancelled = True
        db.commit()
        db.refresh(workflow)
        return workflow

    @staticmethod
    def approve_workflow(workflow_id: str, project_id: str, user: User, db: Session,
                        privacy_status: str = "private", title: Optional[str] = None,
                        description: Optional[str] = None, scheduled_at: Optional[datetime] = None,
                        timezone_name: str = "UTC", idempotency_key: Optional[str] = None) -> ApprovalRecord:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.project_id == project_id).first()
        if not workflow:
            raise ValueError("Workflow not found")
        if privacy_status not in ("private", "unlisted", "public"):
            raise ValueError("Invalid privacy status")

        key = idempotency_key or f"approval:{workflow_id}:{privacy_status}:{uuid.uuid4()}"
        existing = db.query(IdempotencyRecord).filter(IdempotencyRecord.key == key).first()
        if existing:
            approval = db.query(ApprovalRecord).filter(
                ApprovalRecord.id == existing.result_json.get("approval_id")
            ).first()
            if approval:
                return approval

        execution = db.query(WorkflowExecution).filter(WorkflowExecution.workflow_id == workflow_id).first()
        quality = next((t for t in execution.tasks if t.task_key == "quality_check"), None)
        if not quality or quality.status != "completed":
            raise ValueError("Quality check must pass before approval")

        project = db.query(Project).filter(Project.id == project_id).first()
        seo = (project.metadata_json or {}).get("seo", {}) if project else {}
        snapshot = {
            "title": title or seo.get("title", project.title if project else ""),
            "description": description or seo.get("description", ""),
            "privacy_status": privacy_status,
            "public_publish_confirmed": privacy_status == "public",
            "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
            "timezone": timezone_name,
        }
        approval = ApprovalRecord(
            project_id=project_id,
            workflow_id=workflow_id,
            user_id=user.id,
            approval_type="publish",
            approved=True,
            review_snapshot=snapshot,
        )
        db.add(approval)
        db.flush()

        if scheduled_at:
            if scheduled_at.tzinfo is None:
                raise ValueError("Scheduled publishing time must include timezone information")
            if scheduled_at <= datetime.now(timezone.utc):
                raise ValueError("Scheduled publishing time must be in the future")
            existing_schedule = db.query(ScheduledPublishing).filter(
                ScheduledPublishing.project_id == project_id,
                ScheduledPublishing.workflow_id == workflow_id,
            ).first()
            if existing_schedule:
                existing_schedule.scheduled_at = scheduled_at
                existing_schedule.timezone_name = timezone_name
                existing_schedule.privacy_status = privacy_status
                existing_schedule.status = "scheduled"
                existing_schedule.error_log = None
            else:
                db.add(ScheduledPublishing(
                    project_id=project_id,
                    workflow_id=workflow_id,
                    scheduled_at=scheduled_at,
                    timezone_name=timezone_name,
                    privacy_status=privacy_status,
                    status="scheduled",
                ))

        approval_task = next((t for t in execution.tasks if t.task_key == "approval"), None)
        upload_task = next((t for t in execution.tasks if t.task_key == "upload"), None)
        if approval_task:
            approval_task.status = "completed"
            approval_task.progress_percentage = 100
            approval_task.completed_at = datetime.now(timezone.utc)
        if upload_task:
            upload_task.status = "pending"
        db.add(IdempotencyRecord(key=key, operation="publish_approval", result_json={"approval_id": approval.id}))
        db.commit()
        db.refresh(approval)
        AutomationService.add_notification(
            db, user.id, project_id, workflow_id, "approval_granted",
            "Publishing approved", "The workflow was explicitly approved for publishing.",
        )
        return approval

    @staticmethod
    def retry_task(task_id: str, db: Session) -> WorkflowTask:
        task = db.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
        if not task:
            raise ValueError("Task not found")
        task.status = "pending"
        task.error_log = None
        task.progress_percentage = 0
        if task.job:
            task.job.status = "queued"
            task.job.cancelled = False
            task.job.error_log = None
            task.job.next_run_at = None
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def regenerate_task(task_id: str, db: Session) -> WorkflowTask:
        task = db.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
        if not task:
            raise ValueError("Task not found")
        if task.task_key in ("approval", "upload", "quality_check"):
            raise ValueError("Approval, upload, and quality-check tasks cannot be regenerated directly")
        task.status = "pending"
        task.completed_at = None
        task.error_log = None
        task.progress_percentage = 0
        task.output_json = {}
        if task.job:
            task.job.status = "queued"
            task.job.cancelled = False
            task.job.error_log = None
            task.job.next_run_at = None
            task.job.attempt_count = 0
        db.commit()
        db.refresh(task)
        return task

    @classmethod
    async def worker_loop(cls) -> None:
        logger.info("Persistent automation worker started")
        while True:
            db = SessionLocal()
            try:
                for execution in db.query(WorkflowExecution).filter(
                    WorkflowExecution.status.in_(["running", "queued"])
                ).all():
                    if execution.workflow.pause_requested or execution.workflow.cancel_requested:
                        continue
                    execution.status = "running"
                db.commit()

                cls._recover_interrupted(db)
                AutomationService.ensure_jobs(db)

                now = datetime.now(timezone.utc)
                job = db.query(JobQueue).filter(
                    JobQueue.status == "queued",
                    JobQueue.cancelled == False,
                ).order_by(JobQueue.priority.desc(), JobQueue.created_at.asc()).first()
                if job and job.next_run_at:
                    # SQLite may return naive datetimes
                    next_run = job.next_run_at
                    if next_run.tzinfo is None:
                        next_run = next_run.replace(tzinfo=timezone.utc)
                    if next_run > now:
                        job = None

                if job:
                    await cls._process_job(job, db)
            except Exception as exc:
                logger.exception("Automation worker loop error: %s", exc)
            finally:
                db.close()
            await asyncio.sleep(1)

    @staticmethod
    def _recover_interrupted(db: Session) -> None:
        interrupted = db.query(JobQueue).filter(JobQueue.status == "running").all()
        if interrupted:
            for job in interrupted:
                job.status = "queued"
                job.worker_id = None
                job.error_log = "Recovered as interrupted after backend restart"
                db.add(RecoveryLog(scope="job", scope_id=job.id,
                                   event="backend_restart_recovery",
                                   details="Running job reset to queued"))
            db.commit()

        stale_executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.status == "running"
        ).all()
        for execution in stale_executions:
            has_running_job = db.query(JobQueue).filter(
                JobQueue.task_id.in_([t.id for t in execution.tasks]),
                JobQueue.status == "running",
            ).first()
            if not has_running_job:
                continue

    @classmethod
    async def _process_job(cls, job: JobQueue, db: Session) -> None:
        task = db.query(WorkflowTask).filter(WorkflowTask.id == job.task_id).first()
        if not task:
            job.status = "failed"
            job.error_log = "Associated workflow task not found"
            db.commit()
            return
        execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == task.execution_id).first()
        workflow = db.query(Workflow).filter(Workflow.id == execution.workflow_id).first()
        if workflow.cancel_requested:
            job.status = "cancelled"
            job.cancelled = True
            db.commit()
            return
        if workflow.pause_requested:
            job.status = "queued"
            db.commit()
            return

        project = db.query(Project).filter(Project.id == workflow.project_id).first()
        job.status = "running"
        job.worker_id = cls._worker_id
        job.attempt_count += 1
        task.attempt_count = job.attempt_count
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        job.progress_percentage = 10
        attempt = JobAttempt(job_id=job.id, attempt_number=job.attempt_count,
                             status="running", started_at=datetime.now(timezone.utc))
        db.add(attempt)
        db.commit()

        try:
            task_timeouts = {
                "research": 60.0,
                "script": 90.0,
                "storyboard": 60.0,
                "voice": 180.0,
                "images": 180.0,
                "subtitles": 120.0,
                "video": 300.0,
                "editing": 60.0,
                "thumbnail": 60.0,
                "seo_metadata": 60.0,
                "quality_check": 30.0,
                "approval": 10.0,
                "upload": 600.0,
            }
            timeout_seconds = task_timeouts.get(task.task_key, 120.0)
            output = await asyncio.wait_for(
                HardwareTaskQueue.run_sequential(
                    f"{workflow.name}:{task.task_key}",
                    AutomationService.execute_task(task, workflow, project, db),
                ),
                timeout=timeout_seconds,
            )
            job.status = "completed"
            job.progress_percentage = 100
            job.error_log = None
            task.status = "completed"
            task.output_json = output
            task.progress_percentage = 100
            task.completed_at = datetime.now(timezone.utc)
            attempt.status = "completed"
            attempt.completed_at = datetime.now(timezone.utc)

            completed_count = sum(1 for t in execution.tasks if t.status == "completed")
            workflow.progress_percentage = int(completed_count / max(1, len(execution.tasks)) * 100)
            db.commit()
            AutomationService.add_notification(
                db, workflow.user_id, workflow.project_id, workflow.id,
                "task_completed", f"{task.name} completed",
                f"{task.name} completed successfully.", "success",
            )

            unfinished = [t for t in execution.tasks if t.status not in ("completed", "waiting_approval", "blocked", "cancelled")]
            if not unfinished and task.task_key == "upload":
                execution.status = "completed"
                execution.completed_at = datetime.now(timezone.utc)
                workflow.status = "completed"
                workflow.progress_percentage = 100
                db.commit()
                AutomationService.add_notification(
                    db, workflow.user_id, workflow.project_id, workflow.id,
                    "workflow_completed", "Workflow completed",
                    "All workflow tasks completed successfully.", "success",
                )
        except Exception as exc:
            logger.exception("Workflow task %s failed", task.task_key)
            attempt.status = "failed"
            attempt.error_log = str(exc)
            attempt.completed_at = datetime.now(timezone.utc)
            task.error_log = str(exc)
            task.status = "failed"
            job.error_log = str(exc)
            if job.attempt_count < job.max_attempts:
                delay = min(60, 2 ** (job.attempt_count - 1))
                job.status = "queued"
                job.next_run_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
                task.status = "failed"
                db.commit()
                AutomationService.add_notification(
                    db, workflow.user_id, workflow.project_id, workflow.id,
                    "task_retry", f"{task.name} retry scheduled",
                    f"{task.name} failed; retry {job.attempt_count + 1}/{job.max_attempts} in {delay}s.",
                    "warning",
                )
            else:
                job.status = "failed"
                execution.status = "failed"
                execution.error_log = str(exc)
                execution.completed_at = datetime.now(timezone.utc)
                workflow.status = "failed"
                db.commit()
                AutomationService.add_notification(
                    db, workflow.user_id, workflow.project_id, workflow.id,
                    "workflow_failed", "Workflow failed",
                    f"{task.name} failed after {job.attempt_count} attempts: {exc}",
                    "error",
                )

    @classmethod
    def start_worker(cls) -> None:
        if cls._worker_task is None or cls._worker_task.done():
            cls._worker_task = asyncio.create_task(cls.worker_loop())

    @classmethod
    async def stop_worker(cls) -> None:
        if cls._worker_task and not cls._worker_task.done():
            cls._worker_task.cancel()
            try:
                await cls._worker_task
            except asyncio.CancelledError:
                pass
