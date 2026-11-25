import os
import asyncio
import subprocess
import tempfile
from typing import Dict, Any, List
import edge_tts
from app.services.voice.base import BaseVoiceProvider

class EdgeTTSVoiceProvider(BaseVoiceProvider):
    """
    Microsoft Edge Neural TTS Provider.
    Zero-cost, high-fidelity neural voices with native Telugu and English support.
    Runs asynchronously with zero GPU / local VRAM footprint.
    """
    def get_provider_key(self) -> str:
        return "edge_tts"

    def get_available_voices(self) -> List[Dict[str, Any]]:
        return [
            # Telugu Voices
            {
                "id": "te-IN-MohanNeural",
                "name": "Mohan (తెలుగు - Male Neural)",
                "gender": "male",
                "language": "te",
                "engine": "edge_tts",
            },
            {
                "id": "te-IN-ShrutiNeural",
                "name": "Shruti (తెలుగు - Female Neural)",
                "gender": "female",
                "language": "te",
                "engine": "edge_tts",
            },
            # English Voices
            {
                "id": "en-US-ChristopherNeural",
                "name": "Christopher (English - Male Narrative)",
                "gender": "male",
                "language": "en",
                "engine": "edge_tts",
            },
            {
                "id": "en-US-GuyNeural",
                "name": "Guy (English - Male Conversational)",
                "gender": "male",
                "language": "en",
                "engine": "edge_tts",
            },
            {
                "id": "en-US-JennyNeural",
                "name": "Jenny (English - Female Expressive)",
                "gender": "female",
                "language": "en",
                "engine": "edge_tts",
            },
            {
                "id": "en-US-AriaNeural",
                "name": "Aria (English - Female Narrative)",
                "gender": "female",
                "language": "en",
                "engine": "edge_tts",
            },
        ]

    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice_id: str = "te-IN-MohanNeural",
        speed: float = 1.0,
        pitch: float = 0.0,
    ) -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        requested_ext = os.path.splitext(output_path)[1].lower()
        if requested_ext not in (".mp3", ".wav"):
            raise ValueError("Edge TTS output must be .mp3 or .wav")

        # Edge TTS emits MP3. Convert explicitly when WAV was requested.
        temp_mp3 = output_path if requested_ext == ".mp3" else os.path.join(
            tempfile.gettempdir(), f"edge_tts_{os.getpid()}_{id(self)}.mp3"
        )

        # Format rate and pitch adjustments
        rate_percent = int((speed - 1.0) * 100)
        rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"

        pitch_hz = int(pitch)
        pitch_str = f"+{pitch_hz}Hz" if pitch_hz >= 0 else f"{pitch_hz}Hz"

        last_error = None
        for attempt in range(3):
            try:
                for stale_path in (output_path, temp_mp3):
                    if os.path.exists(stale_path):
                        os.remove(stale_path)

                communicate = edge_tts.Communicate(
                    text=text,
                    voice=voice_id,
                    rate=rate_str,
                    pitch=pitch_str,
                )
                await communicate.save(temp_mp3)
                if not os.path.isfile(temp_mp3) or os.path.getsize(temp_mp3) == 0:
                    raise RuntimeError("Edge TTS returned an empty audio file")

                if requested_ext == ".wav":
                    try:
                        import imageio_ffmpeg
                        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
                    except Exception as exc:
                        raise RuntimeError("WAV output requires the bundled FFmpeg converter") from exc

                    result = subprocess.run(
                        [
                            ffmpeg, "-y", "-i", temp_mp3,
                            "-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le", output_path,
                        ],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode != 0:
                        raise RuntimeError(f"Edge TTS MP3-to-WAV conversion failed: {result.stderr[-500:]}")
                    return output_path

                return temp_mp3
            except Exception as exc:
                last_error = exc
                # Provider 403/empty-audio responses can be transient. Retry them,
                # but never replace them with synthetic audio.
                if attempt < 2:
                    await asyncio.sleep(0.75 * (attempt + 1))
            finally:
                if requested_ext == ".wav" and os.path.exists(temp_mp3):
                    os.remove(temp_mp3)

        for stale_path in (output_path, temp_mp3):
            if os.path.exists(stale_path):
                os.remove(stale_path)
        raise RuntimeError(f"Edge TTS synthesis failed for {voice_id}: {last_error}") from last_error
