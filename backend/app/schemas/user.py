from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    is_superuser: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class ChannelResponse(BaseModel):
    id: str
    channel_name: str
    youtube_channel_id: Optional[str] = None
    thumbnail_url: Optional[str] = None
    quota_units_used_today: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
