from typing import Optional
from pydantic import BaseModel
from app.models.reaction import ReactionType

class ReactionCreate(BaseModel):
    reaction_type: ReactionType

class ReactionStatus(BaseModel):
    user_reaction: Optional[ReactionType] = None
    likes_count: int
    dislikes_count: int
