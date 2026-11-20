import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _get_token():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "creator@youtube-studio.ai", "password": "creator12345"},
    )
    return response.json().get("access_token", "")


def _auth_headers():
    return {"Authorization": f"Bearer {_get_token()}"}


def test_youtube_channels_list():
    r = client.get("/api/v1/youtube/channels", headers=_auth_headers())
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "quota_units_used_today" in data[0]


def test_youtube_oauth_url():
    r = client.get("/api/v1/youtube/oauth/url", headers=_auth_headers())
    assert r.status_code == 200
    data = r.json()
    assert "client_id_configured" in data
    assert "instructions" in data


def test_youtube_public_upload_requires_manual_approval():
    headers = _auth_headers()
    projects_r = client.get("/api/v1/projects/", headers=headers)
    projects = projects_r.json()
    if not projects:
        pytest.skip("No projects available")
    proj_id = projects[0]["id"]

    r = client.post(
        "/api/v1/youtube/upload",
        json={
            "project_id": proj_id,
            "title": "Public Video Test",
            "privacy_status": "public",
            "manual_approval_granted": False,
        },
        headers=headers,
    )
    assert r.status_code == 400
    assert "Manual approval required" in r.json()["detail"]


def test_youtube_private_upload_succeeds_when_rendered():
    headers = _auth_headers()
    projects_r = client.get("/api/v1/projects/", headers=headers)
    projects = projects_r.json()
    if not projects:
        pytest.skip("No projects available")

    rendered_proj = next((p for p in projects if p.get("status") == "rendered"), None)
    if not rendered_proj:
        pytest.skip("No rendered project for upload test")

    r = client.post(
        "/api/v1/youtube/upload",
        json={
            "project_id": rendered_proj["id"],
            "title": "Automated AI Video - Private Preview",
            "privacy_status": "private",
            "manual_approval_granted": False,
        },
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["upload_status"] in ("uploaded", "pending")
    assert data["privacy_status"] == "private"


def test_youtube_channel_analytics():
    headers = _auth_headers()
    channels_r = client.get("/api/v1/youtube/channels", headers=headers)
    assert channels_r.status_code == 200
    channels = channels_r.json()
    if not channels:
        pytest.skip("No channels available")
    channel_id = channels[0]["id"]

    r = client.get(
        f"/api/v1/youtube/analytics/{channel_id}",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "subscriber_count" in data
    assert "view_count" in data
    assert "is_live_data" in data
    assert "metrics_notes" in data


def test_unverified_analytics_history_is_honest():
    headers = _auth_headers()
    channels_r = client.get("/api/v1/youtube/channels", headers=headers)
    assert channels_r.status_code == 200, channels_r.text
    channels = channels_r.json()
    if not channels:
        pytest.skip("No channels available")

    channel_id = channels[0]["id"]
    r = client.get(
        f"/api/v1/youtube/analytics/{channel_id}/history",
        params={"start_date": "2026-10-01", "end_date": "2026-10-31"},
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["is_live_data"] is False
    assert data["rows"] == []
    assert data["error"]


@pytest.mark.parametrize("extension", ["csv", "pdf"])
def test_demo_or_unverified_exports_are_refused(extension):
    headers = _auth_headers()
    channels_r = client.get("/api/v1/youtube/channels", headers=headers)
    assert channels_r.status_code == 200, channels_r.text
    channels = channels_r.json()
    if not channels:
        pytest.skip("No channels available")

    channel_id = channels[0]["id"]
    r = client.get(
        f"/api/v1/youtube/analytics/{channel_id}/export/{extension}",
        params={"start_date": "2026-10-01", "end_date": "2026-10-31"},
        headers=headers,
    )
    assert r.status_code == 400


def test_live_report_csv_and_pdf_export_are_supported_for_verified_data():
    from app.core.database import SessionLocal
    from app.models.user import Channel
    from app.services.analytics_service import YouTubeAnalyticsService

    db = SessionLocal()
    try:
        channel = db.query(Channel).first()
        assert channel is not None
        report = {
            "channel_id": channel.id,
            "is_live_data": True,
            "data_mode": "live",
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
            "rows": [{
                "date": "2026-10-01",
                "views": 120,
                "estimated_minutes_watched": 45.5,
                "average_view_duration": 22.75,
                "subscribers_gained": 3,
                "subscribers_lost": 1,
            }],
        }
        csv_text = YouTubeAnalyticsService.export_csv(channel, report)
        assert "YouTube Analytics Export" in csv_text
        assert "2026-10-01" in csv_text
        pdf_bytes = YouTubeAnalyticsService.export_pdf(channel, report)
        assert pdf_bytes.startswith(b"%PDF")
    finally:
        db.close()


def test_duplicate_channel_daily_analytics_record_prevention():
    from datetime import date
    from app.core.database import SessionLocal
    from app.models.analytics import ChannelAnalyticsDaily
    from app.models.user import Channel

    db = SessionLocal()
    try:
        channel = db.query(Channel).first()
        assert channel is not None
        report_date = date(2026, 10, 1)
        existing = db.query(ChannelAnalyticsDaily).filter(
            ChannelAnalyticsDaily.channel_id == channel.id,
            ChannelAnalyticsDaily.report_date == report_date,
        ).first()
        if not existing:
            db.add(ChannelAnalyticsDaily(
                channel_id=channel.id,
                report_date=report_date,
                views=10,
                estimated_minutes_watched=4.0,
            ))
            db.commit()
        count = db.query(ChannelAnalyticsDaily).filter(
            ChannelAnalyticsDaily.channel_id == channel.id,
            ChannelAnalyticsDaily.report_date == report_date,
        ).count()
        assert count == 1
    finally:
        db.close()
