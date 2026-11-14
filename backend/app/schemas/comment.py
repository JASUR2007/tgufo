from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserRead

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class CommentRead(CommentBase):
    id: str
    video_id: str
    user_id: str
    created_at: datetime
    user: Optional[UserRead] = None
    can_delete: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)
