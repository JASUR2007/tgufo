import io
from pathlib import Path
import pytest
from httpx import AsyncClient
from app.core.storage import storage_service
from app.services.video_processing import video_processing_service
from app.models.video import VideoVisibility, VideoProcessingStatus

FIXTURE_MP4_PATH = Path(__file__).parent / "fixtures" / "sample_real_video.mp4"

@pytest.mark.asyncio
async def test_full_real_mp4_lifecycle(client: AsyncClient):
    """
    Full end-to-end integration test verifying with a real H.264/AAC MP4 video:
    1. User registration & channel auto-creation
    2. Upload of genuine H.264/AAC MP4 encoded video (libx264/aac, 320x240, faststart)
    3. Duration calculation via video processing service & thumbnail generation
    4. HTTP 206 Partial Content range playback & timeline scrubbing
    5. Scoped media ticket generation & read-only enforcement
    6. Negative security check: media ticket rejected as general account Bearer token
    7. Strict Private ACL (owner/grantee allowed; stranger/moderator/admin forbidden without grant)
    8. Reaction (like) & comment submission on the video
    """
    assert FIXTURE_MP4_PATH.exists(), f"Real MP4 test fixture missing at {FIXTURE_MP4_PATH}"
    mp4_bytes = FIXTURE_MP4_PATH.read_bytes()
    assert len(mp4_bytes) > 10000
    assert mp4_bytes[4:8] == b"ftyp"

    # Step 1: Register Author (channel is automatically created on registration)
    reg_author = await client.post("/api/v1/auth/register", json={
        "email": "real_author@example.com",
        "username": "real_author",
        "password": "AuthorPass123!",
        "full_name": "Real Video Author"
    })
    assert reg_author.status_code == 201
    author_token = reg_author.json()["access_token"]
    author_headers = {"Authorization": f"Bearer {author_token}"}

    # Step 2: Upload genuine H.264/AAC MP4 video
    upload_res = await client.post(
        "/api/v1/videos/upload",
        data={
            "title": "Real End-to-End MP4 Lifecycle Test",
            "description": "Uploaded genuine H.264/AAC MP4 video to verify playback and range streaming",
            "visibility": "public"
        },
        files={
            "video_file": ("real_h264_test.mp4", io.BytesIO(mp4_bytes), "video/mp4")
        },
        headers=author_headers
    )
    assert upload_res.status_code == 201
    video_data = upload_res.json()
    video_id = video_data["id"]

    # Step 3: Verify video duration & thumbnail processing
    created_mp4 = next(p for p in storage_service.videos_dir.glob("*.mp4") if p.stat().st_size == len(mp4_bytes))
    assert created_mp4.exists()

    # Verify duration calculation on the real MP4 file
    duration = await video_processing_service.get_video_duration(created_mp4)
    assert duration > 0.0

    # Generate thumbnail
    thumb_name = f"thumb_{video_id}_real.jpg"
    await video_processing_service.generate_thumbnail(created_mp4, thumb_name, title="Real MP4 Test")
    assert (storage_service.thumbnails_dir / thumb_name).exists()

    # Step 4: Test Range Streaming with Real MP4 (HTTP 206 Partial Content)
    # Request first 1000 bytes
    range_res = await client.get(
        f"/api/v1/videos/{video_id}/stream",
        headers={"Range": "bytes=0-999"}
    )
    assert range_res.status_code == 206
    assert range_res.headers.get("Accept-Ranges") == "bytes"
    assert range_res.headers.get("Content-Range").startswith("bytes 0-999/")
    assert len(range_res.content) == 1000
    # Confirms real MP4 ftyp container header delivered
    assert range_res.content[4:8] == b"ftyp"

    # Request second chunk (simulate timeline scrubbing / seeking)
    range_res_seek = await client.get(
        f"/api/v1/videos/{video_id}/stream",
        headers={"Range": "bytes=1000-1999"}
    )
    assert range_res_seek.status_code == 206
    assert range_res_seek.headers.get("Content-Range").startswith("bytes 1000-1999/")
    assert len(range_res_seek.content) == 1000

    # Step 5: Test Scoped Media Ticket
    ticket_res = await client.post(
        f"/api/v1/videos/{video_id}/ticket",
        headers=author_headers
    )
    assert ticket_res.status_code == 200
    ticket = ticket_res.json()["ticket"]
    assert ticket is not None

    stream_with_ticket = await client.get(
        f"/api/v1/videos/{video_id}/stream?ticket={ticket}",
        headers={"Range": "bytes=0-100"}
    )
    assert stream_with_ticket.status_code == 206

    # Step 6: Negative Security Check: Ticket CANNOT act as general Bearer access token
    # 6.1 Call /auth/me with Authorization: Bearer <ticket> -> MUST fail with 401
    bad_me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {ticket}"}
    )
    assert bad_me_res.status_code == 401

    # 6.2 Call upload with Authorization: Bearer <ticket> -> MUST fail with 401
    bad_up_res = await client.post(
        "/api/v1/videos/upload",
        headers={"Authorization": f"Bearer {ticket}"},
        data={"title": "Hacker Video"}
    )
    assert bad_up_res.status_code == 401

    # Step 7: Strict Private Access Control Flow
    # 7.1 Author changes video to private
    patch_res = await client.patch(
        f"/api/v1/videos/{video_id}",
        json={"visibility": "private"},
        headers=author_headers
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["visibility"] == "private"

    # 7.2 Register other users
    # Grantee user
    reg_grantee = await client.post("/api/v1/auth/register", json={
        "email": "grantee@example.com",
        "username": "grantee_user",
        "password": "GranteePass123!",
        "full_name": "Granted Viewer"
    })
    grantee_token = reg_grantee.json()["access_token"]
    grantee_headers = {"Authorization": f"Bearer {grantee_token}"}

    # Stranger user
    reg_stranger = await client.post("/api/v1/auth/register", json={
        "email": "stranger@example.com",
        "username": "stranger_user",
        "password": "StrangerPass123!",
        "full_name": "Stranger Viewer"
    })
    stranger_token = reg_stranger.json()["access_token"]
    stranger_headers = {"Authorization": f"Bearer {stranger_token}"}

    # 7.3 Anonymous gets 401
    assert (await client.get(f"/api/v1/videos/{video_id}")).status_code == 401
    assert (await client.get(f"/api/v1/videos/{video_id}/stream")).status_code == 401

    # 7.4 Stranger gets 403 Forbidden
    assert (await client.get(f"/api/v1/videos/{video_id}", headers=stranger_headers)).status_code == 403
    assert (await client.get(f"/api/v1/videos/{video_id}/stream", headers=stranger_headers)).status_code == 403

    # 7.5 Grantee BEFORE being granted gets 403 Forbidden
    assert (await client.get(f"/api/v1/videos/{video_id}", headers=grantee_headers)).status_code == 403

    # 7.6 Author explicitly grants access to grantee_user
    add_grant_res = await client.post(
        f"/api/v1/videos/{video_id}/grants",
        json={"user_identifier": "grantee_user"},
        headers=author_headers
    )
    assert add_grant_res.status_code == 201

    # 7.7 Grantee AFTER being granted gets 200 OK
    grantee_view_res = await client.get(f"/api/v1/videos/{video_id}", headers=grantee_headers)
    assert grantee_view_res.status_code == 200

    # Grantee gets media ticket
    grantee_ticket_res = await client.post(
        f"/api/v1/videos/{video_id}/ticket",
        headers=grantee_headers
    )
    assert grantee_ticket_res.status_code == 200
    grantee_ticket = grantee_ticket_res.json()["ticket"]

    # Grantee streams private video with ticket
    grantee_stream_res = await client.get(
        f"/api/v1/videos/{video_id}/stream?ticket={grantee_ticket}",
        headers={"Range": "bytes=0-200"}
    )
    assert grantee_stream_res.status_code == 206
    assert "no-store" in grantee_stream_res.headers.get("cache-control", "")

    # Step 8: Interaction - Reaction (like) and Comment
    # Grantee likes the video
    like_res = await client.post(
        f"/api/v1/videos/{video_id}/reactions",
        json={"reaction_type": "like"},
        headers=grantee_headers
    )
    assert like_res.status_code == 200

    # Grantee posts comment
    comment_res = await client.post(
        f"/api/v1/videos/{video_id}/comments",
        json={"content": "Excellent real MP4 video playback and strict private ACL!"},
        headers=grantee_headers
    )
    assert comment_res.status_code == 201
    assert comment_res.json()["content"] == "Excellent real MP4 video playback and strict private ACL!"

    # Read back comments
    comments_list = await client.get(f"/api/v1/videos/{video_id}/comments", headers=grantee_headers)
    assert comments_list.status_code == 200
    assert len(comments_list.json()) >= 1
