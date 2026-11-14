from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.user import User
from app.models.channel import Channel
from app.models.video import Video, VideoVisibility, VideoModerationStatus
from app.models.subscription import Subscription
from app.schemas.channel import ChannelRead
from app.schemas.video import VideoRead
from app.schemas.subscription import SubscriptionToggleResponse
from app.api.deps import get_current_user, get_current_user_optional

router = APIRouter(prefix="/channels", tags=["Channels"])

@router.get("/{channel_id}", response_model=ChannelRead)
async def get_channel(
    channel_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    is_subscribed = False
    if current_user:
        sub_res = await db.execute(
            select(Subscription).where(
                Subscription.user_id == current_user.id,
                Subscription.channel_id == channel.id
            )
        )
        is_subscribed = bool(sub_res.scalar_one_or_none())

    return ChannelRead(
        id=channel.id,
        user_id=channel.user_id,
        handle=channel.handle,
        name=channel.name,
        description=channel.description or "",
        avatar_url=channel.avatar_url,
        banner_url=channel.banner_url,
        subscribers_count=channel.subscribers_count,
        created_at=channel.created_at,
        is_subscribed=is_subscribed
    )

@router.get("/{channel_id}/videos", response_model=List[VideoRead])
async def list_channel_videos(
    channel_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    channel_res = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = channel_res.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    is_owner = bool(current_user and channel.user_id == current_user.id)

    stmt = select(Video).options(selectinload(Video.channel)).where(Video.channel_id == channel_id)

    if not is_owner:
        stmt = stmt.where(
            Video.visibility == VideoVisibility.PUBLIC,
            Video.moderation_status == VideoModerationStatus.APPROVED
        )

    stmt = stmt.order_by(desc(Video.created_at))
    result = await db.execute(stmt)
    videos = result.scalars().all()

    items = []
    for v in videos:
        items.append(VideoRead(
            id=v.id,
            channel_id=v.channel_id,
            title=v.title,
            description=v.description or "",
            video_url=f"/api/v1/videos/{v.id}/stream",
            thumbnail_url=f"/api/v1/videos/{v.id}/thumbnail" if v.thumbnail_filename else None,
            duration=v.duration,
            views_count=v.views_count,
            likes_count=v.likes_count,
            dislikes_count=v.dislikes_count,
            visibility=v.visibility,
            processing_status=v.processing_status,
            moderation_status=v.moderation_status,
            created_at=v.created_at,
            channel=ChannelRead.model_validate(channel),
            is_owner=is_owner
        ))
    return items

@router.post("/{channel_id}/subscribe", response_model=SubscriptionToggleResponse)
async def toggle_subscription(
    channel_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    channel_res = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = channel_res.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    if channel.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot subscribe to your own channel")

    sub_res = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.channel_id == channel.id
        )
    )
    existing = sub_res.scalar_one_or_none()

    if existing:
        await db.delete(existing)
        channel.subscribers_count = max(0, channel.subscribers_count - 1)
        is_subscribed = False
    else:
        new_sub = Subscription(user_id=current_user.id, channel_id=channel.id)
        db.add(new_sub)
        channel.subscribers_count += 1
        is_subscribed = True

    await db.commit()
    await db.refresh(channel)

    return SubscriptionToggleResponse(
        is_subscribed=is_subscribed,
        subscribers_count=channel.subscribers_count
    )
