import os
import tempfile
import pytest
from app.services.video.ffprobe_validator import FFprobeValidator


def test_validator_nonexistent_file():
    res = FFprobeValidator.probe_video("nonexistent_video_path_12345.mp4")
    assert res["valid"] is False
    assert "File does not exist" in res["error"]


def test_validator_truncated_file():
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"NOT A REAL VIDEO" * 10)
        tmp_name = f.name
    try:
        res = FFprobeValidator.probe_video(tmp_name)
        assert res["valid"] is False
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)


def test_validator_valid_video():
    storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../storage/renders"))
    candidates = [os.path.join(storage_dir, f) for f in os.listdir(storage_dir) if f.endswith(".mp4")] if os.path.exists(storage_dir) else []
    if not candidates:
        pytest.skip("No rendered MP4 available yet")
    res = FFprobeValidator.probe_video(candidates[0])
    assert res["valid"] is True
    assert res["has_video"] is True
    assert res["has_audio"] is True
    assert res["duration_seconds"] > 0.5
    assert res["width"] > 0
    assert res["height"] > 0
