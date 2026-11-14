from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import generate_uuid, get_utc_now

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_id = Column(String(36), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "channel_id", name="uq_user_channel_subscription"),
    )

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    channel = relationship("Channel", back_populates="subscribers")
