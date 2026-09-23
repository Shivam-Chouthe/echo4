import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_enrich_memory_place(async_client: AsyncClient):
    payload = {
        "client_id": "test-uuid-1234",
        "raw_content": "Best ramen cafe in Koregaon Park",
        "source_url": "https://instagram.com/reel/123",
        "source_type": "INSTAGRAM",
        "client_timestamp": 1727113713000,
    }
    response = await async_client.post("/api/v1/memories/enrich", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["client_id"] == "test-uuid-1234"
    assert data["category"] == "PLACE"
    assert data["intent"] == "Visit this place"
    assert data["target_place"] is not None
    assert data["status"] == "ENRICHED"


@pytest.mark.asyncio
async def test_enrich_memory_invalid_payload(async_client: AsyncClient):
    payload = {
        "client_id": "test-uuid-1234",
        "raw_content": "",
        "client_timestamp": 1727113713000,
    }
    response = await async_client.post("/api/v1/memories/enrich", json=payload)
    assert response.status_code == 422