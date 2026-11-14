from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.video import VideoVisibility
from app.schemas.video import VideoRead

class PlaylistBase(BaseModel):
    title: str
    description: Optional[str] = ""
    visibility: VideoVisibility = VideoVisibility.PUBLIC

class PlaylistCreate(PlaylistBase):
    pass

class PlaylistItemCreate(BaseModel):
    video_id: str

class PlaylistItemRead(BaseModel):
    id: str
    playlist_id: str
    video_id: str
    position: int
    added_at: datetime
    video: Optional[VideoRead] = None

    model_config = ConfigDict(from_attributes=True)

class PlaylistRead(PlaylistBase):
    id: str
    channel_id: str
    created_at: datetime
    items: List[PlaylistItemRead] = []

    model_config = ConfigDict(from_attributes=True)
