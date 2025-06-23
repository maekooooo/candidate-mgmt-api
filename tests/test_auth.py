# tests/test_auth.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from main import app
from app.core.db_client import DBClient
from app.core import security

@pytest_asyncio.fixture
async def client():
    """
    Create an httpx AsyncClient bound to our ASGI app using ASGITransport.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

@pytest.fixture(autouse=True)
def stub_db(monkeypatch):
    """
    Replace DBClient methods so we never touch real Postgres.
    """
    # Stub out signup: echo back an “inserted” user dict
    async def fake_create_entry(self, table_name: str, data: dict):
        return {
            "id": "00000000-0000-0000-0000-000000000001",
            "email": data["email"],
            "hashed_password": data["hashed_password"],
            "is_active": data.get("is_active", True),
        }
    monkeypatch.setattr(DBClient, "create_table_entry", fake_create_entry)

    # Stub out login lookup: only recognize “test@example.com”
    async def fake_query(self, table_name: str, filters=None, single_row=False, **kwargs):
        if filters and filters.get("email") == "test@example.com":
            return {
                "id": "00000000-0000-0000-0000-000000000001",
                "email": "test@example.com",
                # Pre-hash “secret” so verify_password will succeed
                "hashed_password": security.hash_password("test-pw"),
                "is_active": True,
            }
        return None
    monkeypatch.setattr(DBClient, "query_table_data", fake_query)


# ----- Tests -----

@pytest.mark.asyncio
async def test_signup_and_login_flow(client: AsyncClient):
    # 1) signup
    resp = await client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "test-pw"}
    )
    assert resp.status_code == 201, resp.text

    # 2) login success
    resp2 = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "test-pw"}
    )
    assert resp2.status_code == 200, resp2.text
    body = resp2.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"

    # 3) login failure (wrong password)
    resp3 = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrong-pw"}
    )
    assert resp3.status_code == 401, resp3.text
    body3 = resp3.json()
    assert body3["detail"] == "Incorrect email or password"

    # 4) login failure (unknown email)
    resp4 = await client.post(
        "/auth/login",
        json={"email": "unknown@example.com", "password": "test-pw"}
    )
    assert resp4.status_code == 401, resp4.text
    body4 = resp4.json()
    assert body4["detail"] == "Incorrect email or password"
