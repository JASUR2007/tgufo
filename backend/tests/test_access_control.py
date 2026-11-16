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

    # 8. NEGATIVE SECURITY AUDIT: Media Ticket CANNOT be used as general account Bearer token
    # 8.1 Ticket passed as Authorization: Bearer <ticket> to /auth/me -> MUST be 401 Unauthorized
    res_ticket_me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {viewer_ticket}"}
    )
    assert res_ticket_me.status_code == 401

    # 8.2 Ticket passed as Bearer to upload -> MUST be 401 Unauthorized
    res_ticket_upload = await client.post(
        "/api/v1/videos/upload",
        headers={"Authorization": f"Bearer {viewer_ticket}"},
        data={"title": "Unauthorized"}
    )
    assert res_ticket_upload.status_code == 401

    # 8.3 Ticket passed as Bearer to video update (PATCH) -> MUST be 401 Unauthorized
    res_ticket_patch = await client.patch(
        f"/api/v1/videos/{video.id}",
        headers={"Authorization": f"Bearer {viewer_ticket}"},
        json={"title": "Hacked Title"}
    )
    assert res_ticket_patch.status_code == 401

    # 8.4 Ticket for video A used on other video B -> MUST be rejected (cross-video isolation)
    other_video = test_users["public_video"]
    from app.core.security import verify_media_ticket, decode_access_token
    assert verify_media_ticket(viewer_ticket, other_video.id) is None
    assert decode_access_token(viewer_ticket) is None

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

@pytest.mark.asyncio
async def test_private_video_comments_and_reactions_acl(client: AsyncClient, test_users: dict):
    """
    Ensure private video strictly protects comments and reactions:
    - Anonymous: 401 Unauthorized (no comments revealed, cannot post)
    - Stranger: 403 Forbidden (no comments revealed, cannot post, cannot react)
    - Admin (without explicit grant): 403 Forbidden (strictly owner + granted)
    - Owner: 201 Created (post comment), 200 OK (view comments, react)
    - Granted viewer: 201 Created (post comment), 200 OK (view comments, react)
    """
    video = test_users["private_video"]
    tokens = test_users["tokens"]

    # 1. Owner posts comment -> 201 Created
    res_owner_comment = await client.post(
        f"/api/v1/videos/{video.id}/comments",
        headers={"Authorization": f"Bearer {tokens['creator']}"},
        json={"content": "Owner confidential note"}
    )
    assert res_owner_comment.status_code == 201
    assert res_owner_comment.json()["content"] == "Owner confidential note"

    # 2. Anonymous attempts to view comments -> 401 Unauthorized (comments NOT revealed)
    res_anon_comments = await client.get(f"/api/v1/videos/{video.id}/comments")
    assert res_anon_comments.status_code == 401

    # 3. Anonymous attempts to post comment -> 401 Unauthorized
    res_anon_post = await client.post(
        f"/api/v1/videos/{video.id}/comments",
        json={"content": "Anonymous intrusion attempt"}
    )
    assert res_anon_post.status_code == 401

    # 4. Stranger attempts to view comments -> 403 Forbidden (comments NOT revealed)
    res_stranger_comments = await client.get(
        f"/api/v1/videos/{video.id}/comments",
        headers={"Authorization": f"Bearer {tokens['stranger']}"}
    )
    assert res_stranger_comments.status_code == 403

    # 5. Stranger attempts to post comment -> 403 Forbidden (no comment created)
    res_stranger_post = await client.post(
        f"/api/v1/videos/{video.id}/comments",
        headers={"Authorization": f"Bearer {tokens['stranger']}"},
        json={"content": "Stranger comment attempt"}
    )
    assert res_stranger_post.status_code == 403

    # 6. Stranger attempts to toggle reaction -> 403 Forbidden (no reaction recorded)
    res_stranger_react = await client.post(
        f"/api/v1/videos/{video.id}/reactions",
        headers={"Authorization": f"Bearer {tokens['stranger']}"},
        json={"reaction_type": "like"}
    )
    assert res_stranger_react.status_code == 403

    # 7. Stranger attempts to check reaction state -> 403 Forbidden
    res_stranger_react_me = await client.get(
        f"/api/v1/videos/{video.id}/reactions/me",
        headers={"Authorization": f"Bearer {tokens['stranger']}"}
    )
    assert res_stranger_react_me.status_code == 403

    # 8. Admin (without explicit grant) attempts to view/post comment -> 403 Forbidden
    res_admin_comments = await client.get(
        f"/api/v1/videos/{video.id}/comments",
        headers={"Authorization": f"Bearer {tokens['admin']}"}
    )
    assert res_admin_comments.status_code == 403

    res_admin_post = await client.post(
        f"/api/v1/videos/{video.id}/comments",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
        json={"content": "Admin bypass attempt"}
    )
    assert res_admin_post.status_code == 403

    # 9. Granted viewer posts comment -> 201 Created
    res_viewer_post = await client.post(
        f"/api/v1/videos/{video.id}/comments",
        headers={"Authorization": f"Bearer {tokens['viewer']}"},
        json={"content": "Granted viewer allowed comment"}
    )
    assert res_viewer_post.status_code == 201

    # 10. Granted viewer lists comments -> 200 OK (sees comments)
    res_viewer_comments = await client.get(
        f"/api/v1/videos/{video.id}/comments",
        headers={"Authorization": f"Bearer {tokens['viewer']}"}
    )
    assert res_viewer_comments.status_code == 200
    comments_list = res_viewer_comments.json()
    assert len(comments_list) == 2

    # 11. Granted viewer toggles reaction -> 200 OK
    res_viewer_react = await client.post(
        f"/api/v1/videos/{video.id}/reactions",
        headers={"Authorization": f"Bearer {tokens['viewer']}"},
        json={"reaction_type": "like"}
    )
    assert res_viewer_react.status_code == 200
    assert res_viewer_react.json()["likes_count"] == 1

    # 12. Owner toggles reaction -> 200 OK
    res_owner_react = await client.post(
        f"/api/v1/videos/{video.id}/reactions",
        headers={"Authorization": f"Bearer {tokens['creator']}"},
        json={"reaction_type": "like"}
    )
    assert res_owner_react.status_code == 200
    assert res_owner_react.json()["likes_count"] == 2

