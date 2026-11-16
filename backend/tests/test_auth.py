import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # Registration
    reg_payload = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "SecurePassword123!",
        "full_name": "New User"
    }
    res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["username"] == "newuser"

    # Duplicate registration should fail
    res_dup = await client.post("/api/v1/auth/register", json=reg_payload)
    assert res_dup.status_code == 400

    # Login
    login_payload = {
        "email": "newuser@example.com",
        "password": "SecurePassword123!"
    }
    res_login = await client.post("/api/v1/auth/login", json=login_payload)
    assert res_login.status_code == 200
    token = res_login.json()["access_token"]

    # Access /me
    res_me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "newuser@example.com"

@pytest.mark.asyncio
async def test_invalid_login(client: AsyncClient):
    res = await client.post("/api/v1/auth/login", json={"email": "wrong@example.com", "password": "wrong"})
    assert res.status_code == 401
