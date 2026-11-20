from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_header():
    res = client.post("/api/v1/auth/dev-token")
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_generate_longform_script_english():
    headers = get_auth_header()
    req = {
        "title": "The Rise of Microchips",
        "topic": "Evolution of semiconductors",
        "language": "en",
        "aspect_ratio": "16:9",
        "target_scene_count": 5,
        "tone": "cinematic"
    }
    res = client.post("/api/v1/scripts/generate", json=req, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == req["title"]
    assert data["aspect_ratio"] == "16:9"
    assert len(data["scenes"]) >= 3
    assert all("visual_prompt" in s and "narration_text" in s for s in data["scenes"])

def test_generate_shorts_script_telugu():
    headers = get_auth_header()
    req = {
        "title": "అద్భుతమైన స్పేస్ ఫ్యాక్ట్",
        "topic": "నల్ల రంధ్రం రహస్యం",
        "language": "te",
        "aspect_ratio": "9:16",
        "target_scene_count": 3,
        "tone": "urgent"
    }
    res = client.post("/api/v1/scripts/generate", json=req, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["language"] == "te"
    assert data["aspect_ratio"] == "9:16"
    assert len(data["scenes"]) >= 2

def test_generate_story_and_characters():
    headers = get_auth_header()
    req = {
        "premise": "Two engineers test an autonomous robot that starts speaking Telugu",
        "language": "te",
        "character_count": 2,
        "tone": "dramatic"
    }
    res = client.post("/api/v1/scripts/story", json=req, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["characters"]) >= 1
    assert len(data["dialogue_scenes"]) >= 1
    assert all("speaker" in d and "line" in d for d in data["dialogue_scenes"])

def test_save_and_export_storyboard():
    headers = get_auth_header()
    
    # 1. Create a base project
    proj_res = client.post(
        "/api/v1/projects",
        json={
            "title": "Storyboard Export Test",
            "topic": "Testing storyboard persistence",
            "language": "en",
            "aspect_ratio": "16:9",
            "target_resolution": "1080p",
            "target_scene_count": 3
        },
        headers=headers
    )
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    # 2. Save custom scenes to project
    scenes = [
        {
            "scene_order": 1,
            "script_text": "Opening Scene",
            "narration_text": "Welcome to the future.",
            "visual_prompt": "Futuristic neon city 16:9",
            "duration_seconds": 6.0
        },
        {
            "scene_order": 2,
            "script_text": "Climax Scene",
            "narration_text": "Everything accelerated.",
            "visual_prompt": "Processor glow in dark",
            "duration_seconds": 7.5
        }
    ]
    save_res = client.post(f"/api/v1/scripts/{proj_id}/save", json=scenes, headers=headers)
    assert save_res.status_code == 200
    saved_data = save_res.json()
    assert saved_data["total_scenes"] == 2
    assert saved_data["total_duration_seconds"] == 13.5

    # 3. Export storyboard
    export_res = client.get(f"/api/v1/scripts/{proj_id}/export", headers=headers)
    assert export_res.status_code == 200
    export_data = export_res.json()
    assert export_data["project_id"] == proj_id
    assert len(export_data["scenes"]) == 2
