from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
import bcrypt
from jose import jwt, JWTError
from app.core.config import settings

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False

MEDIA_TICKET_SECRET = f"{settings.SECRET_KEY}::MEDIA_TICKET_ONLY"

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access_token"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Strict security check: media-tickets or other token types CANNOT be used as access tokens
        if payload.get("type") == "media_ticket" or payload.get("scope") == "media_ticket":
            return None
        if not payload.get("sub"):
            return None
        return payload
    except JWTError:
        return None

def create_media_ticket(user_id: Any, video_id: Any, expires_minutes: int = 15) -> str:
    """
    Generate a short-lived, video-scoped media ticket for HTML5 video/thumbnail requests.
    Prevents leaking the account's full access token in URLs and server access logs.
    Signed with a separate key (MEDIA_TICKET_SECRET) and tagged with type="media_ticket".
    Cryptographically cannot be decoded or verified as a general account access token.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode = {
        "exp": expire,
        "sub": str(user_id),
        "video_id": str(video_id),
        "type": "media_ticket",
        "scope": "media_ticket"
    }
    return jwt.encode(to_encode, MEDIA_TICKET_SECRET, algorithm=settings.ALGORITHM)

def verify_media_ticket(ticket: str, video_id: Any) -> Optional[str]:
    """
    Verify that the media ticket is valid, not expired, and issued specifically for video_id.
    Uses MEDIA_TICKET_SECRET.
    Returns user_id string if valid, or None.
    """
    try:
        payload = jwt.decode(ticket, MEDIA_TICKET_SECRET, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "media_ticket" or payload.get("scope") != "media_ticket":
            return None
        if str(payload.get("video_id")) != str(video_id):
            return None
        return str(payload.get("sub"))
    except JWTError:
        return None
    except Exception:
        return None
