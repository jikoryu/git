"""Authentication service — register, login, token management."""

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.schemas.user import TokenResponse, UserLogin, UserRegister


def _hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        password.encode("utf-8"), hashed.encode("utf-8")
    )


def _create_token(subject: str, expires_delta: timedelta) -> str:
    """Create a JWT token for the given subject."""
    expire = datetime.now(tz=timezone.utc) + expires_delta
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def _decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises HTTPException on failure."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def register(db: AsyncSession, data: UserRegister) -> User:
    """Register a new user account."""
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = User(
        email=data.email,
        password_hash=_hash_password(data.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def login(db: AsyncSession, data: UserLogin) -> TokenResponse:
    """Authenticate user and return token pair."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not _verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    access_token = _create_token(
        str(user.id),
        timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token = _create_token(
        str(user.id),
        timedelta(days=settings.refresh_token_expire_days),
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


def refresh_access_token(refresh_token: str) -> TokenResponse:
    """Issue a new access token from a valid refresh token."""
    payload = _decode_token(refresh_token)
    user_id = payload.get("sub")
    new_access = _create_token(
        user_id, timedelta(minutes=settings.access_token_expire_minutes)
    )
    new_refresh = _create_token(
        user_id, timedelta(days=settings.refresh_token_expire_days)
    )
    return TokenResponse(access_token=new_access, refresh_token=new_refresh)
