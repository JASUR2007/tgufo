from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.moderation import ReportStatus, ModerationActionType
from app.schemas.user import UserRead
from app.schemas.video import VideoRead

class ReportCreate(BaseModel):
    video_id: str
    reason: str
    details: Optional[str] = ""

class ReportRead(BaseModel):
    id: str
    video_id: str
    reporter_id: str
    reason: str
    details: str
    status: ReportStatus
    created_at: datetime
    reporter: Optional[UserRead] = None
    video: Optional[VideoRead] = None

    model_config = ConfigDict(from_attributes=True)

class ModerationActionCreate(BaseModel):
    action: ModerationActionType
    reason: str

class ModerationActionRead(BaseModel):
    id: str
    moderator_id: str
    video_id: str
    action: ModerationActionType
    reason: str
    created_at: datetime
    moderator: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)
