from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.user import User
from app.models.video import Video, VideoModerationStatus
from app.models.moderation import Report, ReportStatus, ModerationAction, ModerationActionType
from app.schemas.moderation import (
    ReportCreate, ReportRead, ModerationActionCreate, ModerationActionRead
)
from app.schemas.user import UserRead
from app.schemas.video import VideoRead
from app.api.deps import get_current_user, get_current_moderator, verify_video_access

router = APIRouter(prefix="/moderation", tags=["Moderation"])

@router.post("/reports", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def submit_report(
    report_in: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    video_res = await db.execute(
        select(Video).options(selectinload(Video.channel)).where(Video.id == report_in.video_id)
    )
    video = video_res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Strict access verification: cannot report private video without access
    await verify_video_access(video, current_user, db)

    report = Report(
        video_id=report_in.video_id,
        reporter_id=current_user.id,
        reason=report_in.reason,
        details=report_in.details or "",
        status=ReportStatus.PENDING
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return ReportRead(
        id=report.id,
        video_id=report.video_id,
        reporter_id=report.reporter_id,
        reason=report.reason,
        details=report.details,
        status=report.status,
        created_at=report.created_at,
        reporter=UserRead.model_validate(current_user)
    )

@router.get("/reports", response_model=List[ReportRead])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_moderator: User = Depends(get_current_moderator)
):
    stmt = (
        select(Report)
        .options(
            selectinload(Report.reporter),
            selectinload(Report.video).selectinload(Video.channel)
        )
        .order_by(desc(Report.created_at))
    )
    result = await db.execute(stmt)
    reports = result.scalars().all()

    items = []
    for r in reports:
        video_read = None
        if r.video:
            video_read = VideoRead(
                id=r.video.id,
                channel_id=r.video.channel_id,
                title=r.video.title,
                description=r.video.description or "",
                video_url=f"/api/v1/videos/{r.video.id}/stream",
                thumbnail_url=f"/api/v1/videos/{r.video.id}/thumbnail" if r.video.thumbnail_filename else None,
                duration=r.video.duration,
                views_count=r.video.views_count,
                likes_count=r.video.likes_count,
                dislikes_count=r.video.dislikes_count,
                visibility=r.video.visibility,
                processing_status=r.video.processing_status,
                moderation_status=r.video.moderation_status,
                created_at=r.video.created_at
            )
        items.append(ReportRead(
            id=r.id,
            video_id=r.video_id,
            reporter_id=r.reporter_id,
            reason=r.reason,
            details=r.details,
            status=r.status,
            created_at=r.created_at,
            reporter=UserRead.model_validate(r.reporter) if r.reporter else None,
            video=video_read
        ))
    return items

@router.post("/videos/{video_id}/hide", response_model=ModerationActionRead)
async def hide_video(
    video_id: str,
    action_in: ModerationActionCreate,
    current_moderator: User = Depends(get_current_moderator),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    video.moderation_status = VideoModerationStatus.HIDDEN

    # Create audit record
    action = ModerationAction(
        moderator_id=current_moderator.id,
        video_id=video.id,
        action=ModerationActionType.HIDE,
        reason=action_in.reason
    )
    db.add(action)

    # Update associated reports to reviewed
    reports_res = await db.execute(select(Report).where(Report.video_id == video_id))
    for rep in reports_res.scalars().all():
        rep.status = ReportStatus.REVIEWED

    await db.commit()
    await db.refresh(action)

    return ModerationActionRead(
        id=action.id,
        moderator_id=action.moderator_id,
        video_id=action.video_id,
        action=action.action,
        reason=action.reason,
        created_at=action.created_at,
        moderator=UserRead.model_validate(current_moderator)
    )

@router.post("/videos/{video_id}/restore", response_model=ModerationActionRead)
async def restore_video(
    video_id: str,
    action_in: ModerationActionCreate,
    current_moderator: User = Depends(get_current_moderator),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    video.moderation_status = VideoModerationStatus.APPROVED

    action = ModerationAction(
        moderator_id=current_moderator.id,
        video_id=video.id,
        action=ModerationActionType.RESTORE,
        reason=action_in.reason
    )
    db.add(action)
    await db.commit()
    await db.refresh(action)

    return ModerationActionRead(
        id=action.id,
        moderator_id=action.moderator_id,
        video_id=action.video_id,
        action=action.action,
        reason=action.reason,
        created_at=action.created_at,
        moderator=UserRead.model_validate(current_moderator)
    )

@router.get("/actions", response_model=List[ModerationActionRead])
async def list_moderation_actions(
    db: AsyncSession = Depends(get_db),
    current_moderator: User = Depends(get_current_moderator)
):
    stmt = (
        select(ModerationAction)
        .options(selectinload(ModerationAction.moderator))
        .order_by(desc(ModerationAction.created_at))
    )
    result = await db.execute(stmt)
    actions = result.scalars().all()
    return [
        ModerationActionRead(
            id=a.id,
            moderator_id=a.moderator_id,
            video_id=a.video_id,
            action=a.action,
            reason=a.reason,
            created_at=a.created_at,
            moderator=UserRead.model_validate(a.moderator) if a.moderator else None
        )
        for a in actions
    ]
