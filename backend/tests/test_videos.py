import io
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_video_feed_and_search(client: AsyncClient, test_users: dict):
    # List public videos
    res = await client.get("/api/v1/videos")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    # Public video must be in feed
    assert any(item["id"] == test_users["public_video"].id for item in data["items"])
    # Private video must NOT be in public feed
    assert not any(item["id"] == test_users["private_video"].id for item in data["items"])
    # Hidden video must NOT be in public feed
    assert not any(item["id"] == test_users["hidden_video"].id for item in data["items"])

    # Search
    search_res = await client.get("/api/v1/videos/search?q=Public")
    assert search_res.status_code == 200
    assert any("Public" in item["title"] for item in search_res.json()["items"])

@pytest.mark.asyncio
async def test_upload_video(client: AsyncClient, test_users: dict):
    token = test_users["tokens"]["creator"]

    fake_video_bytes = b"fake mp4 video content byte sequence for testing"
    files = {
        "video_file": ("test_upload.mp4", io.BytesIO(fake_video_bytes), "video/mp4"),
    }
    data = {
        "title": "Uploaded Integration Video",
        "description": "Integration test video description",
        "visibility": "public"
    }

    res = await client.post(
        "/api/v1/videos/upload",
        headers={"Authorization": f"Bearer {token}"},
        data=data,
        files=files
    )
    assert res.status_code == 201
    res_data = res.json()
    assert res_data["title"] == "Uploaded Integration Video"
    assert res_data["is_owner"] is True
