from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.video import Video
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentRead
from app.schemas.user import UserRead
from app.api.deps import get_current_user, get_current_user_optional

router = APIRouter(tags=["Comments"])

@router.get("/videos/{video_id}/comments", response_model=List[CommentRead])
async def list_comments(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    stmt = (
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.video_id == video_id)
        .order_by(desc(Comment.created_at))
    )
    result = await db.execute(stmt)
    comments = result.scalars().all()

    response = []
    for c in comments:
        can_delete = False
        if current_user:
            can_delete = (c.user_id == current_user.id or current_user.role in (UserRole.MODERATOR, UserRole.ADMIN))
        
        response.append(CommentRead(
            id=c.id,
            video_id=c.video_id,
            user_id=c.user_id,
            content=c.content,
            created_at=c.created_at,
            user=UserRead.model_validate(c.user) if c.user else None,
            can_delete=can_delete
        ))
    return response

@router.post("/videos/{video_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_comment(
    video_id: str,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    video_res = await db.execute(select(Video).where(Video.id == video_id))
    if not video_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Video not found")

    comment = Comment(
        video_id=video_id,
        user_id=current_user.id,
        content=comment_in.content
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return CommentRead(
        id=comment.id,
        video_id=comment.video_id,
        user_id=comment.user_id,
        content=comment.content,
        created_at=comment.created_at,
        user=UserRead.model_validate(current_user),
        can_delete=True
    )

@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    can_delete = (comment.user_id == current_user.id or current_user.role in (UserRole.MODERATOR, UserRole.ADMIN))
    if not can_delete:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    await db.delete(comment)
    await db.commit()
    return None
