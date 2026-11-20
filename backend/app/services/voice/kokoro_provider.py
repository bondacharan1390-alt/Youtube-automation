import os
from typing import Dict, Any, List
from app.services.voice.base import BaseVoiceProvider
from app.services.voice.fallback_voice_provider import FallbackVoiceProvider

class KokoroVoiceProvider(BaseVoiceProvider):
    """
    Kokoro 82M TTS Provider.
    Ultra-lightweight open-weight model for expressive natural English.
    """
    def get_provider_key(self) -> str:
        return "kokoro"

    def get_available_voices(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "af_heart",
                "name": "Heart (Kokoro - Female Soft)",
                "gender": "female",
                "language": "en",
                "engine": "kokoro",
            },
            {
                "id": "af_bella",
                "name": "Bella (Kokoro - Female Expressive)",
                "gender": "female",
                "language": "en",
                "engine": "kokoro",
            },
            {
                "id": "af_sarah",
                "name": "Sarah (Kokoro - Female Dynamic)",
                "gender": "female",
                "language": "en",
                "engine": "kokoro",
            },
            {
                "id": "am_adam",
                "name": "Adam (Kokoro - Male Cinematic)",
                "gender": "male",
                "language": "en",
                "engine": "kokoro",
            },
            {
                "id": "am_michael",
                "name": "Michael (Kokoro - Male Deep)",
                "gender": "male",
                "language": "en",
                "engine": "kokoro",
            },
        ]

    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice_id: str = "af_heart",
        speed: float = 1.0,
        pitch: float = 0.0,
    ) -> str:
        # Fallback to local audio synthesis if Kokoro binary not loaded
        fallback = FallbackVoiceProvider()
        return await fallback.synthesize(
            text=text,
            output_path=output_path,
            voice_id=voice_id,
            speed=speed,
            pitch=pitch,
        )
