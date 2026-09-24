from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db.session import get_db
from app.models.memory import MemoryRecord
from app.schemas.memory import MemoryEnrichRequest, MemoryEnrichResponse
from app.services.ai.enricher import enricher_service

router = APIRouter()


@router.post(
    "/memories/enrich",
    response_model=MemoryEnrichResponse,
    status_code=status.HTTP_200_OK,
    tags=["Memories"],
    summary="Enrich and persist a captured memory item",
)
async def enrich_memory(
    payload: MemoryEnrichRequest,
    db: Session = Depends(get_db),
) -> MemoryEnrichResponse:
    # 1. Run enrichment
    enriched = await enricher_service.enrich(payload)

    # 2. Check if memory already exists (upsert behavior)
    statement = select(MemoryRecord).where(MemoryRecord.client_id == payload.client_id)
    existing_record = db.exec(statement).first()

    record = existing_record or MemoryRecord(client_id=payload.client_id)
    record.raw_content = payload.raw_content
    record.source_url = payload.source_url
    record.source_type = payload.source_type
    record.client_timestamp = payload.client_timestamp
    record.category = enriched.category.value
    record.title = enriched.title
    record.summary = enriched.summary
    record.intent = enriched.intent
    record.keywords = enriched.keywords
    record.target_place = enriched.target_place.model_dump() if enriched.target_place else None
    record.status = enriched.status

    db.add(record)
    db.commit()
    db.refresh(record)

    return enriched


@router.get(
    "/memories/{client_id}",
    response_model=MemoryEnrichResponse,
    tags=["Memories"],
    summary="Fetch a stored enriched memory by client ID",
)
async def get_memory(
    client_id: str,
    db: Session = Depends(get_db),
) -> MemoryEnrichResponse:
    statement = select(MemoryRecord).where(MemoryRecord.client_id == client_id)
    record = db.exec(statement).first()
    if not record:
        raise HTTPException(status_code=404, detail="Memory not found")

    return MemoryEnrichResponse(
        client_id=record.client_id,
        category=record.category,
        title=record.title,
        summary=record.summary,
        intent=record.intent,
        keywords=record.keywords,
        target_place=record.target_place,
        status=record.status,
    )