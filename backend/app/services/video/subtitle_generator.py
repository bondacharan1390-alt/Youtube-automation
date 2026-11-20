"""Generate SRT and VTT subtitle files from project scenes."""
from typing import List, Dict, Any

def _format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT timestamp: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def _format_vtt_time(seconds: float) -> str:
    """Convert seconds to VTT timestamp: HH:MM:SS.mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

def generate_srt(scenes: List[Dict[str, Any]]) -> str:
    """Generate SRT subtitle content from scene list.
    Each scene dict: {scene_order, narration_text, duration_seconds}
    """
    lines = []
    cursor = 0.0
    for i, scene in enumerate(scenes, 1):
        duration = float(scene.get("duration_seconds", 5.0))
        text = (scene.get("narration_text") or scene.get("script_text") or "").strip()
        if not text:
            cursor += duration
            continue
        # Split long text into 2-line chunks of ~80 chars
        words = text.split()
        chunks = []
        current = []
        length = 0
        for w in words:
            if length + len(w) + 1 > 80 and current:
                chunks.append(" ".join(current))
                current = [w]
                length = len(w)
            else:
                current.append(w)
                length += len(w) + 1
        if current:
            chunks.append(" ".join(current))
        # Each chunk gets equal share of scene duration
        chunk_dur = duration / max(len(chunks), 1)
        for j, chunk in enumerate(chunks):
            start = cursor + j * chunk_dur
            end = start + chunk_dur - 0.1  # slight gap
            lines.append(str(i * 100 + j))
            lines.append(f"{_format_srt_time(start)} --> {_format_srt_time(end)}")
            lines.append(chunk)
            lines.append("")
        cursor += duration
    return "\n".join(lines)

def generate_vtt(scenes: List[Dict[str, Any]]) -> str:
    """Generate WebVTT subtitle content from scene list."""
    lines = ["WEBVTT", ""]
    cursor = 0.0
    for i, scene in enumerate(scenes, 1):
        duration = float(scene.get("duration_seconds", 5.0))
        text = (scene.get("narration_text") or scene.get("script_text") or "").strip()
        if not text:
            cursor += duration
            continue
        words = text.split()
        chunks = []
        current = []
        length = 0
        for w in words:
            if length + len(w) + 1 > 80 and current:
                chunks.append(" ".join(current))
                current = [w]
                length = len(w)
            else:
                current.append(w)
                length += len(w) + 1
        if current:
            chunks.append(" ".join(current))
        chunk_dur = duration / max(len(chunks), 1)
        for j, chunk in enumerate(chunks):
            start = cursor + j * chunk_dur
            end = start + chunk_dur - 0.1
            lines.append(f"cue-{i}-{j}")
            lines.append(f"{_format_vtt_time(start)} --> {_format_vtt_time(end)}")
            lines.append(chunk)
            lines.append("")
        cursor += duration
    return "\n".join(lines)
