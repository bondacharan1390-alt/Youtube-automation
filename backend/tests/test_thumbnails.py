import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.thumbnail.thumbnail_service import ThumbnailService

client = TestClient(app)

def _get_token():
    r = client.post("/api/v1/auth/login", json={"email": "creator@youtube-studio.ai", "password": "creator12345"})
    return r.json().get("access_token", "")


def test_thumbnail_service_landscape_1280x720():
    res = ThumbnailService.generate_thumbnail(
        project_id="test_proj_landscape",
        headline="5 Mind-Blowing AI Breakthroughs",
        subtitle="The Future is Here",
        badge_text="2026 AI",
        theme_name="viral_punch",
        aspect_ratio="16:9",
    )
    assert res["width"] == 1280
    assert res["height"] == 720
    assert os.path.exists(res["file_path"])
    assert res["file_size_bytes"] > 10000


def test_thumbnail_service_portrait_shorts_720x1280_telugu():
    res = ThumbnailService.generate_thumbnail(
        project_id="test_proj_telugu",
        headline="అద్భుతమైన అంతరిక్ష రహస్యాలు",
        subtitle="జేమ్స్ వెబ్ టెలిస్కోప్",
        badge_text="రహస్యం",
        theme_name="cinematic_dark",
        aspect_ratio="9:16",
    )
    assert res["width"] == 720
    assert res["height"] == 1280
    assert os.path.exists(res["file_path"])
    assert res["file_size_bytes"] > 10000


def test_thumbnail_api_themes():
    token = _get_token()
    r = client.get("/api/v1/thumbnails/themes", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    themes = r.json()
    assert len(themes) >= 4
    ids = [t["id"] for t in themes]
    assert "viral_punch" in ids
    assert "cinematic_dark" in ids


def test_thumbnail_api_generate_and_get():
    token = _get_token()
    projects_r = client.get("/api/v1/projects/", headers={"Authorization": f"Bearer {token}"})
    projects = projects_r.json()
    if not projects:
        pytest.skip("No projects available")
    proj_id = projects[0]["id"]

    gen_r = client.post("/api/v1/thumbnails/generate", json={
        "project_id": proj_id,
        "headline": "Testing AI Studio Video Title",
        "subtitle": "Exclusive Preview",
        "badge_text": "HOT",
        "theme_name": "tech_minimal",
    }, headers={"Authorization": f"Bearer {token}"})
    assert gen_r.status_code == 200
    data = gen_r.json()
    assert data["width"] == 1280
    assert data["height"] == 720
    assert "thumbnail_url" in data

    get_r = client.get(f"/api/v1/thumbnails/{proj_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_r.status_code == 200
    assert get_r.json()["project_id"] == proj_id
