import os
import subprocess
import wave
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.project import Project, Scene, Asset
from app.services.hardware_queue import HardwareTaskQueue
from app.services.voice.kokoro_provider import KokoroVoiceProvider
from app.services.voice.edge_tts_provider import EdgeTTSVoiceProvider
from app.services.voice.fallback_voice_provider import FallbackVoiceProvider

STORAGE_AUDIO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage/audio"))


def validate_audio_file(file_path: str) -> Dict[str, Any]:
    """Validate that an audio file is decodable and contains non-silent samples."""
    if not os.path.isfile(file_path) or os.path.getsize(file_path) < 1024:
        raise ValueError("Generated audio file is missing or empty")

    extension = os.path.splitext(file_path)[1].lower()
    if extension == ".wav":
        with wave.open(file_path, "rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_rate = wav_file.getframerate()
            frames = wav_file.readframes(wav_file.getnframes())
            sample_width = wav_file.getsampwidth()
            duration = wav_file.getnframes() / sample_rate if sample_rate else 0
        if not frames or not channels or not sample_rate or duration <= 0:
            raise ValueError("Generated WAV contains no playable audio frames")
        # 16-bit PCM is expected from the WAV conversion path.
        if sample_width != 2:
            raise ValueError("Generated WAV is not 16-bit PCM")
        if not any(frames):
            raise ValueError("Generated WAV contains silence only")
        return {"extension": "wav", "mime_type": "audio/wav", "duration": duration}

    if extension == ".mp3":
        try:
            import imageio_ffmpeg
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception as exc:
            raise ValueError("MP3 validation requires the bundled FFmpeg decoder") from exc
        result = subprocess.run(
            [ffmpeg, "-v", "error", "-i", file_path, "-f", "s16le", "-ac", "1", "-ar", "8000", "pipe:1"],
            capture_output=True,
        )
        if result.returncode != 0 or not result.stdout or not any(result.stdout):
            raise ValueError("Generated MP3 is not decodable or contains silence only")
        duration_result = subprocess.run(
            [ffmpeg, "-v", "error", "-i", file_path, "-f", "null", "-"],
            capture_output=True,
            text=True,
        )
        if duration_result.returncode != 0:
            raise ValueError("Generated MP3 failed decoder validation")
        return {"extension": "mp3", "mime_type": "audio/mpeg", "duration": None}

    raise ValueError(f"Unsupported generated audio format: {extension}")

class VoiceService:
    @staticmethod
    def get_all_voices(
        language: Optional[str] = None,
        gender: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        providers = [
            EdgeTTSVoiceProvider(),
            KokoroVoiceProvider(),
            FallbackVoiceProvider(),
        ]
        all_voices = []
        seen_ids = set()
        for p in providers:
            for v in p.get_available_voices():
                if v["id"] in seen_ids:
                    continue
                if language and v["language"] != language:
                    continue
                if gender and v["gender"] != gender:
                    continue
                seen_ids.add(v["id"])
                all_voices.append(v)
        return all_voices

    @staticmethod
    def get_provider_for_voice(voice_id: str):
        if voice_id.startswith("te-IN") or voice_id.startswith("en-US"):
            return EdgeTTSVoiceProvider()
        elif voice_id.startswith("af_") or voice_id.startswith("am_"):
            return KokoroVoiceProvider()
        return FallbackVoiceProvider()

    @staticmethod
    async def synthesize_scene(
        scene_id: str,
        text: str,
        voice_id: str = "te-IN-MohanNeural",
        speed: float = 1.0,
        pitch: float = 0.0,
        output_format: str = "mp3",
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        os.makedirs(STORAGE_AUDIO_DIR, exist_ok=True)
        ext = "wav" if output_format.lower() == "wav" else "mp3"
        file_name = f"scene_{scene_id}.{ext}"
        output_path = os.path.join(STORAGE_AUDIO_DIR, file_name)

        provider = VoiceService.get_provider_for_voice(voice_id)

        # Enforce sequential execution on the hardware task queue
        actual_path = await HardwareTaskQueue.run_sequential(
            f"Voice Synthesis for Scene {scene_id}",
            provider.synthesize(
                text=text,
                output_path=output_path,
                voice_id=voice_id,
                speed=speed,
                pitch=pitch,
            ),
        )

        audio_info = validate_audio_file(actual_path)
        actual_ext = audio_info["extension"]

        file_size = os.path.getsize(actual_path) if os.path.exists(actual_path) else 0
        relative_url = f"/storage/audio/{os.path.basename(actual_path)}"

        # Link to DB scene and create asset if db is provided
        asset_id = None
        if db:
            scene = db.query(Scene).filter(Scene.id == scene_id).first()
            if scene:
                asset = Asset(
                    project_id=scene.project_id,
                    asset_type="audio",
                    storage_provider="local",
                    file_path=actual_path,
                    file_name=os.path.basename(actual_path),
                    mime_type=audio_info["mime_type"],
                    file_size_bytes=file_size,
                )
                db.add(asset)
                db.commit()
                db.refresh(asset)

                scene.voice_asset_id = asset.id
                db.commit()
                asset_id = asset.id

        return {
            "scene_id": scene_id,
            "asset_id": asset_id,
            "file_path": actual_path,
            "audio_url": relative_url,
            "file_size_bytes": file_size,
            "voice_id": voice_id,
            "speed": speed,
            "pitch": pitch,
            "mime_type": audio_info["mime_type"],
            "audio_format": actual_ext,
        }

    @staticmethod
    async def synthesize_project_scenes(
        project_id: str,
        voice_id: str = "te-IN-MohanNeural",
        speed: float = 1.0,
        pitch: float = 0.0,
        output_format: str = "mp3",
        db: Session = None,
    ) -> List[Dict[str, Any]]:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        results = []
        # Synthesize each scene sequentially
        for scene in project.scenes:
            text_to_speak = scene.narration_text or scene.script_text or f"Scene {scene.scene_order}"
            res = await VoiceService.synthesize_scene(
                scene_id=scene.id,
                text=text_to_speak,
                voice_id=voice_id,
                speed=speed,
                pitch=pitch,
                output_format=output_format,
                db=db,
            )
            results.append(res)

        project.status = "voiced"
        db.commit()
        return results
