import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class AIProvider(Base):
    __tablename__ = "providers"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    
    # Unique identifier key, e.g.: 'ollama', 'kokoro', 'edge_tts', 'faster_whisper', 'comfyui', 'gemini', 'elevenlabs', 'youtube'
    provider_key = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    
    # 'llm', 'tts', 'stt', 'image', 'youtube'
    category = Column(String(50), nullable=False)
    
    # 'local' or 'cloud'
    execution_mode = Column(String(20), default="local")
    
    is_active = Column(Boolean, default=True)
    is_healthy = Column(Boolean, default=False)
    
    # Encrypted API key or auth token
    encrypted_api_key = Column(Text, nullable=True)
    base_url = Column(String(255), nullable=True)
    
    # Provider specific config (model name, temperature, voice id, etc.)
    settings_json = Column(JSON, default=dict)
    
    last_health_check = Column(DateTime, nullable=True)
    health_status_message = Column(String(255), default="Not checked yet")
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=True)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
