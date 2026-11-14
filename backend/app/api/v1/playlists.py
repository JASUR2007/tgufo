from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.user import User
from app.models.channel import Channel
from app.models.video import Video
from app.models.playlist import Playlist, PlaylistItem
from app.schemas.playlist import (
    PlaylistCreate, PlaylistRead, PlaylistItemCreate, PlaylistItemRead
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/playlists", tags=["Playlists"])

@router.get("/channel/{channel_id}", response_model=List[PlaylistRead])
async def list_channel_playlists(
    channel_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Playlist)
        .options(
            selectinload(Playlist.items).selectinload(PlaylistItem.video)
        )
        .where(Playlist.channel_id == channel_id)
        .order_by(desc(Playlist.created_at))
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=PlaylistRead, status_code=status.HTTP_201_CREATED)
async def create_playlist(
    playlist_in: PlaylistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    channel_res = await db.execute(select(Channel).where(Channel.user_id == current_user.id))
    channel = channel_res.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=400, detail="Channel not found")

    playlist = Playlist(
        channel_id=channel.id,
        title=playlist_in.title,
        description=playlist_in.description,
        visibility=playlist_in.visibility
    )
    db.add(playlist)
    await db.commit()
    await db.refresh(playlist)
    playlist.items = []
    return playlist

@router.get("/{playlist_id}", response_model=PlaylistRead)
async def get_playlist(
    playlist_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Playlist)
        .options(
            selectinload(Playlist.items).selectinload(PlaylistItem.video)
        )
        .where(Playlist.id == playlist_id)
    )
    result = await db.execute(stmt)
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist

@router.post("/{playlist_id}/items", response_model=PlaylistItemRead, status_code=status.HTTP_201_CREATED)
async def add_item_to_playlist(
    playlist_id: str,
    item_in: PlaylistItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    playlist_res = await db.execute(
        select(Playlist).options(selectinload(Playlist.channel)).where(Playlist.id == playlist_id)
    )
    playlist = playlist_res.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    if playlist.channel.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this playlist")

    video_res = await db.execute(select(Video).where(Video.id == item_in.video_id))
    if not video_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Video not found")

    item = PlaylistItem(
        playlist_id=playlist_id,
        video_id=item_in.video_id,
        position=len(playlist.items)
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

@router.delete("/{playlist_id}/items/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_playlist(
    playlist_id: str,
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    playlist_res = await db.execute(
        select(Playlist).options(selectinload(Playlist.channel)).where(Playlist.id == playlist_id)
    )
    playlist = playlist_res.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    if playlist.channel.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this playlist")

    item_res = await db.execute(
        select(PlaylistItem).where(
            PlaylistItem.playlist_id == playlist_id,
            PlaylistItem.video_id == video_id
        )
    )
    item = item_res.scalar_one_or_none()
    if item:
        await db.delete(item)
        await db.commit()
    return None
