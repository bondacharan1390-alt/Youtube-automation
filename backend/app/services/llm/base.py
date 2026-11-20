from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseLLMProvider(ABC):
    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns the human-readable provider name."""
        pass

    @abstractmethod
    def check_health(self) -> Dict[str, Any]:
        """Checks connection health and returns status dict."""
        pass

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generates plain text given a prompt."""
        pass

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Generates a structured JSON object given a prompt."""
        pass
