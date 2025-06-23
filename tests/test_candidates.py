# tests/test_candidate.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from main import app
from app.core.db_client import DBClient
from app.core.security import get_current_user

# Bypass the real JWT auth
@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: {"sub": "00000000-0000-0000-0000-000000000001"}

# Stub out DBClient so we never hit Postgres
@pytest.fixture(autouse=True)
def stub_db(monkeypatch):
    # fake in‐memory “table”
    record1 = {
        "id": "11111111-1111-1111-1111-111111111111",
        "full_name": "Alice",
        "email": "alice@example.com",
        "phone": None,
        "skills": ["python"],
        "created_at": None,
        "updated_at": None,
    }
    record2 = {
        "id": "22222222-2222-2222-2222-222222222222",
        "full_name": "Bob",
        "email": "bob@example.com",
        "phone": None,
        "skills": ["java"],
        "created_at": None,
        "updated_at": None,
    }

    async def fake_create(self, table_name: str, data: dict):
        assert table_name == "candidates"
        # echo back with a new id
        return {**data, "id": record1["id"]}

    async def fake_query(self,
                         table_name: str,
                         filters=None,
                         single_row=False,
                         limit=None,
                         offset=None):
        assert table_name == "candidates"
        # list endpoints
        if not single_row:
            results = [record1, record2]
            if filters and filters.get("skills"):
                return [r for r in results if filters["skills"] in r["skills"]]
            return results

        # single_row endpoints
        if filters and filters.get("id") == record1["id"]:
            return record1
        return None

    async def fake_update(self, table_name: str, identifier: dict, update_data: dict):
        assert table_name == "candidates"
        if identifier.get("id") == record1["id"]:
            updated = {**record1, **update_data}
            return updated
        return None

    monkeypatch.setattr(DBClient, "create_table_entry", fake_create)
    monkeypatch.setattr(DBClient, "query_table_data", fake_query)
    monkeypatch.setattr(DBClient, "update_table_entry", fake_update)

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ----- Tests -----

@pytest.mark.asyncio
async def test_create_candidate(client: AsyncClient):
    payload = {"full_name": "Alice", "email": "alice@example.com", "skills": ["python"]}
    r = await client.post("/candidates/", json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["id"] == "11111111-1111-1111-1111-111111111111"
    assert body["full_name"] == "Alice"
    assert body["skills"] == ["python"]

@pytest.mark.asyncio
async def test_list_candidates(client: AsyncClient):
    r = await client.get("/candidates/")
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body, list)
    assert len(body) == 2

@pytest.mark.asyncio
async def test_list_candidates_with_skill_filter(client: AsyncClient):
    r = await client.get("/candidates/?skill=python")
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body) == 1
    assert body[0]["full_name"] == "Alice"

@pytest.mark.asyncio
async def test_get_candidate_by_id_success(client: AsyncClient):
    r = await client.get("/candidates/11111111-1111-1111-1111-111111111111")
    assert r.status_code == 200, r.text
    assert r.json()["email"] == "alice@example.com"

@pytest.mark.asyncio
async def test_get_candidate_by_id_not_found(client: AsyncClient):
    r = await client.get("/candidates/99999999-9999-9999-9999-999999999999")
    assert r.status_code == 404

@pytest.mark.asyncio
async def test_update_candidate_success(client: AsyncClient):
    update = {"full_name": "Alice Updated"}
    r = await client.put("/candidates/11111111-1111-1111-1111-111111111111", json=update)
    assert r.status_code == 200, r.text
    assert r.json()["full_name"] == "Alice Updated"

@pytest.mark.asyncio
async def test_update_candidate_not_found(client: AsyncClient):
    r = await client.put("/candidates/99999999-9999-9999-9999-999999999999", json={"full_name": "No One"})
    assert r.status_code == 404
