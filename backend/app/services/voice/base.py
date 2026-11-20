from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseVoiceProvider(ABC):
    @abstractmethod
    def get_provider_key(self) -> str:
        pass

    @abstractmethod
    def get_available_voices(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice_id: str,
        speed: float = 1.0,
        pitch: float = 0.0,
    ) -> str:
        """Synthesizes audio file and returns the output file path."""
        pass
