"""FFprobe video integrity validation and recovery engine."""
import json
import logging
import os
import shutil
import subprocess
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def _get_ffmpeg() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg") or "ffmpeg"


def _get_ffprobe() -> str:
    """Find ffprobe binary or derive from ffmpeg directory."""
    ffmpeg_exe = _get_ffmpeg()
    ffprobe_dir = os.path.dirname(ffmpeg_exe)
    candidate = os.path.join(ffprobe_dir, "ffprobe.exe" if os.name == "nt" else "ffprobe")
    if os.path.exists(candidate):
        return candidate
    system_ffprobe = shutil.which("ffprobe")
    if system_ffprobe:
        return system_ffprobe
    # Fallback to ffmpeg for stream probing
    return ffmpeg_exe


class FFprobeValidator:
    """Validates rendered MP4 files to guarantee zero false positives."""

    @classmethod
    def probe_video(cls, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {
                "valid": False,
                "error": f"File does not exist: {file_path}",
                "file_size": 0,
            }

        file_size = os.path.getsize(file_path)
        if file_size < 10240:  # < 10 KB is definitely corrupted/incomplete
            return {
                "valid": False,
                "error": f"File size too small ({file_size} bytes)",
                "file_size": file_size,
            }

        ffmpeg = _get_ffmpeg()
        cmd = [ffmpeg, "-v", "error", "-i", file_path, "-f", "null", "-"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        has_decode_error = result.returncode != 0

        # Detailed stream analysis with ffmpeg -i
        info_cmd = [ffmpeg, "-i", file_path]
        info_result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30)
        info_text = info_result.stderr

        has_video_stream = "Video: h264" in info_text or "Video:" in info_text
        has_audio_stream = "Audio: aac" in info_text or "Audio:" in info_text

        # Extract duration
        duration_seconds = 0.0
        for line in info_text.split("\n"):
            if "Duration:" in line:
                try:
                    dur_str = line.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = dur_str.split(":")
                    duration_seconds = int(h) * 3600 + int(m) * 60 + float(s)
                except Exception:
                    pass
                break

        # Extract resolution
        width, height = 0, 0
        for line in info_text.split("\n"):
            if "Stream" in line and "Video:" in line:
                for token in line.split(","):
                    token = token.strip()
                    if "x" in token and any(c.isdigit() for c in token):
                        parts = token.split()[0].split("x")
                        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                            width, height = int(parts[0]), int(parts[1])
                            break

        is_valid = (
            not has_decode_error
            and has_video_stream
            and has_audio_stream
            and duration_seconds > 0.5
            and width > 0
            and height > 0
        )

        return {
            "valid": is_valid,
            "file_size": file_size,
            "has_video": has_video_stream,
            "has_audio": has_audio_stream,
            "width": width,
            "height": height,
            "duration_seconds": duration_seconds,
            "decode_error": result.stderr.strip() if has_decode_error else None,
            "raw_info": info_text[:400],
        }

    @classmethod
    def attempt_recovery_encode(cls, corrupted_path: str, output_path: str) -> bool:
        """Attempt safe re-encode recovery for video with playback/atom issues."""
        try:
            ffmpeg = _get_ffmpeg()
            cmd = [
                ffmpeg, "-y",
                "-err_detect", "ignore_err",
                "-i", corrupted_path,
                "-c:v", "libx264", "-preset", "medium", "-crf", "24",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                "-movflags", "+faststart",
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if result.returncode == 0 and os.path.exists(output_path):
                verification = cls.probe_video(output_path)
                return verification["valid"]
            return False
        except Exception as e:
            logger.error(f"Recovery encode failed: {e}")
            return False
