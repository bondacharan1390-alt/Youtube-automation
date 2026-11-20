import os
import wave
import math
import struct
from typing import Dict, Any, List
from app.services.voice.base import BaseVoiceProvider

class FallbackVoiceProvider(BaseVoiceProvider):
    """
    Generates standard, compliant PCM WAV audio files offline with spoken tone frequency.
    Ensures that when external audio daemons are offline or missing credentials,
    the platform always generates playable audio files immediately for tests and UI previews.
    """
    def get_provider_key(self) -> str:
        return "fallback_voice"

    def get_available_voices(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "fallback_en_male",
                "name": "Standard Studio Male (Offline)",
                "gender": "male",
                "language": "en",
                "engine": "offline",
            },
            {
                "id": "fallback_en_female",
                "name": "Standard Studio Female (Offline)",
                "gender": "female",
                "language": "en",
                "engine": "offline",
            },
            {
                "id": "fallback_te_male",
                "name": "తెలుగు స్టూడియో వాయిస్ (ఆఫ్‌లైన్)",
                "gender": "male",
                "language": "te",
                "engine": "offline",
            },
            {
                "id": "fallback_te_female",
                "name": "తెలుగు న్యూస్ రీడర్ (ఆఫ్‌లైన్)",
                "gender": "female",
                "language": "te",
                "engine": "offline",
            },
        ]

    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice_id: str,
        speed: float = 1.0,
        pitch: float = 0.0,
    ) -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Ensure .wav extension for fallback generator
        wav_path = os.path.splitext(output_path)[0] + ".wav"

        # Calculate duration based on text length: ~140 words per minute
        word_count = max(len(text.split()), 5)
        duration_seconds = max(round((word_count / 140.0) * 60.0 / max(speed, 0.5), 1), 3.0)

        # Standard CD quality audio: 44.1kHz, 16-bit, Mono
        sample_rate = 44100
        num_samples = int(duration_seconds * sample_rate)
        
        # Female voice frequency ~260Hz, Male voice ~180Hz
        base_freq = 240.0 if "female" in voice_id else 180.0
        target_freq = max(base_freq + pitch * 2.0, 100.0)

        with wave.open(wav_path, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)

            # Generate pleasant modulated tone simulating vocal speech pulses
            frames = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                # Harmonic speech envelope modulation
                envelope = math.sin(math.pi * (i / num_samples))
                speech_cadence = (math.sin(2 * math.pi * 3.5 * t) + 1.0) / 2.0
                sample = int(
                    32767
                    * 0.4
                    * envelope
                    * speech_cadence
                    * (0.7 * math.sin(2 * math.pi * target_freq * t) + 0.3 * math.sin(2 * math.pi * target_freq * 2 * t))
                )
                frames.extend(struct.pack("<h", max(-32768, min(32767, sample))))
            wav_file.writeframes(frames)

        return wav_path
