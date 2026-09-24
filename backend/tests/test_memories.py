from unittest.mock import patch
import pytest
from httpx import AsyncClient
from app.schemas.memory import MemoryCategory, MemoryEnrichResponse


@pytest.mark.asyncio
async def test_enrich_memory_fallback(async_client: AsyncClient):
    payload = {
        "client_id": "test-uuid-fallback",
        "raw_content": "Check out this documentation on FastAPI lifespan",
        "source_url": "https://fastapi.tiangolo.com",
        "source_type": "URL",
        "client_timestamp": 1727113713000,
    }
    response = await async_client.post("/api/v1/memories/enrich", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] == "test-uuid-fallback"
    assert data["status"] == "ENRICHED"


@pytest.mark.asyncio
async def test_enrich_memory_gemini_mocked(async_client: AsyncClient):
    mocked_response = MemoryEnrichResponse(
        client_id="test-uuid-1234",
        category=MemoryCategory.PLACE,
        title="Artisan Ramen",
        summary="A famous Japanese ramen restaurant in Koregaon Park.",
        intent="Visit for dinner",
        keywords=["ramen", "dinner", "pune"],
        target_place={"name": "Koregaon Park Ramen", "latitude": 18.5362, "longitude": 73.8940},
        status="ENRICHED",
    )

    with patch("app.services.ai.enricher.enricher_service.enrich", return_value=mocked_response):
        payload = {
            "client_id": "test-uuid-1234",
            "raw_content": "Best artisan ramen shop in KP Pune",
            "source_type": "TEXT",
            "client_timestamp": 1727113713000,
        }
        response = await async_client.post("/api/v1/memories/enrich", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Artisan Ramen"
        assert data["category"] == "PLACE"
        assert data["target_place"]["latitude"] == 18.5362


@pytest.mark.asyncio
async def test_enrich_memory_invalid_payload(async_client: AsyncClient):
    payload = {
        "client_id": "test-uuid-1234",
        "raw_content": "",
        "client_timestamp": 1727113713000,
    }
    response = await async_client.post("/api/v1/memories/enrich", json=payload)
    assert response.status_code == 422