import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_media_ticket
from app.core.storage import storage_service
from app.services.video_processing import video_processing_service
from app.models.user import User, UserRole
from app.models.channel import Channel
from app.models.video import (
    Video, VideoVisibility, VideoProcessingStatus, VideoModerationStatus, VideoAccessGrant
)
from app.models.reaction import VideoReaction
from app.schemas.video import (
    VideoRead, VideoListResponse, VideoUpdate, VideoAccessGrantCreate, VideoAccessGrantRead
)
from app.schemas.channel import ChannelRead
from app.schemas.user import UserRead
from app.api.deps import get_current_user, get_current_user_optional, get_media_user_optional, verify_video_access

router = APIRouter(prefix="/videos", tags=["Videos"])

async def process_video_background(video_id: str, video_filename: str, title: str):
    video_path = storage_service.videos_dir / video_filename
    duration = await video_processing_service.get_video_duration(video_path)
    
    thumb_name = f"thumb_{uuid.uuid4().hex[:12]}.jpg"
    await video_processing_service.generate_thumbnail(video_path, thumb_name, title=title)

    try:
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if video:
                video.duration = duration
                if not video.thumbnail_filename:
                    video.thumbnail_filename = thumb_name
                video.processing_status = VideoProcessingStatus.READY
                await session.commit()
    except Exception as e:
        print(f"[process_video_background] Background DB update skipped or handled: {e}")

def build_video_read(video: Video, current_user: Optional[User] = None, user_reaction: Optional[str] = None) -> VideoRead:
    channel_read = None
    if video.channel:
        channel_read = ChannelRead(
            id=video.channel.id,
            user_id=video.channel.user_id,
            handle=video.channel.handle,
            name=video.channel.name,
            description=video.channel.description or "",
            avatar_url=video.channel.avatar_url,
            banner_url=video.channel.banner_url,
            subscribers_count=video.channel.subscribers_count,
            created_at=video.channel.created_at
        )

    is_owner = False
    if current_user and video.channel:
        is_owner = (video.channel.user_id == current_user.id)

    video_url = f"/api/v1/videos/{video.id}/stream"
    thumb_url = f"/api/v1/videos/{video.id}/thumbnail" if video.thumbnail_filename else None

    return VideoRead(
        id=video.id,
        channel_id=video.channel_id,
        title=video.title,
        description=video.description or "",
        video_url=video_url,
        thumbnail_url=thumb_url,
        duration=video.duration,
        views_count=video.views_count,
        likes_count=video.likes_count,
        dislikes_count=video.dislikes_count,
        visibility=video.visibility,
        processing_status=video.processing_status,
        moderation_status=video.moderation_status,
        created_at=video.created_at,
        channel=channel_read,
        user_reaction=user_reaction,
        is_owner=is_owner
    )

