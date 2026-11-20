import os
import asyncio
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
        # Ensure .mp3 extension
        mp3_path = os.path.splitext(output_path)[0] + ".mp3"

        # Format rate and pitch adjustments
        rate_percent = int((speed - 1.0) * 100)
        rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"

        pitch_hz = int(pitch)
        pitch_str = f"+{pitch_hz}Hz" if pitch_hz >= 0 else f"{pitch_hz}Hz"

        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice_id,
                rate=rate_str,
                pitch=pitch_str,
            )
            await communicate.save(mp3_path)
            return mp3_path
        except Exception:
            # If network is unavailable or sandboxed, seamlessly fallback to local audio synthesis
            from app.services.voice.fallback_voice_provider import FallbackVoiceProvider
            fallback = FallbackVoiceProvider()
            return await fallback.synthesize(
                text=text,
                output_path=output_path,
                voice_id=voice_id,
                speed=speed,
                pitch=pitch,
            )
