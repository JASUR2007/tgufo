from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.channel import ChannelRead

class SubscriptionRead(BaseModel):
    id: str
    user_id: str
    channel_id: str
    created_at: datetime
    channel: ChannelRead

    model_config = ConfigDict(from_attributes=True)

class SubscriptionToggleResponse(BaseModel):
    is_subscribed: bool
    subscribers_count: int
