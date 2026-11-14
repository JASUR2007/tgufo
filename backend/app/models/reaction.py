from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import generate_uuid, get_utc_now

class ReactionType(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"

class VideoReaction(Base):
    __tablename__ = "video_reactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reaction_type = Column(SQLEnum(ReactionType), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("video_id", "user_id", name="uq_video_user_reaction"),
    )

    # Relationships
    video = relationship("Video", back_populates="reactions")
    user = relationship("User", back_populates="reactions")
