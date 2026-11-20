from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseImageProvider(ABC):
    @abstractmethod
    def get_provider_key(self) -> str:
        pass

    @abstractmethod
    def check_health(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        output_path: str,
        aspect_ratio: str = "16:9",
        negative_prompt: str = "",
        seed: int = 42,
    ) -> str:
        """Generates an image file and returns the output file path."""
        pass
