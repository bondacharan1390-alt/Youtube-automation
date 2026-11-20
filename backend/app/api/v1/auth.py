from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.models.user import User, Channel
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered")
    
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Auto-create a default channel for the user
    channel = Channel(
        user_id=user.id,
        channel_name=f"{user.full_name or 'My'} AI Channel",
        quota_units_used_today=0
    )
    db.add(channel)
    db.commit()

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))

@router.post("/login", response_model=TokenResponse)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is inactive")
    
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)

@router.post("/dev-token", response_model=TokenResponse)
def get_dev_token(db: Session = Depends(get_db)):
    """Convenience endpoint for instant local development without credentials entry"""
    if not settings.DEBUG or settings.APP_ENV.lower() in ("production", "prod"):
        raise HTTPException(status_code=404, detail="Development token endpoint is disabled")
    user = db.query(User).filter(User.email == "creator@youtube-studio.ai").first()
    if not user:
        user = User(
            email="creator@youtube-studio.ai",
            full_name="AI Studio Creator",
            hashed_password=get_password_hash("creator12345"),
            is_active=True,
            is_superuser=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        channel = Channel(
            user_id=user.id,
            channel_name="AI Cinema Telugu & Global",
            quota_units_used_today=150
        )
        db.add(channel)
        db.commit()

    token = create_access_token(user.id, timedelta(days=30))
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))
