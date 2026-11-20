import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_dev_token():
    response = client.post("/api/v1/auth/dev-token")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "creator@youtube-studio.ai"

def test_register_and_login():
    unique_id = uuid.uuid4().hex[:8]
    email = f"test_user_{unique_id}@example.com"
    reg_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": "securepassword123"}
    )
    assert reg_response.status_code == 200
    reg_data = reg_response.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == email

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "securepassword123"}
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
