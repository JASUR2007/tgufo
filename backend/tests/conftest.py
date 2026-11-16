import asyncio
import os
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User, UserRole
from app.models.channel import Channel
from app.models.video import Video, VideoVisibility, VideoProcessingStatus, VideoModerationStatus, VideoAccessGrant
from app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///./test_youtube.db"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_test_db():
    settings.STORAGE_TYPE = "local"
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()
    if os.path.exists("./test_youtube.db"):
        os.remove("./test_youtube.db")

@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def test_users(db_session: AsyncSession):
    suffix = uuid.uuid4().hex[:6]
    admin = User(
        email=f"admin_{suffix}@test.com",
        username=f"admin_{suffix}",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN
    )
    mod = User(
        email=f"mod_{suffix}@test.com",
        username=f"mod_{suffix}",
        hashed_password=get_password_hash("password123"),
        role=UserRole.MODERATOR
    )
    creator = User(
        email=f"creator_{suffix}@test.com",
        username=f"creator_{suffix}",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER
    )
    viewer = User(
        email=f"viewer_{suffix}@test.com",
        username=f"viewer_{suffix}",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER
    )
    stranger = User(
        email=f"stranger_{suffix}@test.com",
        username=f"stranger_{suffix}",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER
    )
    db_session.add_all([admin, mod, creator, viewer, stranger])
    await db_session.flush()

    # Channels
    channel = Channel(
        user_id=creator.id,
        handle=f"@creator_{suffix}",
        name="Creator Channel"
    )
    db_session.add(channel)
    await db_session.flush()

    # Videos
    public_video = Video(
        channel_id=channel.id,
        title=f"Public Test Video {suffix}",
        video_filename=f"public_{suffix}.mp4",
        visibility=VideoVisibility.PUBLIC,
        processing_status=VideoProcessingStatus.READY,
        moderation_status=VideoModerationStatus.APPROVED
    )
    private_video = Video(
        channel_id=channel.id,
        title=f"Private Test Video {suffix}",
        video_filename=f"private_{suffix}.mp4",
        visibility=VideoVisibility.PRIVATE,
        processing_status=VideoProcessingStatus.READY,
        moderation_status=VideoModerationStatus.APPROVED
    )
    hidden_video = Video(
        channel_id=channel.id,
        title=f"Hidden Test Video {suffix}",
        video_filename=f"hidden_{suffix}.mp4",
        visibility=VideoVisibility.PUBLIC,
        processing_status=VideoProcessingStatus.READY,
        moderation_status=VideoModerationStatus.HIDDEN
    )
    db_session.add_all([public_video, private_video, hidden_video])
    await db_session.flush()

    # Grant viewer access to private video
    grant = VideoAccessGrant(video_id=private_video.id, user_id=viewer.id)
    db_session.add(grant)
    await db_session.commit()

    return {
        "admin": admin,
        "moderator": mod,
        "creator": creator,
        "viewer": viewer,
        "stranger": stranger,
        "channel": channel,
        "public_video": public_video,
        "private_video": private_video,
        "hidden_video": hidden_video,
        "tokens": {
            "admin": create_access_token(admin.id),
            "moderator": create_access_token(mod.id),
            "creator": create_access_token(creator.id),
            "viewer": create_access_token(viewer.id),
            "stranger": create_access_token(stranger.id)
        }
    }

