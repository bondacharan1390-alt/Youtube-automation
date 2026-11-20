from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ProviderBase(BaseModel):
    name: str
    provider_key: str
    category: str
    execution_mode: str = "local"
    is_active: bool = True
    base_url: Optional[str] = None
    settings_json: Dict[str, Any] = {}

class ProviderUpdate(BaseModel):
    is_active: Optional[bool] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    settings_json: Optional[Dict[str, Any]] = None

class ProviderResponse(ProviderBase):
    id: str
    is_healthy: bool
    has_api_key: bool = False
    health_status_message: str
    last_health_check: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class HealthCheckResponse(BaseModel):
    provider_key: str
    is_healthy: bool
    latency_ms: Optional[float] = None
    message: str
