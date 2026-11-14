from enum import Enum
from sqlalchemy import Column, String, Integer, BigInteger, Float, Text, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import generate_uuid, get_utc_now

class VideoVisibility(str, Enum):
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"

class VideoProcessingStatus(str, Enum):
    UPLOADING = "uploading"
    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class VideoModerationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    HIDDEN = "hidden"

class Video(Base):
    __tablename__ = "videos"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    channel_id = Column(String(36), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True, default="")
    video_filename = Column(String(255), nullable=False)
    thumbnail_filename = Column(String(255), nullable=True)
    duration = Column(Float, default=0.0, nullable=False)
    views_count = Column(BigInteger, default=0, nullable=False)
    likes_count = Column(Integer, default=0, nullable=False)
    dislikes_count = Column(Integer, default=0, nullable=False)
    visibility = Column(SQLEnum(VideoVisibility), default=VideoVisibility.PUBLIC, nullable=False, index=True)
    processing_status = Column(SQLEnum(VideoProcessingStatus), default=VideoProcessingStatus.UPLOADING, nullable=False, index=True)
    moderation_status = Column(SQLEnum(VideoModerationStatus), default=VideoModerationStatus.APPROVED, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships
    channel = relationship("Channel", back_populates="videos")
    comments = relationship("Comment", back_populates="video", cascade="all, delete-orphan")
    reactions = relationship("VideoReaction", back_populates="video", cascade="all, delete-orphan")
    access_grants = relationship("VideoAccessGrant", back_populates="video", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="video", cascade="all, delete-orphan")
    playlist_items = relationship("PlaylistItem", back_populates="video", cascade="all, delete-orphan")

class VideoAccessGrant(Base):
    __tablename__ = "video_access_grants"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("video_id", "user_id", name="uq_video_user_grant"),
    )

    # Relationships
    video = relationship("Video", back_populates="access_grants")
    user = relationship("User", back_populates="access_grants")
