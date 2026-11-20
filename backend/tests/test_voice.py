from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_header():
    res = client.post("/api/v1/auth/dev-token")
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_list_voices():
    # 1. All voices
    res = client.get("/api/v1/voice/voices")
    assert res.status_code == 200
    voices = res.json()
    assert len(voices) >= 5

    # 2. Filter by Telugu
    te_res = client.get("/api/v1/voice/voices?language=te")
    assert te_res.status_code == 200
    te_voices = te_res.json()
    assert len(te_voices) >= 2
    assert any(v["id"] == "te-IN-MohanNeural" for v in te_voices)
    assert any(v["id"] == "te-IN-ShrutiNeural" for v in te_voices)

    # 3. Filter by English male
    en_m_res = client.get("/api/v1/voice/voices?language=en&gender=male")
    assert en_m_res.status_code == 200
    assert all(v["gender"] == "male" and v["language"] == "en" for v in en_m_res.json())

def test_synthesize_scene_voice():
    headers = get_auth_header()

    # 1. Create a project to get a valid scene
    proj_res = client.post(
        "/api/v1/projects",
        json={
            "title": "Voice Synthesis Test",
            "language": "te",
            "aspect_ratio": "16:9",
            "target_resolution": "1080p",
            "target_scene_count": 2,
        },
        headers=headers,
    )
    assert proj_res.status_code == 201
    scene_id = proj_res.json()["scenes"][0]["id"]

    # 2. Synthesize Telugu voice
    syn_res = client.post(
        "/api/v1/voice/synthesize",
        json={
            "scene_id": scene_id,
            "text": "నమస్కారం, ఇది వాయిస్ టెస్ట్ ఆడియో.",
            "voice_id": "te-IN-MohanNeural",
            "speed": 1.1,
            "pitch": 0.0,
            "output_format": "mp3",
        },
        headers=headers,
    )
    assert syn_res.status_code == 200
    data = syn_res.json()
    assert data["scene_id"] == scene_id
    assert "audio_url" in data
    assert data["file_size_bytes"] > 0
    assert data["audio_url"].startswith("/storage/audio/")

def test_synthesize_all_scenes():
    headers = get_auth_header()

    # Create project with 2 scenes
    proj_res = client.post(
        "/api/v1/projects",
        json={
            "title": "Batch Voice Test",
            "language": "en",
            "aspect_ratio": "16:9",
            "target_resolution": "1080p",
            "target_scene_count": 2,
        },
        headers=headers,
    )
    proj_id = proj_res.json()["id"]

    # Synthesize all
    batch_res = client.post(
        f"/api/v1/voice/synthesize-all/{proj_id}",
        json={"voice_id": "en-US-ChristopherNeural", "speed": 1.0, "pitch": 0.0},
        headers=headers,
    )
    assert batch_res.status_code == 200
    results = batch_res.json()
    assert len(results) == 2
    assert all(r["file_size_bytes"] > 0 for r in results)
