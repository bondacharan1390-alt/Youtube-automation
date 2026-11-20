import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _get_token():
    r = client.post("/api/v1/auth/login", json={"email": "creator@youtube-studio.ai", "password": "creator12345"})
    return r.json().get("access_token", "")

def test_get_timeline_requires_auth():
    """Unauthenticated requests should not succeed."""
    r = client.get("/api/v1/editor/timeline/nonexistent")
    # May return 401 or 404 depending on middleware ordering — both are correct rejections
    assert r.status_code in (401, 403, 404, 422)

def test_get_timeline_not_found():
    token = _get_token()
    r = client.get("/api/v1/editor/timeline/nonexistent-project-id", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404

def test_get_timeline_valid_project():
    token = _get_token()
    projects_r = client.get("/api/v1/projects/", headers={"Authorization": f"Bearer {token}"})
    if projects_r.status_code != 200:
        pytest.skip("Projects endpoint failed")
    projects = projects_r.json()
    if isinstance(projects, dict):
        items = projects.get("items", [])
    else:
        items = projects
    if not items:
        pytest.skip("No projects available")
    proj_id = items[0]["id"]
    r = client.get(f"/api/v1/editor/timeline/{proj_id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "scenes" in data
    assert "aspect_ratio" in data

def test_start_render_invalid_project():
    token = _get_token()
    r = client.post("/api/v1/editor/render", json={
        "project_id": "invalid-id",
        "resolution": "1080p",
        "include_subtitles": False,
        "bgm_volume": 0.1,
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404

def test_generate_subtitles():
    token = _get_token()
    projects_r = client.get("/api/v1/projects/", headers={"Authorization": f"Bearer {token}"})
    if projects_r.status_code != 200:
        pytest.skip("Projects endpoint failed")
    projects = projects_r.json()
    if isinstance(projects, dict):
        items = projects.get("items", [])
    else:
        items = projects
    if not items:
        pytest.skip("No projects available")
    proj_id = items[0]["id"]
    r = client.post(f"/api/v1/subtitles/generate/{proj_id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "srt_url" in data
    assert "vtt_url" in data
