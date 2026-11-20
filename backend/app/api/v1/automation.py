import os
import hmac
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_db
from app.models.automation import (
    ApprovalRecord,
    Notification,
    ScheduledPublishing,
    Workflow,
    WorkflowExecution,
)
from app.models.project import Project
from app.models.user import User
from app.services.automation_service import AutomationService

router = APIRouter(prefix="/automation", tags=["Automation Engine"])


class CreateWorkflowRequest(BaseModel):
    project_id: str
    settings: Dict[str, Any] = Field(default_factory=dict)
    idempotency_key: Optional[str] = None


class ApprovalRequest(BaseModel):
    privacy_status: str = "private"
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    timezone_name: str = "UTC"
    idempotency_key: Optional[str] = None


class N8nWebhookRequest(BaseModel):
    project_id: str
    settings: Dict[str, Any] = Field(default_factory=dict)
    idempotency_key: Optional[str] = None


@router.post("/n8n/webhook")
def n8n_workflow_webhook(
    req: N8nWebhookRequest,
    x_n8n_secret: Optional[str] = Header(default=None, alias="X-N8n-Secret"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enabled = os.getenv("N8N_ENABLED", "false").lower() in ("1", "true", "yes")
    expected = os.getenv("N8N_WEBHOOK_SECRET", "")
    if not enabled:
        raise HTTPException(status_code=404, detail="n8n integration is disabled")
    if not expected or not x_n8n_secret or not hmac.compare_digest(x_n8n_secret, expected):
        raise HTTPException(status_code=401, detail="Invalid n8n webhook secret")
    project = db.query(Project).filter(Project.id == req.project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    workflow = AutomationService.create_workflow(project, current_user.id, req.settings, db, req.idempotency_key)
    AutomationService.start_workflow(workflow.id, db)
    return {"workflow_id": workflow.id, "status": "started", "n8n": "accepted"}


@router.post("/workflows")
def create_workflow(
    req: CreateWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == req.project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    workflow = AutomationService.create_workflow(project, current_user.id, req.settings, db, req.idempotency_key)
    return workflow_status(workflow.id, db, current_user)


@router.post("/workflows/{workflow_id}/start")
def start_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user.id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    try:
        AutomationService.start_workflow(workflow_id, db)
        return workflow_status(workflow_id, db, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/workflows")
def list_workflows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workflows = db.query(Workflow).filter(Workflow.user_id == current_user.id).order_by(Workflow.created_at.desc()).all()
    return [workflow_status(w.id, db, current_user) for w in workflows]


@router.get("/workflows/{workflow_id}")
def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return workflow_status(workflow_id, db, current_user)


def workflow_status(workflow_id: str, db: Session, current_user: User) -> Dict[str, Any]:
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user.id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.workflow_id == workflow_id).order_by(
        WorkflowExecution.created_at.desc()
    ).first()
    tasks = []
    if execution:
        for task in sorted(execution.tasks, key=lambda t: t.position):
            job = task.job
            tasks.append({
                "id": task.id,
                "task_key": task.task_key,
                "task_key": task.task_key,
                "name": task.name,
                "status": task.status,
                "position": task.position,
                "depends_on": task.depends_on,
                "progress_percentage": task.progress_percentage,
                "output": task.output_json,
                "error": task.error_log,
                "attempt_count": task.attempt_count,
                "job_status": job.status if job else None,
                "job_attempt_count": job.attempt_count if job else 0,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            })
    return {
        "id": workflow.id,
        "project_id": workflow.project_id,
        "name": workflow.name,
        "status": workflow.status,
        "progress_percentage": workflow.progress_percentage,
        "pause_requested": workflow.pause_requested,
        "cancel_requested": workflow.cancel_requested,
        "execution_id": execution.id if execution else None,
        "execution_status": execution.status if execution else None,
        "tasks": tasks,
        "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
        "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
    }


@router.post("/workflows/{workflow_id}/pause")
def pause_workflow(workflow_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user.id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow_status(AutomationService.pause_workflow(workflow_id, db).id, db, current_user)


@router.post("/workflows/{workflow_id}/resume")
def resume_workflow(workflow_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user.id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow_status(AutomationService.resume_workflow(workflow_id, db).id, db, current_user)


@router.post("/workflows/{workflow_id}/cancel")
def cancel_workflow(workflow_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user.id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow_status(AutomationService.cancel_workflow(workflow_id, db).id, db, current_user)


@router.post("/tasks/{task_id}/retry")
def retry_task(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.automation import WorkflowTask
    task = db.query(WorkflowTask).join(WorkflowTask.execution).join(WorkflowExecution).join(Workflow).filter(
        WorkflowTask.id == task_id,
        Workflow.user_id == current_user.id,
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        result = AutomationService.retry_task(task_id, db)
        return {"id": result.id, "status": result.status}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/tasks/{task_id}/regenerate")
def regenerate_task(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.automation import WorkflowTask, WorkflowExecution
    task = db.query(WorkflowTask).join(WorkflowExecution).join(Workflow).filter(
        WorkflowTask.id == task_id,
        Workflow.user_id == current_user.id,
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        result = AutomationService.regenerate_task(task_id, db)
        return {"id": result.id, "status": result.status}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/workflows/{workflow_id}/approve")
def approve_workflow(
    workflow_id: str,
    req: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user.id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    try:
        approval = AutomationService.approve_workflow(
            workflow_id=workflow_id,
            project_id=workflow.project_id,
            user=current_user,
            db=db,
            privacy_status=req.privacy_status,
            title=req.title,
            description=req.description,
            scheduled_at=req.scheduled_at,
            timezone_name=req.timezone_name,
            idempotency_key=req.idempotency_key,
        )
        return {
            "id": approval.id,
            "approved": approval.approved,
            "review_snapshot": approval.review_snapshot,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/workflows/{workflow_id}/history")
def workflow_history(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user.id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.workflow_id == workflow_id).first()
    tasks = execution.tasks if execution else []
    return [{
        "task_id": task.id,
        "task_key": task.task_key,
        "status": task.status,
        "attempt_count": task.attempt_count,
        "error": task.error_log,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "output": task.output_json,
    } for task in sorted(tasks, key=lambda t: t.position)]


@router.get("/notifications")
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(100).all()
    return [{
        "id": n.id,
        "type": n.notification_type,
        "title": n.title,
        "message": n.message,
        "level": n.level,
        "read": n.read,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    } for n in items]
