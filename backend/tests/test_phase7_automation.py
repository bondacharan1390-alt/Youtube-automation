from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal
from app.main import app
from app.models.project import Project
from app.models.automation import WorkflowExecution
from app.models.automation import JobQueue
from app.models.project import PublishJob
from app.services.automation_service import AutomationService
from fastapi.testclient import TestClient


client = TestClient(app)


def auth_headers():
    response = client.post("/api/v1/auth/dev-token")
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_phase7_workflow_creation_duplicate_and_pause_resume():
    headers = auth_headers()
    project = client.post("/api/v1/projects", headers=headers, json={
        "title": "Phase 7 Integration Test",
        "topic": "Persistent automation",
        "language": "en",
        "aspect_ratio": "16:9",
        "target_resolution": "720p",
        "target_scene_count": 3,
    })
    assert project.status_code == 201
    project_id = project.json()["id"]

    created = client.post("/api/v1/automation/workflows", headers=headers, json={
        "project_id": project_id,
        "settings": {"target_scene_count": 3},
        "idempotency_key": "phase7-test-create",
    })
    assert created.status_code == 200
    workflow_id = created.json()["id"]

    duplicate = client.post("/api/v1/automation/workflows", headers=headers, json={
        "project_id": project_id,
        "settings": {"target_scene_count": 3},
        "idempotency_key": "phase7-test-create",
    })
    assert duplicate.status_code == 200
    assert duplicate.json()["id"] == workflow_id

    started = client.post(f"/api/v1/automation/workflows/{workflow_id}/start", headers=headers)
    assert started.status_code == 200

    paused = client.post(f"/api/v1/automation/workflows/{workflow_id}/pause", headers=headers)
    assert paused.status_code == 200
    assert paused.json()["status"] == "paused"

    resumed = client.post(f"/api/v1/automation/workflows/{workflow_id}/resume", headers=headers)
    assert resumed.status_code == 200
    assert resumed.json()["status"] in ("running", "queued")


def test_phase7_private_default_and_quality_gate():
    db = SessionLocal()
    user = __import__("app.models.user", fromlist=["User"]).User
    current_user = db.query(user).first()
    project = Project(
        user_id=current_user.id,
        title="Approval Safety Test",
        topic="Publishing safeguards",
        language="en",
        aspect_ratio="16:9",
        target_resolution="1080p",
        target_scene_count=2,
        status="draft",
        metadata_json={},
    )
    db.add(project)
    db.flush()
    workflow = AutomationService.create_workflow(project, current_user.id, {}, db)
    db.commit()

    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.workflow_id == workflow.id
    ).first()
    try:
        try:
            AutomationService.approve_workflow(
                workflow.id,
                project.id,
                current_user,
                db,
                privacy_status="public",
            )
            assert False, "Public approval must be blocked before quality completion"
        except ValueError:
            pass

        quality = next(t for t in execution.tasks if t.task_key == "quality_check")
        quality.status = "completed"
        quality.output_json = {"passed": True}
        quality.progress_percentage = 100
        db.commit()

        approval = AutomationService.approve_workflow(
            workflow.id,
            project.id,
            current_user,
            db,
            privacy_status="private",
            timezone_name="UTC",
        )
        assert approval.approved is True
        assert approval.review_snapshot["privacy_status"] == "private"
        assert approval.review_snapshot["public_publish_confirmed"] is False

        scheduled = datetime.now(timezone.utc) + timedelta(hours=2)
        scheduled_approval = AutomationService.approve_workflow(
            workflow.id,
            project.id,
            current_user,
            db,
            privacy_status="private",
            scheduled_at=scheduled,
            timezone_name="UTC",
            idempotency_key="phase7-scheduled-test",
        )
        assert scheduled_approval.review_snapshot["scheduled_at"] is not None
    finally:
        db.close()


def test_phase7_n8n_disabled_by_default():
    headers = auth_headers()
    response = client.post(
        "/api/v1/automation/n8n/webhook",
        headers=headers,
        json={"project_id": "missing", "settings": {}},
    )
    assert response.status_code in (404, 401)


def test_phase7_backend_restart_recovers_running_job():
    db = SessionLocal()
    current_user = db.query(__import__("app.models.user", fromlist=["User"]).User).first()
    project = Project(
        user_id=current_user.id,
        title="Restart Recovery Test",
        topic="Persistent queue recovery",
        language="en",
        aspect_ratio="16:9",
        target_resolution="720p",
        target_scene_count=2,
        status="draft",
        metadata_json={},
    )
    db.add(project)
    db.flush()
    workflow = AutomationService.create_workflow(project, current_user.id, {}, db)
    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.workflow_id == workflow.id
    ).first()
    execution.status = "running"
    db.commit()
    AutomationService.ensure_jobs(db)

    task_ids = [task.id for task in execution.tasks]
    job = db.query(JobQueue).filter(JobQueue.task_id.in_(task_ids)).first()
    if job:
        job.status = "running"
        job.worker_id = "crashed-worker"
        db.commit()
        AutomationService._recover_interrupted(db)
        db.refresh(job)
        assert job.status == "queued"
        assert job.worker_id is None
    db.close()


def test_phase7_duplicate_job_retry_cancel_and_upload_safeguards():
    db = SessionLocal()
    user_model = __import__("app.models.user", fromlist=["User"]).User
    current_user = db.query(user_model).first()

    project = Project(
        user_id=current_user.id,
        title="Queue Control Test",
        topic="Persistent queue controls",
        language="en",
        aspect_ratio="16:9",
        target_resolution="720p",
        target_scene_count=2,
        status="draft",
        metadata_json={},
    )
    db.add(project)
    db.flush()
    workflow = AutomationService.create_workflow(project, current_user.id, {}, db)
    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.workflow_id == workflow.id
    ).first()
    execution.status = "running"
    db.commit()

    first_count = AutomationService.ensure_jobs(db)
    second_count = AutomationService.ensure_jobs(db)
    assert first_count >= 1
    assert second_count == 0

    task_ids = [task.id for task in execution.tasks]
    jobs = db.query(JobQueue).filter(JobQueue.task_id.in_(task_ids)).all()
    assert len(jobs) == 1
    assert len({job.idempotency_key for job in jobs}) == 1

    task = next(t for t in execution.tasks if t.task_key == "research")
    task.status = "failed"
    task.error_log = "test failure"
    db.commit()
    retried = AutomationService.retry_task(task.id, db)
    assert retried.status == "pending"

    cancelled = AutomationService.cancel_workflow(workflow.id, db)
    assert cancelled.status == "cancelled"
    assert cancelled.cancel_requested is True

    existing_publish = PublishJob(
        project_id=project.id,
        title="Already uploaded",
        privacy_status="private",
        manual_approval_granted=True,
        upload_status="uploaded",
        youtube_video_id="already-uploaded-id",
    )
    db.add(existing_publish)
    db.commit()

    from app.services.youtube.youtube_service import YouTubeService
    try:
        YouTubeService.upload_video(
            project_id=project.id,
            user=current_user,
            title="Duplicate attempt",
            description="Must be blocked",
            tags=[],
            privacy_status="private",
            scheduled_publish_time=None,
            manual_approval_granted=False,
            db=db,
        )
        assert False, "Duplicate upload must be blocked"
    except ValueError as exc:
        assert "already" in str(exc).lower() or "upload" in str(exc).lower()
    finally:
        db.close()
