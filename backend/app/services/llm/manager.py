from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.provider import AIProvider
from app.core.security import decrypt_secret
from app.services.llm.base import BaseLLMProvider
from app.services.llm.ollama import OllamaProvider
from app.services.llm.gemini import GeminiProvider
from app.services.llm.fallback import FallbackScriptEngine

class LLMManager:
    """
    Central router that dynamically queries the best available LLM:
    1. Checks if local Ollama daemon is active and responsive.
    2. If not, checks if cloud Gemini API key is configured and valid.
    3. If neither is available, falls back to the high-fidelity Offline Heuristic Engine.
    """

    @classmethod
    def get_provider(cls, db: Optional[Session] = None) -> BaseLLMProvider:
        # 1. Check Ollama
        if db:
            ollama_rec = db.query(AIProvider).filter(AIProvider.provider_key == "ollama").first()
            base_url = (ollama_rec.base_url if ollama_rec else None) or "http://localhost:11434"
            model = "llama3.2:3b-instruct-q4_K_M"
            if ollama_rec and ollama_rec.settings_json:
                model = ollama_rec.settings_json.get("model", model)
        else:
            base_url = "http://localhost:11434"
            model = "llama3.2:3b-instruct-q4_K_M"

        ollama = OllamaProvider(base_url=base_url, model=model)
        health = ollama.check_health()
        if health.get("is_healthy"):
            return ollama

        # 2. Check Gemini Cloud
        if db:
            gemini_rec = db.query(AIProvider).filter(AIProvider.provider_key == "gemini").first()
            if gemini_rec and gemini_rec.encrypted_api_key:
                decrypted_key = decrypt_secret(gemini_rec.encrypted_api_key)
                if decrypted_key:
                    gemini = GeminiProvider(api_key=decrypted_key)
                    g_health = gemini.check_health()
                    if g_health.get("is_healthy"):
                        return gemini

        # 3. Resilient Fallback Engine
        return FallbackScriptEngine()

    @classmethod
    def generate_json_safe(
        cls,
        prompt: str,
        system_prompt: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        provider = cls.get_provider(db=db)
        try:
            return provider.generate_json(prompt, system_prompt=system_prompt)
        except Exception:
            # If primary selected provider fails during generation, fallback seamlessly
            fallback = FallbackScriptEngine()
            return fallback.generate_json(prompt, system_prompt=system_prompt)
