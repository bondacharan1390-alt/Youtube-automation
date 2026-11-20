from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_header():
    res = client.post("/api/v1/auth/dev-token")
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_generate_scene_image():
    headers = get_auth_header()

    # 1. Create a project to get a valid scene
    proj_res = client.post(
        "/api/v1/projects",
        json={
            "title": "Image Generation Test",
            "language": "en",
            "aspect_ratio": "16:9",
            "target_resolution": "1080p",
            "target_scene_count": 2,
        },
        headers=headers,
    )
    assert proj_res.status_code == 201
    scene_id = proj_res.json()["scenes"][0]["id"]

    # 2. Generate 16:9 image
    img_res = client.post(
        "/api/v1/images/generate",
        json={
            "scene_id": scene_id,
            "prompt": "Cinematic futuristic laboratory with glowing quantum processors, 16:9, 8k",
            "aspect_ratio": "16:9",
            "character_tokens": "Alex, young tech researcher",
            "seed": 1234,
        },
        headers=headers,
    )
    assert img_res.status_code == 200
    data = img_res.json()
    assert data["scene_id"] == scene_id
    assert data["aspect_ratio"] == "16:9"
    assert "image_url" in data
    assert data["image_url"].startswith("/storage/images/")
    assert data["file_size_bytes"] > 0

def test_regenerate_scene_image():
    headers = get_auth_header()

    proj_res = client.post(
        "/api/v1/projects",
        json={
            "title": "Regenerate Image Test",
            "language": "te",
            "aspect_ratio": "9:16",
            "target_resolution": "1080p",
            "target_scene_count": 1,
        },
        headers=headers,
    )
    scene_id = proj_res.json()["scenes"][0]["id"]

    regen_res = client.post(
        f"/api/v1/images/regenerate/{scene_id}",
        json={"custom_prompt": "Dramatic space nebula vortex, vertical 9:16"},
        headers=headers,
    )
    assert regen_res.status_code == 200
    data = regen_res.json()
    assert data["scene_id"] == scene_id
    assert data["file_size_bytes"] > 0
