import json
import httpx
from typing import Dict, Any, Optional
from app.services.llm.base import BaseLLMProvider

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def get_provider_name(self) -> str:
        return f"Google Gemini ({self.model})"

    def check_health(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"is_healthy": False, "message": "Gemini API key is not configured"}
        try:
            url = f"{self.base_url}/models/{self.model}?key={self.api_key}"
            with httpx.Client(timeout=5.0) as client:
                res = client.get(url)
                if res.status_code == 200:
                    return {"is_healthy": True, "message": "Gemini 1.5 Flash API active"}
                return {"is_healthy": False, "message": f"Gemini API returned {res.status_code}"}
        except Exception as e:
            return {"is_healthy": False, "message": f"Gemini connection error: {str(e)}"}

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        if not self.api_key:
            raise ValueError("Gemini API key not configured")

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        with httpx.Client(timeout=45.0) as client:
            res = client.post(url, json=payload)
            if res.status_code != 200:
                raise RuntimeError(f"Gemini API error {res.status_code}: {res.text}")
            data = res.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            return candidates[0]["content"]["parts"][0]["text"].strip()

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("Gemini API key not configured")

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        with httpx.Client(timeout=45.0) as client:
            res = client.post(url, json=payload)
            if res.status_code != 200:
                raise RuntimeError(f"Gemini API error {res.status_code}: {res.text}")
            data = res.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return json.loads(raw_text)
