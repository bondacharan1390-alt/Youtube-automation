"""Video composition engine using FFmpeg (bundled via imageio-ffmpeg)."""
import os
import json
import shutil
import asyncio
import subprocess
import tempfile
import logging
from datetime import datetime, timezone
from typing import List, Optional, Any
from sqlalchemy.orm import Session
from app.models.project import Project, Scene, Asset, RenderJob
from app.services.hardware_queue import HardwareTaskQueue
from app.services.video.subtitle_generator import generate_srt, generate_vtt
from app.services.video.ffprobe_validator import FFprobeValidator

logger = logging.getLogger(__name__)

STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage"))

def _get_ffmpeg() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg") or "ffmpeg"

def _run_ffmpeg(args: List[str], description: str = "") -> subprocess.CompletedProcess:
    """Run ffmpeg command and return result."""
    ffmpeg = _get_ffmpeg()
    cmd = [ffmpeg, "-y"] + args
    logger.info(f"FFmpeg [{description}]: {' '.join(cmd[:8])}...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        logger.error(f"FFmpeg error: {result.stderr[-500:]}")
        raise RuntimeError(f"FFmpeg failed [{description}]: {result.stderr[-300:]}")
    return result

def _create_scene_video(
    image_path: str,
    audio_path: Optional[str],
    duration: float,
    output_path: str,
    width: int,
    height: int,
    scene_index: int,
) -> None:
    """Create a single scene video from image + audio using Ken Burns zoom."""
    # Build filter for ken burns zoom: slow zoom from 1.0 to 1.05
    fps = 25
    total_frames = int(duration * fps)
    zoom_expr = f"'min(zoom+0.0004,1.08)'"
    vf = (
        f"scale={width*2}:{height*2},"
        f"zoompan=z={zoom_expr}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":d={total_frames}:s={width}x{height}:fps={fps},"
        f"format=yuv420p"
    )
    if audio_path and os.path.exists(audio_path):
        args = [
            "-loop", "1", "-i", image_path,
            "-i", audio_path,
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-t", str(duration),
            "-shortest",
            output_path
        ]
    else:
        # Generate silent audio
        args = [
            "-loop", "1", "-i", image_path,
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-t", str(duration),
            "-shortest",
            output_path
        ]
    _run_ffmpeg(args, f"scene_{scene_index}_video")

def _create_placeholder_image(output_path: str, width: int, height: int, text: str) -> None:
    """Create a gradient placeholder image using PIL."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (width, height), color=(20, 20, 40))
        draw = ImageDraw.Draw(img)
        # Gradient overlay
        for y in range(height):
            alpha = int(40 * (1 - y / height))
            draw.line([(0, y), (width, y)], fill=(20 + alpha, 20, 60 + alpha))
        # Scene text
        draw.text((width // 2, height // 2), text[:60], fill=(200, 200, 220), anchor="mm")
        img.save(output_path, "PNG")
    except Exception as e:
        logger.warning(f"PIL placeholder failed: {e} — creating minimal PNG")
        # Minimal valid PNG (1x1 pixel) upscaled via ffmpeg
        with open(output_path, "wb") as f:
            f.write(bytes([
                0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A,0x00,0x00,0x00,0x0D,
                0x49,0x48,0x44,0x52,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x01,
                0x08,0x02,0x00,0x00,0x00,0x90,0x77,0x53,0xDE,0x00,0x00,0x00,
                0x0C,0x49,0x44,0x41,0x54,0x08,0xD7,0x63,0x14,0x14,0x14,0x00,
                0x00,0x00,0x20,0x00,0x01,0xE2,0x28,0xFB,0xCA,0x00,0x00,0x00,
                0x00,0x49,0x45,0x4E,0x44,0xAE,0x42,0x60,0x82
            ]))

async def compose_video_async(
    project_id: str,
    resolution: str,
    include_subtitles: bool,
    bgm_volume: float,
    db: Session,
    job_id: str,
    bitrate_kbps: int = 5000,
    fps: int = 25,
) -> str:
    """Full async video composition pipeline."""
    renders_dir = os.path.join(STORAGE_DIR, "renders")
    subtitles_dir = os.path.join(STORAGE_DIR, "subtitles")
    temp_dir = tempfile.mkdtemp(prefix=f"render_{project_id}_")
    os.makedirs(renders_dir, exist_ok=True)
    os.makedirs(subtitles_dir, exist_ok=True)

    try:
        # Resolve resolution
        width, height = (1920, 1080) if resolution == "1080p" else (1280, 720)

        # Load project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Shorts → portrait
        if project.aspect_ratio == "9:16":
            width, height = (1080, 1920) if resolution == "1080p" else (720, 1280)

        scenes = sorted(project.scenes, key=lambda s: s.scene_order)
        if not scenes:
            raise ValueError("Project has no scenes")

        # Update job progress helper
        def _update_job(pct: int, msg: str):
            job = db.query(RenderJob).filter(RenderJob.id == job_id).first()
            if job:
                job.progress_percentage = pct
                job.error_log = msg
                db.commit()

        _update_job(5, "Preparing scenes...")

        # Generate subtitles
        scenes_data = [
            {
                "scene_order": s.scene_order,
                "narration_text": s.narration_text,
                "script_text": s.script_text,
                "duration_seconds": s.duration_seconds or 5.0,
            }
            for s in scenes
        ]
        srt_content = generate_srt(scenes_data)
        vtt_content = generate_vtt(scenes_data)
        srt_path = os.path.join(subtitles_dir, f"{project_id}.srt")
        vtt_path = os.path.join(subtitles_dir, f"{project_id}.vtt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        with open(vtt_path, "w", encoding="utf-8") as f:
            f.write(vtt_content)

        _update_job(15, "Rendering scene videos...")

        # Build per-scene video clips
        scene_videos = []
        total_scenes = len(scenes)
        for idx, scene in enumerate(scenes):
            scene_vid_path = os.path.join(temp_dir, f"scene_{idx:03d}.mp4")

            # Resolve image
            image_path = None
            if scene.visual_asset_id:
                asset = db.query(Asset).filter(Asset.id == scene.visual_asset_id).first()
                if asset and os.path.exists(asset.file_path):
                    image_path = asset.file_path
            if not image_path:
                # Look for auto-generated image
                images_dir = os.path.join(STORAGE_DIR, "images")
                candidate = os.path.join(images_dir, f"scene_{scene.id}.png")
                if os.path.exists(candidate):
                    image_path = candidate
            if not image_path:
                # Create placeholder
                placeholder = os.path.join(temp_dir, f"placeholder_{idx:03d}.png")
                _create_placeholder_image(placeholder, width, height, scene.script_text or f"Scene {scene.scene_order}")
                image_path = placeholder

            # Resolve audio
            audio_path = None
            if scene.voice_asset_id:
                asset = db.query(Asset).filter(Asset.id == scene.voice_asset_id).first()
                if asset and os.path.exists(asset.file_path):
                    audio_path = asset.file_path
            if not audio_path:
                audio_dir = os.path.join(STORAGE_DIR, "audio")
                candidate_mp3 = os.path.join(audio_dir, f"scene_{scene.id}.mp3")
                candidate_wav = os.path.join(audio_dir, f"scene_{scene.id}.wav")
                if os.path.exists(candidate_mp3):
                    audio_path = candidate_mp3
                elif os.path.exists(candidate_wav):
                    audio_path = candidate_wav

            duration = scene.duration_seconds or 5.0
            _create_scene_video(image_path, audio_path, duration, scene_vid_path, width, height, idx)
            scene_videos.append(scene_vid_path)

            progress = 15 + int(60 * (idx + 1) / total_scenes)
            _update_job(progress, f"Rendered scene {idx+1}/{total_scenes}")
            # Yield to event loop
            await asyncio.sleep(0)

        _update_job(78, "Concatenating scenes...")

        # Concatenate all scene videos
        concat_list = os.path.join(temp_dir, "concat.txt")
        with open(concat_list, "w") as f:
            for sv in scene_videos:
                f.write(f"file '{sv}'\n")

        concat_output = os.path.join(temp_dir, "concat.mp4")
        _run_ffmpeg(
            ["-f", "concat", "-safe", "0", "-i", concat_list,
             "-c", "copy", concat_output],
            "concat"
        )

        _update_job(85, "Encoding final video...")

        final_output = os.path.join(renders_dir, f"{project_id}.mp4")

        if include_subtitles and os.path.exists(srt_path):
            # Burn subtitles — use escaped path for ffmpeg on Windows
            clean_srt = srt_path.replace("\\", "/")
            escaped_srt = clean_srt.replace(":", r"\:")
            _run_ffmpeg([
                "-i", concat_output,
                "-vf", f"subtitles=filename='{escaped_srt}':force_style='FontSize=20,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2'",
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-c:a", "aac", "-b:a", "128k",
                final_output
            ], "burn_subtitles")
        else:
            _run_ffmpeg([
                "-i", concat_output,
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-c:a", "aac", "-b:a", "128k",
                final_output
            ], "final_encode")

        _update_job(90, "Validating render output with FFprobe...")

        # Strict validation: Never report successful rendering until validated!
        validation = FFprobeValidator.probe_video(final_output)
        if not validation["valid"]:
            logger.warning(f"Initial render validation failed: {validation}. Attempting recovery encode...")
            _update_job(92, "Attempting error recovery re-encode...")
            recovered_output = os.path.join(renders_dir, f"{project_id}_recovered.mp4")
            success = FFprobeValidator.attempt_recovery_encode(final_output, recovered_output)
            if success:
                os.replace(recovered_output, final_output)
                validation = FFprobeValidator.probe_video(final_output)
            
            if not validation["valid"]:
                raise RuntimeError(f"FFprobe integrity validation failed: {validation.get('error') or validation.get('decode_error')}")

        _update_job(95, "Saving asset record...")

        # Register as asset
        file_size = os.path.getsize(final_output) if os.path.exists(final_output) else 0
        video_asset = Asset(
            project_id=project_id,
            asset_type="video",
            storage_provider="local",
            file_path=final_output,
            file_name=f"{project_id}.mp4",
            mime_type="video/mp4",
            file_size_bytes=file_size,
        )
        db.add(video_asset)

        project.status = "rendered"
        db.commit()

        _update_job(100, f"Render complete ({validation['duration_seconds']:.1f}s, {validation['width']}x{validation['height']})")
        return final_output

    except Exception as e:
        logger.exception(f"Render failed: {e}")
        job = db.query(RenderJob).filter(RenderJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_log = str(e)
            db.commit()
        raise
    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
