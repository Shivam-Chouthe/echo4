from fastapi import APIRouter, status
from app.schemas.memory import MemoryEnrichRequest, MemoryEnrichResponse
from app.services.ai.enricher import enricher_service

router = APIRouter()


@router.post(
    "/memories/enrich",
    response_model=MemoryEnrichResponse,
    status_code=status.HTTP_200_OK,
    tags=["Memories"],
    summary="Enrich a captured memory item with intent and categorization",
)
async def enrich_memory(payload: MemoryEnrichRequest) -> MemoryEnrichResponse:
    return await enricher_service.enrich(payload)