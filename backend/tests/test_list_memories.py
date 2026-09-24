import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_memories_and_filtering(async_client: AsyncClient):
    # Seed a place memory
    place_payload = {
        "client_id": "item-place-01",
        "raw_content": "Visit Koregaon Park cafe",
        "source_type": "TEXT",
        "client_timestamp": 1727184000000,
    }
    await async_client.post("/api/v1/memories/enrich", json=place_payload)

    # Seed a tool memory
    tool_payload = {
        "client_id": "item-tool-02",
        "raw_content": "Try uv package manager for fast Python environments",
        "source_type": "TEXT",
        "client_timestamp": 1727184005000,
    }
    await async_client.post("/api/v1/memories/enrich", json=tool_payload)

    # 1. Fetch all items
    res = await async_client.get("/api/v1/memories")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2

    # 2. Filter by category PLACE
    res_place = await async_client.get("/api/v1/memories?category=PLACE")
    assert res_place.status_code == 200
    place_data = res_place.json()
    assert all(item["category"] == "PLACE" for item in place_data["items"])

    # 3. Test pagination limit
    res_paginated = await async_client.get("/api/v1/memories?limit=1")
    assert res_paginated.status_code == 200
    paginated_data = res_paginated.json()
    assert len(paginated_data["items"]) == 1
    assert paginated_data["limit"] == 1