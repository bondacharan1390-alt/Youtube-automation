from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_header():
    res = client.post("/api/v1/auth/dev-token")
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_providers_workflow():
    headers = get_auth_header()
    
    # 1. List providers
    res = client.get("/api/v1/providers", headers=headers)
    assert res.status_code == 200
    providers = res.json()
    assert len(providers) >= 5
    
    provider_keys = [p["provider_key"] for p in providers]
    assert "ollama" in provider_keys
    assert "kokoro" in provider_keys
    assert "edge_tts" in provider_keys
    assert "faster_whisper" in provider_keys
    assert "comfyui" in provider_keys

    # 2. Update provider configuration
    update_res = client.put(
        "/api/v1/providers/ollama",
        json={"base_url": "http://127.0.0.1:11434", "is_active": True},
        headers=headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["base_url"] == "http://127.0.0.1:11434"

    # 3. Check health of Kokoro TTS & Edge-TTS
    health_res = client.post("/api/v1/providers/kokoro/check-health", headers=headers)
    assert health_res.status_code == 200
    assert health_res.json()["is_healthy"] is True

    edge_health_res = client.post("/api/v1/providers/edge_tts/check-health", headers=headers)
    assert edge_health_res.status_code == 200
    assert edge_health_res.json()["is_healthy"] is True

def test_dashboard_stats():
    headers = get_auth_header()
    res = client.get("/api/v1/stats", headers=headers)
    assert res.status_code == 200
    stats = res.json()
    assert "total_projects" in stats
    assert "system_memory_total_gb" in stats
    assert stats["youtube_quota_limit"] == 10000
