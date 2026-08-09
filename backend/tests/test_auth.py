"""认证流程冒烟测试：登录 → 携带 token 访问受保护接口 → 无 token 被拦截。"""
import pytest


@pytest.mark.asyncio
async def test_login_with_valid_credentials(client):
    """admin/admin123 登录应返回 access_token 与 refresh_token。"""
    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


@pytest.mark.asyncio
async def test_login_with_wrong_password(client):
    """错误密码应返回 401。"""
    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "wrong-password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_token(client):
    """登录后用 token 访问 /auth/me 应返回当前用户。"""
    login = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login.json()["access_token"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["username"] == "admin"
    assert body["is_superuser"] is True


@pytest.mark.asyncio
async def test_me_without_token_rejected(client):
    """无 token 访问受保护接口应返回 401。"""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
