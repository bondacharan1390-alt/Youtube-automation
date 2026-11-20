from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_header():
    res = client.post("/api/v1/auth/dev-token")
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_list_and_create_projects():
    headers = get_auth_header()
    
    # 1. List projects
    list_res = client.get("/api/v1/projects", headers=headers)
    assert list_res.status_code == 200
    initial_count = len(list_res.json())
    
    # 2. Create Long video project (16:9, English)
    new_proj = {
        "title": "Automated Test Project 16:9",
        "topic": "Testing automated generation pipeline",
        "language": "en",
        "aspect_ratio": "16:9",
        "target_resolution": "1080p",
        "target_scene_count": 3
    }
    create_res = client.post("/api/v1/projects", json=new_proj, headers=headers)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["title"] == new_proj["title"]
    assert len(created["scenes"]) == 3
    
    # 3. Create Shorts project (9:16, Telugu)
    new_short = {
        "title": "తెలుగు షార్ట్ ప్రాజెక్ట్ (Telugu Short)",
        "topic": "తెలుగు AI సాంకేతికత",
        "language": "te",
        "aspect_ratio": "9:16",
        "target_resolution": "1080p",
        "target_scene_count": 4
    }
    short_res = client.post("/api/v1/projects", json=new_short, headers=headers)
    assert short_res.status_code == 201
    created_short = short_res.json()
    assert created_short["language"] == "te"
    assert created_short["aspect_ratio"] == "9:16"
    assert len(created_short["scenes"]) == 4

    # 4. Filter by language=te
    filtered_res = client.get("/api/v1/projects?language=te", headers=headers)
    assert filtered_res.status_code == 200
    assert all(p["language"] == "te" for p in filtered_res.json())

    # 5. Delete project
    del_res = client.delete(f"/api/v1/projects/{created['id']}", headers=headers)
    assert del_res.status_code == 204
