import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _get_token():
    r = client.post("/api/v1/auth/login", json={"email": "creator@youtube-studio.ai", "password": "creator12345"})
    return r.json().get("access_token", "")


def test_list_playlists_api():
    token = _get_token()
    r = client.get("/api/v1/youtube/playlists", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    # At least default seeded playlist exists
    assert len(data) >= 1
    assert "youtube_playlist_id" in data[0]
    assert "title" in data[0]


def test_create_playlist_api():
    token = _get_token()
    r = client.post(
        "/api/v1/youtube/playlists",
        json={
            "title": "Quantum Robotics 2026",
            "description": "Curated videos on quantum robotics and intelligence.",
            "privacy_status": "private",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Quantum Robotics 2026"
    assert data["privacy_status"] == "private"
    assert data["youtube_playlist_id"].startswith("PL_")


def test_add_video_to_playlist_api():
    token = _get_token()
    # List playlists to get an ID
    list_r = client.get("/api/v1/youtube/playlists", headers={"Authorization": f"Bearer {token}"})
    playlists = list_r.json()
    assert len(playlists) > 0
    pl_id = playlists[0]["youtube_playlist_id"]

    r = client.post(
        "/api/v1/youtube/playlists/add-video",
        json={
            "playlist_id": pl_id,
            "video_id": "sim_test_vid_12345",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "item_id" in data
