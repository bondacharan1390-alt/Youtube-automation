import pytest
from app.services.video.subtitle_generator import generate_srt, generate_vtt

SCENES = [
    {"scene_order": 1, "narration_text": "Welcome to AI YouTube Studio", "script_text": None, "duration_seconds": 5.0},
    {"scene_order": 2, "narration_text": "This is an automated video creation platform", "script_text": None, "duration_seconds": 6.0},
    {"scene_order": 3, "narration_text": None, "script_text": "AI technology is transforming content creation", "duration_seconds": 4.0},
]

def test_srt_format():
    srt = generate_srt(SCENES)
    assert "-->" in srt
    assert "Welcome to AI YouTube Studio" in srt
    assert "00:00:00,000" in srt or "00:00:" in srt

def test_vtt_format():
    vtt = generate_vtt(SCENES)
    assert vtt.startswith("WEBVTT")
    assert "-->" in vtt
    assert "automated video creation" in vtt

def test_srt_timestamps_sequential():
    srt = generate_srt(SCENES)
    lines = [l for l in srt.split("\n") if "-->" in l]
    assert len(lines) >= 2
    # Second timestamp should be after the first
    times = [l.split(" --> ")[0].strip() for l in lines]
    assert times[0] <= times[1]

def test_empty_scenes():
    srt = generate_srt([])
    assert srt == ""

def test_vtt_uses_dot_separator():
    vtt = generate_vtt(SCENES[:1])
    # VTT uses . for ms, SRT uses ,
    for line in vtt.split("\n"):
        if "-->" in line:
            assert "." in line
            assert "," not in line
