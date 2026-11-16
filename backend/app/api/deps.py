from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_access_token, verify_media_ticket
from app.models.user import User, UserRole
from app.models.video import Video, VideoVisibility, VideoModerationStatus, VideoAccessGrant

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Extracts authenticated user from HTTP Authorization Bearer header
    (or legacy query ?token= for backward compatibility).
    NOTE: Media tickets are NEVER accepted as general access tokens!
    """
    effective_token = token
    if not effective_token:
        effective_token = request.query_params.get("token")

    if not effective_token:
        return None

    payload = decode_access_token(effective_token)
    if not payload or not payload.get("sub"):
        return None

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    return result.scalar_one_or_none()

async def get_media_user_optional(
    video_id: str,
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Specifically for read-only video stream and thumbnail delivery.
    Accepts:
    1. Short-lived media ticket via ?ticket=... strictly validated for this specific video_id.
    2. HTTP Authorization Bearer header.
    3. Query parameter ?token=... (backward compatibility).
    """
    # 1. Check scoped media ticket
    ticket = request.query_params.get("ticket")
    if ticket:
        ticket_user_id = verify_media_ticket(ticket, str(video_id))
        if ticket_user_id:
            result = await db.execute(select(User).where(User.id == ticket_user_id, User.is_active == True))
            return result.scalar_one_or_none()

    # 2. Check Bearer token from header or query param
    effective_token = token or request.query_params.get("token")
    if effective_token:
        payload = decode_access_token(effective_token)
        if payload and payload.get("sub"):
            user_id = payload.get("sub")
            result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
            return result.scalar_one_or_none()

    return None

async def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_moderator(
    user: User = Depends(get_current_user)
) -> User:
    if user.role not in (UserRole.MODERATOR, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator or Admin privileges required"
        )
    return user

async def get_current_admin(
    user: User = Depends(get_current_user)
) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user

async def verify_video_access(
    video: Video,
    user: Optional[User],
    db: AsyncSession
) -> bool:
    """
    Strict ACL & Moderation enforcement according to specification:
    1. Hidden video (moderated):
       - Accessible ONLY to video owner, moderator, or admin.
       - Blocked for ordinary viewers (403).
    2. Private video:
       - Accessible ONLY to:
         a) Video channel owner
         b) Users explicitly granted access in video_access_grants
         c) System administrator (governance)
       - NOT accessible to moderators or strangers without explicit grant.
    3. Public / Unlisted video:
       - Accessible to everyone (unlisted is just hidden from search/feed).
    """
    is_owner = False
    if user and video.channel:
        is_owner = (video.channel.user_id == user.id)

    # 1. Moderation Status Check
    if video.moderation_status == VideoModerationStatus.HIDDEN:
        is_mod_or_admin = bool(user and user.role in (UserRole.MODERATOR, UserRole.ADMIN))
        if not (is_owner or is_mod_or_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This video has been hidden by moderators for violating community guidelines."
            )

    # 2. Visibility Check
    if video.visibility == VideoVisibility.PRIVATE:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to view this private video."
            )

        # Strict specification: Private video accessible ONLY to owner or explicitly granted users
        if is_owner:
            return True

        # Check explicit grant in video_access_grants table (even admin/moderator must have explicit grant)
        grant_result = await db.execute(
            select(VideoAccessGrant).where(
                VideoAccessGrant.video_id == video.id,
                VideoAccessGrant.user_id == user.id
            )
        )
        if not grant_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. This is a private video and the owner has not granted you access."
            )

    return True
