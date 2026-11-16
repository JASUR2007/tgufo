import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_comments_and_reactions(client: AsyncClient, test_users: dict):
    video = test_users["public_video"]
    tokens = test_users["tokens"]

    # 1. Post a comment
    comment_res = await client.post(
        f"/api/v1/videos/{video.id}/comments",
        headers={"Authorization": f"Bearer {tokens['viewer']}"},
        json={"content": "Great architectural test!"}
    )
    assert comment_res.status_code == 201
    comment_id = comment_res.json()["id"]
    assert comment_res.json()["content"] == "Great architectural test!"

    # 2. List comments
    list_res = await client.get(f"/api/v1/videos/{video.id}/comments")
    assert list_res.status_code == 200
    assert any(c["id"] == comment_id for c in list_res.json())

    # 3. Like the video
    like_res = await client.post(
        f"/api/v1/videos/{video.id}/reactions",
        headers={"Authorization": f"Bearer {tokens['viewer']}"},
        json={"reaction_type": "like"}
    )
    assert like_res.status_code == 200
    assert like_res.json()["user_reaction"] == "like"
    assert like_res.json()["likes_count"] == 1

    # 4. Toggle like again -> becomes neutral
    unlike_res = await client.post(
        f"/api/v1/videos/{video.id}/reactions",
        headers={"Authorization": f"Bearer {tokens['viewer']}"},
        json={"reaction_type": "like"}
    )
    assert unlike_res.status_code == 200
    assert unlike_res.json()["user_reaction"] is None
    assert unlike_res.json()["likes_count"] == 0

    # 5. Switch to dislike
    dislike_res = await client.post(
        f"/api/v1/videos/{video.id}/reactions",
        headers={"Authorization": f"Bearer {tokens['viewer']}"},
        json={"reaction_type": "dislike"}
    )
    assert dislike_res.status_code == 200
    assert dislike_res.json()["user_reaction"] == "dislike"
    assert dislike_res.json()["dislikes_count"] == 1

    # 6. Delete comment
    del_res = await client.delete(
        f"/api/v1/comments/{comment_id}",
        headers={"Authorization": f"Bearer {tokens['viewer']}"}
    )
    assert del_res.status_code == 204
