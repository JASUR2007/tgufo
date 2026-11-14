from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import generate_uuid, get_utc_now

class ReportStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    DISMISSED = "dismissed"

class ModerationActionType(str, Enum):
    HIDE = "hide"
    RESTORE = "restore"
    DELETE = "delete"

class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    reporter_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(String(100), nullable=False)
    details = Column(Text, nullable=True, default="")
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.PENDING, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    video = relationship("Video", back_populates="reports")
    reporter = relationship("User", back_populates="reports")

class ModerationAction(Base):
    __tablename__ = "moderation_actions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    moderator_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(SQLEnum(ModerationActionType), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    moderator = relationship("User")
    video = relationship("Video")
