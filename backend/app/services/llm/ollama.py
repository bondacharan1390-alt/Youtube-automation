import json
import httpx
from typing import Dict, Any, Optional
from app.services.llm.base import BaseLLMProvider

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b-instruct-q4_K_M"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def get_provider_name(self) -> str:
        return f"Ollama ({self.model})"

    def check_health(self) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("models", [])]
                    return {
                        "is_healthy": True,
                        "message": f"Connected. Available models: {', '.join(models[:3]) or 'None'}",
                    }
                return {"is_healthy": False, "message": f"HTTP {res.status_code}"}
        except Exception as e:
            return {"is_healthy": False, "message": f"Ollama offline: {str(e)}"}

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "You are an expert YouTube content creator and scriptwriter.",
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        with httpx.Client(timeout=60.0) as client:
            res = client.post(f"{self.base_url}/api/generate", json=payload)
            if res.status_code != 200:
                raise RuntimeError(f"Ollama error {res.status_code}: {res.text}")
            return res.json().get("response", "").strip()

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        sys = (system_prompt or "") + "\nStrictly respond with a valid, parseable JSON object only. Do not include markdown codeblocks or conversational filler."
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": sys,
            "stream": False,
            "format": "json",
            "options": {"temperature": temperature},
        }
        with httpx.Client(timeout=60.0) as client:
            res = client.post(f"{self.base_url}/api/generate", json=payload)
            if res.status_code != 200:
                raise RuntimeError(f"Ollama error {res.status_code}: {res.text}")
            raw = res.json().get("response", "").strip()
            return json.loads(raw)
