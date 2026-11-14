from enum import Enum
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import generate_uuid, get_utc_now
from app.models.video import VideoVisibility

class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    channel_id = Column(String(36), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True, default="")
    visibility = Column(SQLEnum(VideoVisibility), default=VideoVisibility.PUBLIC, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships
    channel = relationship("Channel", back_populates="playlists")
    items = relationship("PlaylistItem", back_populates="playlist", cascade="all, delete-orphan", order_by="PlaylistItem.position")

class PlaylistItem(Base):
    __tablename__ = "playlist_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    playlist_id = Column(String(36), ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    position = Column(Integer, default=0, nullable=False)
    added_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("playlist_id", "video_id", name="uq_playlist_video"),
    )

    # Relationships
    playlist = relationship("Playlist", back_populates="items")
    video = relationship("Video", back_populates="playlist_items")
