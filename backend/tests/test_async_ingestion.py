from unittest.mock import patch
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ingest_memory_returns_202_accepted(async_client: AsyncClient):
    payload = {
        "client_id": "async-test-001",
        "raw_content": "Visit the Aga Khan Palace in Pune on Saturday morning",
        "source_type": "TEXT",
        "client_timestamp": 1727184000000,
    }

    with patch("app.api.v1.endpoints.memories.process_memory_background") as mock_task:
        response = await async_client.post("/api/v1/memories/ingest", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert data["client_id"] == "async-test-001"
        assert data["status"] == "PENDING"

    # Verify initial pending record was persisted
    get_res = await async_client.get("/api/v1/memories/async-test-001")
    assert get_res.status_code == 200
    res_data = get_res.json()
    assert res_data["client_id"] == "async-test-001"
    assert res_data["status"] == "PENDING"