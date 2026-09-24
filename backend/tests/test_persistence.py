import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_enrich_and_retrieve_persisted_memory(async_client: AsyncClient):
    payload = {
        "client_id": "test-persist-001",
        "raw_content": "Must visit German Bakery in Koregaon Park Pune for breakfast",
        "source_type": "TEXT",
        "client_timestamp": 1727184000000,
    }

    # 1. Post to enrich endpoint
    post_res = await async_client.post("/api/v1/memories/enrich", json=payload)
    assert post_res.status_code == 200

    # 2. Query persisted record by client_id
    get_res = await async_client.get(f"/api/v1/memories/{payload['client_id']}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["client_id"] == payload["client_id"]
    assert "status" in data
    assert data["status"] == "ENRICHED"


@pytest.mark.asyncio
async def test_get_nonexistent_memory(async_client: AsyncClient):
    res = await async_client.get("/api/v1/memories/unknown-client-id")
    assert res.status_code == 404