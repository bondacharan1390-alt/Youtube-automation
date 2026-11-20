import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.project import PublishJob, Project
from app.models.user import User

client = TestClient(app)


def _get_token():
    r = client.post("/api/v1/auth/login", json={"email": "creator@youtube-studio.ai", "password": "creator12345"})
    return r.json().get("access_token", "")


def test_retry_deduplication():
    """Verify that retrying an already uploaded job returns the existing job without creating duplicates."""
    token = _get_token()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "creator@youtube-studio.ai").first()
        proj = db.query(Project).filter(Project.user_id == user.id).first()
        assert proj is not None

        # Ensure a completed publish job exists
        job = db.query(PublishJob).filter(PublishJob.project_id == proj.id, PublishJob.upload_status == "uploaded").first()
        if not job:
            job = PublishJob(
                project_id=proj.id,
                title="Test Deduplication",
                privacy_status="private",
                upload_status="uploaded",
                youtube_video_id="sim_dedup_test_123",
                manual_approval_granted=True,
            )
            db.add(job)
            db.commit()
            db.refresh(job)

        job_id = job.id
    finally:
        db.close()

    r = client.post(f"/api/v1/youtube/retry/{job_id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["job_id"] == job_id
    assert data["upload_status"] == "uploaded"
    assert data["youtube_video_id"] == "sim_dedup_test_123"


def test_retry_bounded_limit():
    """Verify that retries are bounded to max 3 attempts."""
    token = _get_token()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "creator@youtube-studio.ai").first()
        proj = db.query(Project).filter(Project.user_id == user.id).first()
        job = PublishJob(
            project_id=proj.id,
            title="Max Retry Test",
            privacy_status="private",
            upload_status="failed",
            retry_count=3,  # Already at max limit
            manual_approval_granted=True,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id
    finally:
        db.close()

    r = client.post(f"/api/v1/youtube/retry/{job_id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400
    assert "Maximum retry limit" in r.json()["detail"]


def test_thumbnail_attachment_api():
    """Verify thumbnail attachment endpoint attaches thumbnail cleanly."""
    token = _get_token()
    proj_r = client.get("/api/v1/projects/", headers={"Authorization": f"Bearer {token}"})
    projects = proj_r.json()
    if not projects:
        pytest.skip("No projects available")

    # Create dummy thumbnail file if needed
    storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../storage/thumbnails"))
    os.makedirs(storage_dir, exist_ok=True)
    thumb_path = os.path.join(storage_dir, f"{projects[0]['id']}.png")
    if not os.path.exists(thumb_path):
        with open(thumb_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

    r = client.post(
        "/api/v1/youtube/thumbnails/attach",
        json={
            "video_id": "sim_sample_vid_999",
            "project_id": projects[0]["id"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True


def test_thumbnail_file_size_limit():
    """Verify thumbnails exceeding 2MB are rejected."""
    token = _get_token()
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        # Write 2.5 MB dummy file
        f.write(b"0" * int(2.5 * 1024 * 1024))
        oversized_path = f.name

    try:
        r = client.post(
            "/api/v1/youtube/thumbnails/attach",
            json={
                "video_id": "sim_sample_vid_999",
                "thumbnail_path": oversized_path,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 400
        assert "exceeds YouTube 2MB limit" in r.json()["detail"]
    finally:
        if os.path.exists(oversized_path):
            os.remove(oversized_path)
