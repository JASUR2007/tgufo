from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserRead

class ChannelBase(BaseModel):
    handle: str
    name: str
    description: Optional[str] = ""
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None

class ChannelCreate(ChannelBase):
    pass

class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None

class ChannelRead(ChannelBase):
    id: str
    user_id: str
    subscribers_count: int
    created_at: datetime
    is_subscribed: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)
