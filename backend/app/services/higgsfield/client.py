"""Small, server-only Higgsfield REST client.

This module deliberately does not submit a request for health checks. Generation
requests can consume prepaid balance, so callers must explicitly submit them.
"""

from typing import Any, Dict, Optional
from urllib.parse import urljoin, urlparse

import httpx

from app.core.config import settings


class HiggsfieldAPIError(RuntimeError):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class HiggsfieldClient:
    def __init__(self, credential: str, base_url: Optional[str] = None):
        if not credential:
            raise HiggsfieldAPIError("Higgsfield API credential is not configured")
        self.credential = credential
        self.base_url = (base_url or settings.HIGGSFIELD_API_BASE_URL).rstrip("/")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Key {self.credential}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _safe_url(self, url: str) -> str:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = urljoin(f"{self.base_url}/", url.lstrip("/"))
        parsed = urlparse(url)
        configured = urlparse(self.base_url)
        if parsed.scheme != configured.scheme or parsed.netloc != configured.netloc:
            raise HiggsfieldAPIError("Higgsfield returned an unsafe lifecycle URL")
        return url

    async def _request(self, method: str, url: str, **kwargs: Any) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=settings.HIGGSFIELD_TIMEOUT_SECONDS) as client:
                response = await client.request(method, url, headers=self._headers(), **kwargs)
        except httpx.HTTPError as exc:
            raise HiggsfieldAPIError(f"Higgsfield request failed: {exc.__class__.__name__}") from exc

        if response.status_code >= 400:
            detail = "Higgsfield API request failed"
            try:
                body = response.json()
                if isinstance(body, dict):
                    detail = str(body.get("error") or body.get("message") or detail)
            except ValueError:
                pass
            raise HiggsfieldAPIError(detail, response.status_code)

        try:
            data = response.json()
        except ValueError as exc:
            raise HiggsfieldAPIError("Higgsfield returned invalid JSON", response.status_code) from exc
        if not isinstance(data, dict):
            raise HiggsfieldAPIError("Higgsfield returned an unexpected response")
        return data

    async def submit(self, model_path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not model_path or model_path.startswith("http") or ".." in model_path:
            raise HiggsfieldAPIError("Invalid Higgsfield model path")
        url = f"{self.base_url}/{model_path.strip('/')}"
        return await self._request("POST", url, json=payload)

    async def status(self, status_url: str, request_id: str) -> Dict[str, Any]:
        url = status_url or urljoin(f"{self.base_url}/", f"requests/{request_id}/status")
        return await self._request("GET", self._safe_url(url))

    async def cancel(self, cancel_url: str, request_id: str) -> Dict[str, Any]:
        url = cancel_url or urljoin(f"{self.base_url}/", f"requests/{request_id}/cancel")
        return await self._request("POST", self._safe_url(url))
