import os
import tempfile
import pytest
from app.services.youtube.resumable_uploader import ResumableUploader


def test_resumable_chunk_range_calculation():
    """Verify standard RFC 7233 byte-range math for chunked uploads."""
    total_size = 12 * 1024 * 1024  # 12 MB
    chunk_size = 5 * 1024 * 1024   # 5 MB chunk

    chunks = []
    start = 0
    while start < total_size:
        end = min(start + chunk_size, total_size) - 1
        chunks.append((start, end))
        start = end + 1

    assert len(chunks) == 3
    # Chunk 0: 0 to 5242879 (5 MB)
    assert chunks[0] == (0, 5242879)
    # Chunk 1: 5242880 to 10485759 (5 MB)
    assert chunks[1] == (5242880, 10485759)
    # Chunk 2: 10485760 to 12582911 (2 MB)
    assert chunks[2] == (10485760, 12582911)

    content_range = f"bytes {chunks[0][0]}-{chunks[0][1]}/{total_size}"
    assert content_range == "bytes 0-5242879/12582912"


def test_resumable_uploader_simulation():
    """Verify offline / staging resumable upload simulation with progress tracking."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        # Write 8 MB dummy data
        f.write(b"0" * (8 * 1024 * 1024))
        temp_path = f.name

    progress_log = []
    try:
        def on_progress(bytes_done, total):
            progress_log.append((bytes_done, total))

        res = ResumableUploader.simulate_resumable_upload(
            file_path=temp_path,
            chunk_size=3 * 1024 * 1024,
            progress_callback=on_progress,
        )

        assert res["status"] == "uploaded"
        assert res["video_id"].startswith("sim_")
        assert res["total_bytes"] == 8 * 1024 * 1024
        assert len(progress_log) == 3
        # Final progress must report 100%
        assert progress_log[-1][0] == 8 * 1024 * 1024
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_resumable_empty_file_handling():
    """Verify zero-length file raises error in resumable upload."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="is empty"):
            ResumableUploader.simulate_resumable_upload(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
