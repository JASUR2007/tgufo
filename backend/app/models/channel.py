from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import generate_uuid, get_utc_now

class Channel(Base):
    __tablename__ = "channels"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    handle = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True, default="")
    avatar_url = Column(String(500), nullable=True)
    banner_url = Column(String(500), nullable=True)
    subscribers_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="channel")
    videos = relationship("Video", back_populates="channel", cascade="all, delete-orphan")
    playlists = relationship("Playlist", back_populates="channel", cascade="all, delete-orphan")
    subscribers = relationship("Subscription", back_populates="channel", cascade="all, delete-orphan")
