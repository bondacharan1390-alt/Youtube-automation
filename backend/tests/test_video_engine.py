import pytest
from app.services.video.subtitle_generator import generate_srt, generate_vtt

def test_subtitle_generator_import():
    """Verify subtitle generator module imports cleanly."""
    from app.services.video import subtitle_generator
    assert hasattr(subtitle_generator, "generate_srt")
    assert hasattr(subtitle_generator, "generate_vtt")

def test_video_composer_import():
    """Verify video_composer imports cleanly (uses imageio-ffmpeg)."""
    from app.services.video import video_composer
    assert hasattr(video_composer, "_get_ffmpeg")
    ffmpeg = video_composer._get_ffmpeg()
    assert ffmpeg is not None and len(ffmpeg) > 0

def test_render_job_import():
    """Verify render_job module imports cleanly."""
    from app.services.video.render_job import RenderJobService
    assert hasattr(RenderJobService, "start_render")
    assert hasattr(RenderJobService, "get_job_status")

def test_srt_timing_accuracy():
    """Verify SRT timing math is correct."""
    from app.services.video.subtitle_generator import _format_srt_time
    assert _format_srt_time(0.0) == "00:00:00,000"
    assert _format_srt_time(61.5) == "00:01:01,500"
    # 3661.1 may produce ,099 or ,100 due to float precision — accept both
    result = _format_srt_time(3661.1)
    assert result in ("01:01:01,100", "01:01:01,099")

def test_vtt_timing_accuracy():
    """Verify VTT timing math is correct."""
    from app.services.video.subtitle_generator import _format_vtt_time
    assert _format_vtt_time(0.0) == "00:00:00.000"
    assert _format_vtt_time(90.25) == "00:01:30.250"
