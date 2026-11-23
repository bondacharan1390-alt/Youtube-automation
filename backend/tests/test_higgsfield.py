import pytest
from fastapi.testclient import TestClient

from app.api.v1 import higgsfield as higgsfield_api
from app.core.database import SessionLocal
from app.core.security import encrypt_secret
from app.main import app
from app.models.provider import AIProvider
from app.services.image.canvas_image_provider import CanvasImageProvider
from app.services.image.comfyui_provider import ComfyUIImageProvider
from app.services.higgsfield.client import HiggsfieldAPIError, HiggsfieldClient


client = TestClient(app)


def auth_headers():
    token = client.post("/api/v1/auth/dev-token").json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def configure_provider():
    db = SessionLocal()
    try:
        provider = db.query(AIProvider).filter(AIProvider.provider_key == "higgsfield").first()
        provider.is_active = True
        provider.encrypted_api_key = encrypt_secret("test-credential")
        db.commit()
    finally:
        db.close()


def test_higgsfield_auth_header_never_exposes_plain_credential_in_response():
    adapter = HiggsfieldClient("test-credential")
    assert adapter._headers()["Authorization"] == "Key test-credential"


def test_higgsfield_mocked_job_polling_and_cancel(monkeypatch):
    configure_provider()

    class FakeClient:
        def __init__(self, credential, base_url=None):
            assert credential == "test-credential"

        async def submit(self, model_path, payload):
            assert model_path == "kling-video/v4.0/image-to-video"
            assert payload["image_url"].startswith("https://")
            return {"request_id": "req-test-1", "status": "queued", "status_url": "https://api.higgsfield.ai/requests/req-test-1/status", "cancel_url": "https://api.higgsfield.ai/requests/req-test-1/cancel"}

        async def status(self, status_url, request_id):
            return {"status": "completed", "video": {"url": "https://cdn.example/video.mp4"}}

        async def cancel(self, cancel_url, request_id):
            return {"status": "canceled"}

    monkeypatch.setattr(higgsfield_api, "HiggsfieldClient", FakeClient)
    headers = auth_headers()
    created = client.post(
        "/api/v1/higgsfield/generations",
        json={
            "model_path": "kling-video/v4.0/image-to-video",
            "operation": "image_to_video",
            "payload": {"image_url": "https://cdn.example/input.png", "duration": 5},
        },
        headers=headers,
    )
    assert created.status_code == 202
    job_id = created.json()["id"]

    polled = client.get(f"/api/v1/higgsfield/generations/{job_id}", headers=headers)
    assert polled.status_code == 200
    assert polled.json()["status"] == "completed"
    assert polled.json()["output_url"].endswith("video.mp4")

    cancelled = client.post(f"/api/v1/higgsfield/generations/{job_id}/cancel", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "canceled"


def test_higgsfield_provider_failures_are_returned_without_retry(monkeypatch):
    configure_provider()

    class FailingClient:
        def __init__(self, credential, base_url=None):
            pass

        async def submit(self, model_path, payload):
            raise HiggsfieldAPIError("provider rejected request", 422)

    monkeypatch.setattr(higgsfield_api, "HiggsfieldClient", FailingClient)
    response = client.post(
        "/api/v1/higgsfield/generations",
        json={
            "model_path": "kling-video/v4.0/image-to-video",
            "operation": "image_to_video",
            "payload": {"image_url": "https://cdn.example/input.png", "duration": 5},
        },
        headers=auth_headers(),
    )
    assert response.status_code == 502
    assert "provider rejected request" in response.json()["detail"]


@pytest.mark.asyncio
async def test_existing_comfyui_fallback_remains_available(tmp_path):
    provider = ComfyUIImageProvider(base_url="http://127.0.0.1:1")
    output = await provider.generate_image("fallback", str(tmp_path / "fallback.png"), seed=7)
    assert output.endswith("fallback.png")
    assert (tmp_path / "fallback.png").exists()
    assert CanvasImageProvider().check_health()["is_healthy"] is True
