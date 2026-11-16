import pytest
from httpx import AsyncClient
from app.core.storage import storage_service

@pytest.mark.asyncio
async def test_public_video_accessible(client: AsyncClient, test_users: dict):
    video = test_users["public_video"]
    # Anonymous request
    res = await client.get(f"/api/v1/videos/{video.id}")
    assert res.status_code == 200
    assert res.json()["id"] == video.id

@pytest.mark.asyncio
async def test_private_video_access_control(client: AsyncClient, test_users: dict):
    video = test_users["private_video"]
    tokens = test_users["tokens"]

    # Ensure dummy media file exists in storage for stream testing
    v_path = storage_service.videos_dir / video.video_filename
    if not v_path.exists():
        v_path.write_bytes(b"dummy video content for streaming test")

    # 1. Anonymous access -> 401 Unauthorized
    res_anon = await client.get(f"/api/v1/videos/{video.id}")
    assert res_anon.status_code == 401

    # 2. Stranger access -> 403 Forbidden
    res_stranger = await client.get(
        f"/api/v1/videos/{video.id}",
        headers={"Authorization": f"Bearer {tokens['stranger']}"}
    )
    assert res_stranger.status_code == 403
    assert "Access denied" in res_stranger.json()["detail"]

    # 3. Moderator access WITHOUT grant -> 403 Forbidden (strictly owner + granted)
    res_mod = await client.get(
        f"/api/v1/videos/{video.id}",
        headers={"Authorization": f"Bearer {tokens['moderator']}"}
    )
    assert res_mod.status_code == 403
    assert "Access denied" in res_mod.json()["detail"]

    # 4. Granted viewer access via Header -> 200 OK
    res_viewer = await client.get(
        f"/api/v1/videos/{video.id}",
        headers={"Authorization": f"Bearer {tokens['viewer']}"}
    )
    assert res_viewer.status_code == 200
    assert res_viewer.json()["id"] == video.id

    # 5. Owner access -> 200 OK
    res_owner = await client.get(
        f"/api/v1/videos/{video.id}",
        headers={"Authorization": f"Bearer {tokens['creator']}"}
    )
    assert res_owner.status_code == 200

    # 6. Admin access WITHOUT owner grant -> 403 Forbidden (strictly owner + granted viewers per spec)
    res_admin = await client.get(
        f"/api/v1/videos/{video.id}",
        headers={"Authorization": f"Bearer {tokens['admin']}"}
    )
    assert res_admin.status_code == 403
    assert "Access denied" in res_admin.json()["detail"]

    # 7. Scoped media ticket generation & stream authentication
    # Owner gets media ticket
    res_ticket_owner = await client.post(
        f"/api/v1/videos/{video.id}/ticket",
        headers={"Authorization": f"Bearer {tokens['creator']}"}
    )
    assert res_ticket_owner.status_code == 200
    owner_ticket = res_ticket_owner.json()["ticket"]

    # Granted viewer gets media ticket
    res_ticket_viewer = await client.post(
        f"/api/v1/videos/{video.id}/ticket",
        headers={"Authorization": f"Bearer {tokens['viewer']}"}
    )
    assert res_ticket_viewer.status_code == 200
    viewer_ticket = res_ticket_viewer.json()["ticket"]

    # Stranger cannot get media ticket -> 403
    res_ticket_stranger = await client.post(
        f"/api/v1/videos/{video.id}/ticket",
        headers={"Authorization": f"Bearer {tokens['stranger']}"}
    )
    assert res_ticket_stranger.status_code == 403

    # Browser <video src="/api/v1/videos/{id}/stream?ticket=..."> stream authentication
    res_stream_ticket = await client.get(
        f"/api/v1/videos/{video.id}/stream?ticket={viewer_ticket}"
    )
    assert res_stream_ticket.status_code in (200, 206)
    # Cache-control for private media must be private/no-store
    assert "no-store" in res_stream_ticket.headers.get("cache-control", "")

    # With stranger token query param -> 403 Forbidden
    res_stream_stranger = await client.get(
        f"/api/v1/videos/{video.id}/stream?token={tokens['stranger']}"
    )
    assert res_stream_stranger.status_code == 403

    # Without token/ticket query param -> 401 Unauthorized
    res_stream_anon = await client.get(
        f"/api/v1/videos/{video.id}/stream"
    )
    assert res_stream_anon.status_code == 401

@pytest.mark.asyncio
async def test_thumbnail_acl_protection(client: AsyncClient, test_users: dict):
    video = test_users["private_video"]
    tokens = test_users["tokens"]

    # Ensure thumbnail file exists in storage
    video.thumbnail_filename = f"thumb_{video.id}.jpg"
    t_path = storage_service.thumbnails_dir / video.thumbnail_filename
    t_path.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIFdummythumbnailbytes")

    # Anonymous access to private thumbnail -> 401
    res_anon = await client.get(f"/api/v1/videos/{video.id}/thumbnail")
    assert res_anon.status_code == 401

    # Stranger access to private thumbnail -> 403
    res_stranger = await client.get(
        f"/api/v1/videos/{video.id}/thumbnail?token={tokens['stranger']}"
    )
    assert res_stranger.status_code == 403

    # Granted user access to private thumbnail with query ticket -> 200
    res_ticket = await client.post(
        f"/api/v1/videos/{video.id}/ticket",
        headers={"Authorization": f"Bearer {tokens['viewer']}"}
    )
    viewer_ticket = res_ticket.json()["ticket"]

    res_granted = await client.get(
        f"/api/v1/videos/{video.id}/thumbnail?ticket={viewer_ticket}"
    )
    assert res_granted.status_code == 200
    # Private thumbnail Cache-Control MUST be private/no-store
    assert "no-store" in res_granted.headers.get("cache-control", "")

    # Public video thumbnail check -> Cache-Control: public
    pub_video = test_users["public_video"]
    pub_video.thumbnail_filename = f"thumb_{pub_video.id}.jpg"
    (storage_service.thumbnails_dir / pub_video.thumbnail_filename).write_bytes(b"\xff\xd8\xff\xe0JFIFpublic")
    res_pub = await client.get(f"/api/v1/videos/{pub_video.id}/thumbnail")
    assert res_pub.status_code == 200
    assert "public" in res_pub.headers.get("cache-control", "")

@pytest.mark.asyncio
async def test_hidden_moderated_video(client: AsyncClient, test_users: dict):
    video = test_users["hidden_video"]
    tokens = test_users["tokens"]

    # Normal viewer cannot view hidden video -> 403 Forbidden
    res_viewer = await client.get(
        f"/api/v1/videos/{video.id}",
        headers={"Authorization": f"Bearer {tokens['viewer']}"}
    )
    assert res_viewer.status_code == 403
    assert "hidden by moderators" in res_viewer.json()["detail"]

    # Moderator can view -> 200 OK
    res_mod = await client.get(
        f"/api/v1/videos/{video.id}",
        headers={"Authorization": f"Bearer {tokens['moderator']}"}
    )
    assert res_mod.status_code == 200
