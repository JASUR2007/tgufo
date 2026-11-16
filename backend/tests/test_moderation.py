import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_moderation_flow(client: AsyncClient, test_users: dict):
    video = test_users["public_video"]
    tokens = test_users["tokens"]

    # 1. Normal user submits report
    report_res = await client.post(
        "/api/v1/moderation/reports",
        headers={"Authorization": f"Bearer {tokens['viewer']}"},
        json={
            "video_id": video.id,
            "reason": "Copyright Infringement",
            "details": "Contains unauthorized music."
        }
    )
    assert report_res.status_code == 201
    assert report_res.json()["reason"] == "Copyright Infringement"

    # 2. Non-moderator attempts to view reports -> 403 Forbidden
    unauth_list = await client.get(
        "/api/v1/moderation/reports",
        headers={"Authorization": f"Bearer {tokens['viewer']}"}
    )
    assert unauth_list.status_code == 403

    # 3. Moderator views reports -> 200 OK
    mod_list = await client.get(
        "/api/v1/moderation/reports",
        headers={"Authorization": f"Bearer {tokens['moderator']}"}
    )
    assert mod_list.status_code == 200
    assert len(mod_list.json()) >= 1

    # 4. Moderator hides video
    hide_res = await client.post(
        f"/api/v1/moderation/videos/{video.id}/hide",
        headers={"Authorization": f"Bearer {tokens['moderator']}"},
        json={"action": "hide", "reason": "Violates copyright guidelines."}
    )
    assert hide_res.status_code == 200
    assert hide_res.json()["action"] == "hide"

    # 5. Video is now hidden for ordinary viewers
    check_video = await client.get(
        f"/api/v1/videos/{video.id}",
        headers={"Authorization": f"Bearer {tokens['viewer']}"}
    )
    assert check_video.status_code == 403

    # 6. Moderator restores video
    restore_res = await client.post(
        f"/api/v1/moderation/videos/{video.id}/restore",
        headers={"Authorization": f"Bearer {tokens['moderator']}"},
        json={"action": "restore", "reason": "Claim resolved."}
    )
    assert restore_res.status_code == 200

    # 7. Audit log contains both actions
    actions_res = await client.get(
        "/api/v1/moderation/actions",
        headers={"Authorization": f"Bearer {tokens['moderator']}"}
    )
    assert actions_res.status_code == 200
    assert len(actions_res.json()) >= 2
