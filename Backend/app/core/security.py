from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

VIDEO_STREAM_TOKEN_TYPE = "video-stream"
VIDEO_STREAM_TOKEN_TTL_MINUTES = 10


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise ValueError("Invalid authentication token.") from exc


def create_video_stream_token(
    user_id: int,
    video_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=VIDEO_STREAM_TOKEN_TTL_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "video_id": int(video_id),
        "typ": VIDEO_STREAM_TOKEN_TYPE,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_video_stream_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise ValueError("Invalid stream token.") from exc

    if payload.get("typ") != VIDEO_STREAM_TOKEN_TYPE:
        raise ValueError("Invalid stream token type.")
    if payload.get("video_id") is None:
        raise ValueError("Stream token is missing video id.")
    if payload.get("sub") is None:
        raise ValueError("Stream token is missing subject.")
    return payload
