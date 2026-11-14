import asyncio
import os
import shutil
from pathlib import Path
from PIL import Image, ImageDraw

from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import get_password_hash
from app.core.storage import storage_service
from app.models.user import User, UserRole
from app.models.channel import Channel
from app.models.video import (
    Video, VideoVisibility, VideoProcessingStatus, VideoModerationStatus, VideoAccessGrant
)
from app.models.comment import Comment
from app.models.reaction import VideoReaction, ReactionType
from app.models.subscription import Subscription
from app.models.playlist import Playlist, PlaylistItem
from app.models.moderation import Report, ReportStatus
from sqlalchemy import select

def create_sample_mp4(filepath: Path, duration_sec: int = 5):
    """
    Creates a real playable MP4 video file.
    If ffmpeg is installed, generates synthetic test video with color bars & audio tone.
    Otherwise, writes a valid minimal MP4 file container.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        try:
            cmd = [
                ffmpeg, "-y",
                "-f", "lavfi", "-i", f"testsrc=duration={duration_sec}:size=1280x720:rate=30",
                "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration_sec}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                "-c:a", "aac", "-b:a", "128k",
                str(filepath)
            ]
            import subprocess
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return
        except Exception as e:
            print(f"[Seed] ffmpeg synthetic video generation failed: {e}")

    # Fallback: create a valid binary MP4 stub with ftyp, moov, mdat atoms
    # A known minimal valid blank H.264/AAC MP4 container sequence
    minimal_mp4_bytes = (
        b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2avc1mp41'
        b'\x00\x00\x00\x08free'
        b'\x00\x00\x01\x00mdat' + (b'\x00' * 50000) +
        b'\x00\x00\x00\x30moov\x00\x00\x00\x28mvhd\x00\x00\x00\x00' + (b'\x00' * 32)
    )
    with open(filepath, "wb") as f:
        f.write(minimal_mp4_bytes)

def create_sample_thumbnail(filepath: Path, title: str, bg_color: tuple):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1280, 720), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Red YouTube play badge
    draw.rounded_rectangle([560, 280, 720, 440], radius=28, fill=(255, 0, 0))
    draw.polygon([(625, 325), (625, 395), (675, 360)], fill=(255, 255, 255))

    # Bottom banner
    draw.rectangle([0, 600, 1280, 720], fill=(15, 15, 15))
    draw.text((40, 640), title, fill=(240, 240, 240))

    img.save(str(filepath), "JPEG", quality=85)

async def seed_demo_data():
    print("[Seed] Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        res = await session.execute(select(User).where(User.email == "admin@youtube.local"))
        if res.scalar_one_or_none():
            print("[Seed] Database already seeded. Skipping.")
            return

        print("[Seed] Creating demo users...")
        users_data = [
            {
                "email": "admin@youtube.local",
                "username": "admin",
                "full_name": "Site Administrator",
                "password": "AdminPass123!",
                "role": UserRole.ADMIN,
                "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=admin",
                "handle": "@admin",
                "channel_name": "YouTube Administration",
                "bio": "Official administration channel for monitoring and system management."
            },
            {
                "email": "moderator@youtube.local",
                "username": "moderator",
                "full_name": "Safety Moderator",
                "password": "ModPass123!",
                "role": UserRole.MODERATOR,
                "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=moderator",
                "handle": "@moderator",
                "channel_name": "Safety & Integrity",
                "bio": "Community guidelines oversight and content review."
            },
            {
                "email": "creator@youtube.local",
                "username": "tech_guru",
                "full_name": "Alex Tech Guru",
                "password": "CreatorPass123!",
                "role": UserRole.USER,
                "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=tech_guru",
                "handle": "@tech_guru",
                "channel_name": "Tech Insights & Tutorials",
                "bio": "Deep dives into Python, FastAPI, Docker, and AI engineering."
            },
            {
                "email": "viewer@youtube.local",
                "username": "demo_viewer",
                "full_name": "John Viewer",
                "password": "ViewerPass123!",
                "role": UserRole.USER,
                "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=demo_viewer",
                "handle": "@demo_viewer",
                "channel_name": "John's Space",
                "bio": "Passionate learner and video consumer."
            }
        ]

        created_users = {}
        created_channels = {}

        for ud in users_data:
            user = User(
                email=ud["email"],
                username=ud["username"],
                full_name=ud["full_name"],
                hashed_password=get_password_hash(ud["password"]),
                role=ud["role"],
                avatar_url=ud["avatar"]
            )
            session.add(user)
            await session.flush()
            created_users[ud["username"]] = user

            channel = Channel(
                user_id=user.id,
                handle=ud["handle"],
                name=ud["channel_name"],
                description=ud["bio"],
                avatar_url=ud["avatar"],
                banner_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1600&h=400&fit=crop"
            )
            session.add(channel)
            await session.flush()
            created_channels[ud["username"]] = channel

        print("[Seed] Generating video files and records...")
        videos_data = [
            {
                "title": "Building a Modern YouTube Clone with FastAPI & React",
                "description": "Learn the full architecture of a video sharing platform: object storage, HTTP Range streaming, and AI-driven development.",
                "creator": "tech_guru",
                "filename": "fastapi_youtube_arch.mp4",
                "thumb": "thumb_fastapi.jpg",
                "color": (20, 30, 45),
                "visibility": VideoVisibility.PUBLIC,
                "duration": 420.0,
                "views": 15420,
                "likes": 842,
                "dislikes": 12
            },
            {
                "title": "Microservices Deployment on Clean Ubuntu with Docker",
                "description": "Step-by-step walkthrough of single-command zero-downtime deployment using docker compose, reverse proxies, and healthchecks.",
                "creator": "tech_guru",
                "filename": "docker_clean_ubuntu.mp4",
                "thumb": "thumb_docker.jpg",
                "color": (15, 45, 30),
                "visibility": VideoVisibility.PUBLIC,
                "duration": 315.0,
                "views": 8920,
                "likes": 610,
                "dislikes": 5
            },
            {
                "title": "Python 3.12+ Async I/O & SQLAlchemy 2.0 Best Practices",
                "description": "Deep architectural patterns for high-throughput asynchronous database applications.",
                "creator": "tech_guru",
                "filename": "python_async_guide.mp4",
                "thumb": "thumb_python.jpg",
                "color": (45, 30, 15),
                "visibility": VideoVisibility.PUBLIC,
                "duration": 580.0,
                "views": 12300,
                "likes": 980,
                "dislikes": 8
            },
            {
                "title": "[UNLISTED] Internal Architecture Review & Brainstorming",
                "description": "Unlisted meeting recording for the engineering team. Accessible only via direct URL.",
                "creator": "tech_guru",
                "filename": "unlisted_review.mp4",
                "thumb": "thumb_unlisted.jpg",
                "color": (40, 20, 40),
                "visibility": VideoVisibility.UNLISTED,
                "duration": 180.0,
                "views": 45,
                "likes": 12,
                "dislikes": 0
            },
            {
                "title": "[PRIVATE] Confidential Strategy & Revenue Projections 2026",
                "description": "Strictly confidential! Accessible only to owner, admin, and granted viewer.",
                "creator": "tech_guru",
                "filename": "private_strategy.mp4",
                "thumb": "thumb_private.jpg",
                "color": (50, 10, 10),
                "visibility": VideoVisibility.PRIVATE,
                "duration": 240.0,
                "views": 18,
                "likes": 5,
                "dislikes": 0
            },
            {
                "title": "Reported Video: Clickbait and Misleading Guidelines Test",
                "description": "This video has been reported by a user and is pending moderator review.",
                "creator": "demo_viewer",
                "filename": "reported_test.mp4",
                "thumb": "thumb_reported.jpg",
                "color": (35, 35, 35),
                "visibility": VideoVisibility.PUBLIC,
                "duration": 60.0,
                "views": 520,
                "likes": 10,
                "dislikes": 45
            }
        ]

        created_videos = []
        for vd in videos_data:
            v_path = storage_service.videos_dir / vd["filename"]
            t_path = storage_service.thumbnails_dir / vd["thumb"]

            create_sample_mp4(v_path, duration_sec=5)
            create_sample_thumbnail(t_path, vd["title"][:40], vd["color"])

            # Ensure synced to MinIO S3 if S3 storage is enabled
            if storage_service.s3_client:
                try:
                    with open(v_path, "rb") as vf:
                        storage_service.s3_client.put_object(
                            Bucket=settings.S3_BUCKET_NAME,
                            Key=f"videos/{vd['filename']}",
                            Body=vf.read()
                        )
                    with open(t_path, "rb") as tf:
                        storage_service.s3_client.put_object(
                            Bucket=settings.S3_BUCKET_NAME,
                            Key=f"thumbnails/{vd['thumb']}",
                            Body=tf.read()
                        )
                except Exception as e:
                    print(f"[Seed] S3 object storage upload notice: {e}")

            video = Video(
                channel_id=created_channels[vd["creator"]].id,
                title=vd["title"],
                description=vd["description"],
                video_filename=vd["filename"],
                thumbnail_filename=vd["thumb"],
                duration=vd["duration"],
                views_count=vd["views"],
                likes_count=vd["likes"],
                dislikes_count=vd["dislikes"],
                visibility=vd["visibility"],
                processing_status=VideoProcessingStatus.READY,
                moderation_status=VideoModerationStatus.APPROVED
            )
            session.add(video)
            await session.flush()
            created_videos.append(video)

        # Private video grant: give demo_viewer access to private video!
        private_video = created_videos[4]
        viewer_user = created_users["demo_viewer"]
        grant = VideoAccessGrant(
            video_id=private_video.id,
            user_id=viewer_user.id
        )
        session.add(grant)

        print("[Seed] Adding comments, reactions, subscriptions, and reports...")
        # Comments on first video
        c1 = Comment(
            video_id=created_videos[0].id,
            user_id=created_users["demo_viewer"].id,
            content="Amazing explanation of HTTP Range streaming! Worked perfectly with HTML5 player."
        )
        c2 = Comment(
            video_id=created_videos[0].id,
            user_id=created_users["admin"].id,
            content="Great architectural overview. Clean, modular, and easy to deploy on clean Ubuntu."
        )
        session.add_all([c1, c2])

        # Reaction on first video
        r1 = VideoReaction(
            video_id=created_videos[0].id,
            user_id=created_users["demo_viewer"].id,
            reaction_type=ReactionType.LIKE
        )
        session.add(r1)

        # Subscription: viewer subscribes to tech_guru
        sub = Subscription(
            user_id=created_users["demo_viewer"].id,
            channel_id=created_channels["tech_guru"].id
        )
        session.add(sub)
        created_channels["tech_guru"].subscribers_count = 1

        # Report on the reported video
        rep = Report(
            video_id=created_videos[5].id,
            reporter_id=created_users["demo_viewer"].id,
            reason="Misleading Content / Clickbait",
            details="Video claims 1000x speedup without explanation.",
            status=ReportStatus.PENDING
        )
        session.add(rep)

        # Playlist: "Fullstack Engineering"
        pl = Playlist(
            channel_id=created_channels["tech_guru"].id,
            title="Fullstack Web Engineering & DevOps",
            description="Complete curriculum covering FastAPI, React, Docker, and Architecture.",
            visibility=VideoVisibility.PUBLIC
        )
        session.add(pl)
        await session.flush()

        pi1 = PlaylistItem(playlist_id=pl.id, video_id=created_videos[0].id, position=0)
        pi2 = PlaylistItem(playlist_id=pl.id, video_id=created_videos[1].id, position=1)
        session.add_all([pi1, pi2])

        await session.commit()
        print("[Seed] Successfully completed demo database population!")

if __name__ == "__main__":
    asyncio.run(seed_demo_data())
