from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.user import User
from app.models.video import Video
from app.models.reaction import VideoReaction, ReactionType
from app.schemas.reaction import ReactionCreate, ReactionStatus
from app.api.deps import get_current_user, verify_video_access

router = APIRouter(prefix="/videos/{video_id}/reactions", tags=["Reactions"])

@router.post("", response_model=ReactionStatus)
async def toggle_reaction(
    video_id: str,
    reaction_in: ReactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    video_res = await db.execute(
        select(Video).options(selectinload(Video.channel)).where(Video.id == video_id)
    )
    video = video_res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Strict access verification: private/hidden videos require proper authorization
    await verify_video_access(video, current_user, db)

    reaction_res = await db.execute(
        select(VideoReaction).where(
            VideoReaction.video_id == video_id,
            VideoReaction.user_id == current_user.id
        )
    )
    existing = reaction_res.scalar_one_or_none()

    current_state = None
    if existing:
        if existing.reaction_type == reaction_in.reaction_type:
            # Clicking same reaction again -> removes reaction (neutral)
            if existing.reaction_type == ReactionType.LIKE:
                video.likes_count = max(0, video.likes_count - 1)
            else:
                video.dislikes_count = max(0, video.dislikes_count - 1)
            await db.delete(existing)
            current_state = None
        else:
            # Switching from like to dislike or vice versa
            if existing.reaction_type == ReactionType.LIKE:
                video.likes_count = max(0, video.likes_count - 1)
                video.dislikes_count += 1
            else:
                video.dislikes_count = max(0, video.dislikes_count - 1)
                video.likes_count += 1
            existing.reaction_type = reaction_in.reaction_type
            current_state = reaction_in.reaction_type
    else:
        # First time reaction
        new_reaction = VideoReaction(
            video_id=video_id,
            user_id=current_user.id,
            reaction_type=reaction_in.reaction_type
        )
        db.add(new_reaction)
        if reaction_in.reaction_type == ReactionType.LIKE:
            video.likes_count += 1
        else:
            video.dislikes_count += 1
        current_state = reaction_in.reaction_type

    await db.commit()
    await db.refresh(video)

    return ReactionStatus(
        user_reaction=current_state,
        likes_count=video.likes_count,
        dislikes_count=video.dislikes_count
    )

@router.get("/me", response_model=ReactionStatus)
async def get_my_reaction(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    video_res = await db.execute(
        select(Video).options(selectinload(Video.channel)).where(Video.id == video_id)
    )
    video = video_res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Strict access verification: private/hidden videos require proper authorization
    await verify_video_access(video, current_user, db)

    reaction_res = await db.execute(
        select(VideoReaction).where(
            VideoReaction.video_id == video_id,
            VideoReaction.user_id == current_user.id
        )
    )
    existing = reaction_res.scalar_one_or_none()

    return ReactionStatus(
        user_reaction=existing.reaction_type if existing else None,
        likes_count=video.likes_count,
        dislikes_count=video.dislikes_count
    )
