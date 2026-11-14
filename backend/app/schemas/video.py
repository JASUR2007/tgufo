from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.video import VideoVisibility, VideoProcessingStatus, VideoModerationStatus
from app.schemas.channel import ChannelRead
from app.schemas.user import UserRead

class VideoBase(BaseModel):
    title: str
    description: Optional[str] = ""
    visibility: VideoVisibility = VideoVisibility.PUBLIC

class VideoCreate(VideoBase):
    pass

class VideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[VideoVisibility] = None

class VideoAccessGrantCreate(BaseModel):
    user_identifier: str  # username or email

class VideoAccessGrantRead(BaseModel):
    id: str
    video_id: str
    user_id: str
    user: Optional[UserRead] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class VideoRead(VideoBase):
    id: str
    channel_id: str
    video_url: str
    thumbnail_url: Optional[str] = None
    duration: float
    views_count: int
    likes_count: int
    dislikes_count: int
    processing_status: VideoProcessingStatus
    moderation_status: VideoModerationStatus
    created_at: datetime
    channel: Optional[ChannelRead] = None
    user_reaction: Optional[str] = None  # "like", "dislike", or None
    is_owner: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)

class VideoListResponse(BaseModel):
    items: List[VideoRead]
    total: int
    page: int
    page_size: int
