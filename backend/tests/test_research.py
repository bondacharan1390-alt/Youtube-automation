from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_header():
    res = client.post("/api/v1/auth/dev-token")
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_topic_analysis_english():
    headers = get_auth_header()
    req = {
        "topic": "Autonomous AI Agents in 2026",
        "language": "en"
    }
    res = client.post("/api/v1/research/analyze", json=req, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["topic"] == req["topic"]
    assert data["language"] == "en"
    assert data["virality_score"] >= 50
    assert len(data["hook_angles"]) >= 1
    assert len(data["primary_keywords"]) >= 1

def test_topic_analysis_telugu():
    headers = get_auth_header()
    req = {
        "topic": "జేమ్స్ వెబ్ టెలిస్కోప్ కొత్త ఆవిష్కరణలు",
        "language": "te"
    }
    res = client.post("/api/v1/research/analyze", json=req, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["language"] == "te"
    assert len(data["primary_keywords"]) >= 1

def test_generate_video_ideas():
    headers = get_auth_header()
    req = {
        "seed_keyword": "Quantum Computing",
        "language": "en"
    }
    res = client.post("/api/v1/research/ideas", json=req, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["seed_keyword"] == "Quantum Computing"
    assert len(data["ideas"]) >= 3
    assert all("title" in idea and "hook" in idea for idea in data["ideas"])
