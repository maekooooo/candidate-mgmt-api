# tests/test_applications.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from uuid import UUID

from main import app
from app.core.db_client import DBClient
from app.core.security import get_current_user
from app.models.application import ApplicationStatus

# Bypass the real JWT auth
@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: {"sub": "00000000-0000-0000-0000-000000000001"}

# Stub out DBClient so we never hit Postgres
@pytest.fixture(autouse=True)
def stub_db(monkeypatch):
    # two fake application rows
    app1 = {
        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "candidate_id": "11111111-1111-1111-1111-111111111111",
        "job_title": "Engineer",
        "status": ApplicationStatus.APPLIED.value,
        "applied_at": None,
    }
    app2 = {
        "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "candidate_id": "22222222-2222-2222-2222-222222222222",
        "job_title": "Designer",
        "status": ApplicationStatus.INTERVIEWING.value,
        "applied_at": None,
    }

    # create: echo back with a new id, unless job_title is "Bad" (simulate failure)
    async def fake_create(self, table_name: str, data: dict):
        assert table_name == "applications"
        if data.get("job_title") == "Bad":
            return None
        return {**data, "id": app1["id"], "status": app1["status"]}

    # query list: return only those for matching candidate_id
    async def fake_query(self, table_name: str, filters=None, single_row=False, **kwargs):
        assert table_name == "applications"
        all_apps = [app1, app2]
        if filters and "candidate_id" in filters:
            return [a for a in all_apps if a["candidate_id"] == filters["candidate_id"]]
        return all_apps

    # update: only app1 exists; merging update_data into it
    async def fake_update(self, table_name: str, identifier: dict, update_data: dict):
        assert table_name == "applications"
        if identifier.get("id") == app1["id"]:
            return {**app1, **update_data}
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
async def test_create_application_success(client: AsyncClient):
    cid = "11111111-1111-1111-1111-111111111111"
    payload = {"job_title": "Engineer"}
    r = await client.post(f"/candidates/{cid}/applications", json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["id"] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    assert body["candidate_id"] == cid
    assert body["job_title"] == "Engineer"
    assert body["status"] == ApplicationStatus.APPLIED.value

@pytest.mark.asyncio
async def test_create_application_failure(client: AsyncClient):
    cid = "11111111-1111-1111-1111-111111111111"
    payload = {"job_title": "Bad"}
    r = await client.post(f"/candidates/{cid}/applications", json=payload)
    assert r.status_code == 400
    assert r.json()["detail"] == "Failed to create application"

@pytest.mark.asyncio
async def test_list_applications_for_candidate(client: AsyncClient):
    cid = "11111111-1111-1111-1111-111111111111"
    r = await client.get(f"/candidates/{cid}/applications")
    assert r.status_code == 200, r.text
    apps = r.json()
    assert isinstance(apps, list)
    assert len(apps) == 1
    assert apps[0]["candidate_id"] == cid

@pytest.mark.asyncio
async def test_list_applications_empty(client: AsyncClient):
    # candidate 333 has no apps
    r = await client.get("/candidates/33333333-3333-3333-3333-333333333333/applications")
    assert r.status_code == 200
    assert r.json() == []

@pytest.mark.asyncio
async def test_update_application_success(client: AsyncClient):
    aid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    new_status = ApplicationStatus.HIRED.value
    r = await client.patch(f"/applications/{aid}?application_status={new_status}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == aid
    assert body["status"] == new_status

@pytest.mark.asyncio
async def test_update_application_invalid_status(client: AsyncClient):
    aid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    r = await client.patch(f"/applications/{aid}?application_status=NOT_A_STATUS")
    assert r.status_code == 400
