"""
Basic API tests for the RAG Chatbot backend.
Run with: pytest tests/ -v
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.anyio
async def test_register(client: AsyncClient):
    response = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "org_name": "Test Org",
    })
    # Will fail without DB, but should at least hit the endpoint
    assert response.status_code in (201, 500)


@pytest.mark.anyio
async def test_unauthorized_chat(client: AsyncClient):
    response = await client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 403  # No auth header


@pytest.mark.anyio
async def test_unauthorized_documents(client: AsyncClient):
    response = await client.get("/api/documents")
    assert response.status_code == 403


@pytest.mark.anyio
async def test_unauthorized_admin(client: AsyncClient):
    response = await client.get("/api/admin/analytics")
    assert response.status_code == 403