@router.get("", response_model=VideoListResponse)
async def list_videos(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    offset = (page - 1) * page_size
    stmt = (
        select(Video)
        .options(selectinload(Video.channel))
        .where(
            Video.visibility == VideoVisibility.PUBLIC,
            Video.moderation_status == VideoModerationStatus.APPROVED
        )
    )

    if search:
        search_filter = or_(
            Video.title.ilike(f"%{search}%"),
            Video.description.ilike(f"%{search}%")
        )
        stmt = stmt.where(search_filter)

    stmt = stmt.order_by(desc(Video.created_at)).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    videos = result.scalars().all()

    items = [build_video_read(v, current_user) for v in videos]
    return VideoListResponse(
        items=items,
        total=len(items),
        page=page,
        page_size=page_size
    )

@router.post("/upload", response_model=VideoRead, status_code=status.HTTP_201_CREATED)
async def upload_video(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: Optional[str] = Form(""),
    visibility: VideoVisibility = Form(VideoVisibility.PUBLIC),
    video_file: UploadFile = File(...),
    thumbnail_file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify user channel exists
    channel_res = await db.execute(select(Channel).where(Channel.user_id == current_user.id))
    channel = channel_res.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=400, detail="User channel does not exist")

    # Read video content and save
    video_content = await video_file.read()
    video_ext = Path(video_file.filename or "video.mp4").suffix or ".mp4"
    video_filename = f"{uuid.uuid4().hex}{video_ext}"
    await storage_service.save_file(video_content, "videos", video_filename)

    # Save thumbnail if provided
    thumbnail_filename = None
    if thumbnail_file and thumbnail_file.filename:
        thumb_content = await thumbnail_file.read()
        thumb_ext = Path(thumbnail_file.filename).suffix or ".jpg"
        thumbnail_filename = f"thumb_{uuid.uuid4().hex}{thumb_ext}"
        await storage_service.save_file(thumb_content, "thumbnails", thumbnail_filename)

    video = Video(
        channel_id=channel.id,
        title=title,
        description=description or "",
        video_filename=video_filename,
        thumbnail_filename=thumbnail_filename,
        duration=0.0,
        visibility=visibility,
        processing_status=VideoProcessingStatus.QUEUED,
        moderation_status=VideoModerationStatus.APPROVED
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    # Load channel relation
    video.channel = channel

    # Enqueue background processing (ffmpeg probe + thumbnail if not uploaded)
    background_tasks.add_task(
        process_video_background,
        video_id=video.id,
        video_filename=video_filename,
        title=title
    )

    return build_video_read(video, current_user)

@router.get("/search", response_model=VideoListResponse)
async def search_videos(
    q: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    offset = (page - 1) * page_size
    stmt = (
        select(Video)
        .options(selectinload(Video.channel))
        .where(
            Video.visibility == VideoVisibility.PUBLIC,
            Video.moderation_status == VideoModerationStatus.APPROVED,
            or_(
                Video.title.ilike(f"%{q}%"),
                Video.description.ilike(f"%{q}%")
            )
        )
        .order_by(desc(Video.views_count), desc(Video.created_at))
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    videos = result.scalars().all()

    items = [build_video_read(v, current_user) for v in videos]
    return VideoListResponse(items=items, total=len(items), page=page, page_size=page_size)

@router.get("/{video_id}", response_model=VideoRead)
async def get_video(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    stmt = (
        select(Video)
        .options(selectinload(Video.channel))
        .where(Video.id == video_id)
    )
    result = await db.execute(stmt)
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Access control verification
    await verify_video_access(video, current_user, db)

    # Increment views
    video.views_count += 1
    await db.commit()

    # User reaction check
    user_reaction = None
    if current_user:
        reaction_res = await db.execute(
            select(VideoReaction).where(
                VideoReaction.video_id == video.id,
                VideoReaction.user_id == current_user.id
            )
        )
        r = reaction_res.scalar_one_or_none()
        if r:
            user_reaction = r.reaction_type.value

    return build_video_read(video, current_user, user_reaction)

@router.patch("/{video_id}", response_model=VideoRead)
async def update_video(
    video_id: str,
    update_data: VideoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Video).options(selectinload(Video.channel)).where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    is_owner = (video.channel and video.channel.user_id == current_user.id)
    is_admin = (current_user.role == UserRole.ADMIN)

    if not (is_owner or is_admin):
        raise HTTPException(status_code=403, detail="Not authorized to edit this video")

    if update_data.title is not None:
        video.title = update_data.title
    if update_data.description is not None:
        video.description = update_data.description
    if update_data.visibility is not None:
        video.visibility = update_data.visibility

    await db.commit()
    await db.refresh(video)
    return build_video_read(video, current_user)

@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Video).options(selectinload(Video.channel)).where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    is_owner = (video.channel and video.channel.user_id == current_user.id)
    is_admin = (current_user.role == UserRole.ADMIN)

    if not (is_owner or is_admin):
        raise HTTPException(status_code=403, detail="Not authorized to delete this video")

    await db.delete(video)
    await db.commit()
    return None

@router.post("/{video_id}/ticket")
async def generate_media_ticket_endpoint(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a short-lived (15 min) media ticket scoped strictly to this video.
    Allows HTML5 <video> and <img> to authenticate securely without exposing account access tokens in URLs.
    """
    result = await db.execute(
        select(Video).options(selectinload(Video.channel)).where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Verify that this user is authorized to view this video
    await verify_video_access(video, current_user, db)

    ticket = create_media_ticket(user_id=current_user.id, video_id=str(video_id), expires_minutes=15)
    return {
        "ticket": ticket,
        "video_id": str(video_id),
        "expires_in_seconds": 900
    }

@router.get("/{video_id}/stream")
async def stream_video(
    video_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_media_user_optional)
):
    result = await db.execute(
        select(Video).options(selectinload(Video.channel)).where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Strict Access control verification (owner, granted users, or public)
    await verify_video_access(video, current_user, db)

    is_public = bool(
        video.visibility == VideoVisibility.PUBLIC and
        video.moderation_status == VideoModerationStatus.APPROVED
    )

    range_header = request.headers.get("range")
    return storage_service.create_range_streaming_response(
        folder="videos",
        filename=video.video_filename,
        range_header=range_header,
        media_type="video/mp4",
        is_public=is_public
    )

@router.get("/{video_id}/thumbnail")
async def get_thumbnail(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_media_user_optional)
):
    result = await db.execute(
        select(Video).options(selectinload(Video.channel)).where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()
    if not video or not video.thumbnail_filename:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    # Strict Access control check: private/hidden thumbnails require authorization
    await verify_video_access(video, current_user, db)

    is_public = bool(
        video.visibility == VideoVisibility.PUBLIC and
        video.moderation_status == VideoModerationStatus.APPROVED
    )

    return storage_service.get_thumbnail_response(video.thumbnail_filename, is_public=is_public)

# Private Video Grants Endpoints
@router.get("/{video_id}/grants", response_model=List[VideoAccessGrantRead])
async def list_grants(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Video).options(selectinload(Video.channel)).where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video.channel.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only video owner can view access grants")

    grants_res = await db.execute(
        select(VideoAccessGrant)
        .options(selectinload(VideoAccessGrant.user))
        .where(VideoAccessGrant.video_id == video_id)
    )
    return grants_res.scalars().all()

@router.post("/{video_id}/grants", response_model=VideoAccessGrantRead, status_code=status.HTTP_201_CREATED)
async def add_grant(
    video_id: str,
    grant_in: VideoAccessGrantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Video).options(selectinload(Video.channel)).where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video.channel.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only video owner can manage access grants")

    target_user_res = await db.execute(
        select(User).where(
            or_(
                User.username == grant_in.user_identifier,
                User.email == grant_in.user_identifier
            )
        )
    )
    target_user = target_user_res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    # Check if grant already exists
    existing = await db.execute(
        select(VideoAccessGrant).where(
            VideoAccessGrant.video_id == video_id,
            VideoAccessGrant.user_id == target_user.id
        )
    )
    grant = existing.scalar_one_or_none()
    if not grant:
        grant = VideoAccessGrant(video_id=video_id, user_id=target_user.id)
        db.add(grant)
        await db.commit()
        await db.refresh(grant)

    grant.user = target_user
    return grant

@router.delete("/{video_id}/grants/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_grant(
    video_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Video).options(selectinload(Video.channel)).where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video.channel.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only video owner can revoke access")

    grant_res = await db.execute(
        select(VideoAccessGrant).where(
            VideoAccessGrant.video_id == video_id,
            VideoAccessGrant.user_id == user_id
        )
    )
    grant = grant_res.scalar_one_or_none()
    if grant:
        await db.delete(grant)
        await db.commit()
    return None
