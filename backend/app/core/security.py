from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import jwt
import bcrypt
from cryptography.fernet import Fernet
from app.core.config import settings

if settings.APP_ENV.lower() in ("production", "prod"):
    if not settings.SECRET_KEY or "change-in-env" in settings.SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be configured securely in production")
    if not settings.FERNET_KEY:
        raise RuntimeError("FERNET_KEY must be configured securely in production")

# Initialize Fernet cipher
try:
    fernet = Fernet(settings.FERNET_KEY.encode())
except Exception:
    fernet = Fernet(Fernet.generate_key())

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8")[:72], salt).decode("utf-8")

def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def create_oauth_state(user_id: str) -> str:
    to_encode = {
        "sub": str(user_id),
        "purpose": "youtube-oauth",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
        "nonce": __import__("secrets").token_urlsafe(24),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_oauth_state(state: str, user_id: str) -> bool:
    try:
        payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("purpose") == "youtube-oauth" and payload.get("sub") == str(user_id)
    except jwt.PyJWTError:
        return False

def encrypt_secret(plain_text: str) -> str:
    if not plain_text:
        return ""
    return fernet.encrypt(plain_text.encode()).decode()

def decrypt_secret(cipher_text: str) -> str:
    if not cipher_text:
        return ""
    try:
        return fernet.decrypt(cipher_text.encode()).decode()
    except Exception:
        return ""
