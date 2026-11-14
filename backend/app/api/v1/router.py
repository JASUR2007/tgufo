from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.videos import router as videos_router
from app.api.v1.reactions import router as reactions_router
from app.api.v1.comments import router as comments_router
from app.api.v1.channels import router as channels_router
from app.api.v1.playlists import router as playlists_router
from app.api.v1.moderation import router as moderation_router
from app.api.v1.users import router as users_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(videos_router)
api_v1_router.include_router(reactions_router)
api_v1_router.include_router(comments_router)
api_v1_router.include_router(channels_router)
api_v1_router.include_router(playlists_router)
api_v1_router.include_router(moderation_router)
api_v1_router.include_router(users_router)
