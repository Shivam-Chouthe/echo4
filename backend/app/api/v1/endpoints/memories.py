from sqlalchemy import func
from app.schemas.memory import (
    MemoryEnrichRequest,
    MemoryEnrichResponse,
    MemoryIngestResponse,
    MemoryListItem,
    MemoryListResponse,
    MemoryCategory,
)

import logging
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db.session import engine, get_db
from app.models.memory import MemoryRecord
from app.schemas.memory import (
    MemoryEnrichRequest,
    MemoryEnrichResponse,
    MemoryIngestResponse,
)
from app.services.ai.enricher import enricher_service

logger = logging.getLogger(__name__)
router = APIRouter()


async def process_memory_background(payload: MemoryEnrichRequest, db_engine=None) -> None:
    """Async worker function running outside the HTTP request/response cycle."""
    target_engine = db_engine or engine
    try:
        enriched = await enricher_service.enrich(payload)
        with Session(target_engine) as db:
            statement = select(MemoryRecord).where(MemoryRecord.client_id == payload.client_id)
            record = db.exec(statement).first()
            if record:
                record.category = enriched.category.value
                record.title = enriched.title
                record.summary = enriched.summary
                record.intent = enriched.intent
                record.keywords = enriched.keywords
                record.target_place = (
                    enriched.target_place.model_dump() if enriched.target_place else None
                )
                record.status = "ENRICHED"
                db.add(record)
                db.commit()
    except Exception as exc:
        logger.error("Background task failed for %s: %s", payload.client_id, exc)
        with Session(target_engine) as db:
            statement = select(MemoryRecord).where(MemoryRecord.client_id == payload.client_id)
            record = db.exec(statement).first()
            if record:
                record.status = "FAILED"
                db.add(record)
                db.commit()


@router.post(
    "/memories/ingest",
    response_model=MemoryIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Memories"],
    summary="Non-blocking share-sheet memory intake (returns 202 Accepted immediately)",
)
async def ingest_memory(
    payload: MemoryEnrichRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> MemoryIngestResponse:
    statement = select(MemoryRecord).where(MemoryRecord.client_id == payload.client_id)
    existing_record = db.exec(statement).first()

    record = existing_record or MemoryRecord(client_id=payload.client_id)
    record.raw_content = payload.raw_content
    record.source_url = payload.source_url
    record.source_type = payload.source_type
    record.client_timestamp = payload.client_timestamp
    record.status = "PENDING"

    db.add(record)
    db.commit()

    # Pass the active bind engine so background worker writes to the same db
    bind_engine = db.get_bind()
    background_tasks.add_task(process_memory_background, payload, bind_engine)

    return MemoryIngestResponse(
        client_id=payload.client_id,
        status="PENDING",
        message="Memory received and queued for background AI enrichment",
    )


@router.post(
    "/memories/enrich",
    response_model=MemoryEnrichResponse,
    status_code=status.HTTP_200_OK,
    tags=["Memories"],
    summary="Synchronously enrich and persist a memory (waits for Gemini)",
)
async def enrich_memory(
    payload: MemoryEnrichRequest,
    db: Session = Depends(get_db),
) -> MemoryEnrichResponse:
    enriched = await enricher_service.enrich(payload)

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
    record.target_place = (
        enriched.target_place.model_dump() if enriched.target_place else None
    )
    record.status = enriched.status

    db.add(record)
    db.commit()
    return enriched


@router.get(
    "/memories",
    response_model=MemoryListResponse,
    tags=["Memories"],
    summary="List stored memories with optional filtering and pagination",
)
async def list_memories(
    category: Optional[MemoryCategory] = None,
    status: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> MemoryListResponse:
    base_query = select(MemoryRecord)

    if category:
        base_query = base_query.where(MemoryRecord.category == category.value)
    if status:
        base_query = base_query.where(MemoryRecord.status == status)
    if query:
        search_pattern = f"%{query}%"
        base_query = base_query.where(
            (MemoryRecord.title.ilike(search_pattern))
            | (MemoryRecord.summary.ilike(search_pattern))
            | (MemoryRecord.raw_content.ilike(search_pattern))
        )

    # Count total matching records
    total = db.exec(select(func.count()).select_from(base_query.subquery())).one()

    # Order newest first and apply pagination
    paginated_query = (
        base_query.order_by(MemoryRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    records = db.exec(paginated_query).all()

    items = [
        MemoryListItem(
            client_id=r.client_id,
            category=r.category,
            title=r.title,
            summary=r.summary,
            intent=r.intent,
            keywords=r.keywords,
            target_place=r.target_place,
            status=r.status,
            source_type=r.source_type,
            source_url=r.source_url,
            client_timestamp=r.client_timestamp,
            created_at=r.created_at,
        )
        for r in records
    ]

    return MemoryListResponse(
        total=total,
        items=items,
        limit=limit,
        offset=offset,
    )



@router.get(
    "/memories/{client_id}",
    tags=["Memories"],
    summary="Fetch memory status and enriched payload by client ID",
)
async def get_memory(
    client_id: str,
    db: Session = Depends(get_db),
):
    statement = select(MemoryRecord).where(MemoryRecord.client_id == client_id)
    record = db.exec(statement).first()
    if not record:
        raise HTTPException(status_code=404, detail="Memory not found")

    return {
        "client_id": record.client_id,
        "status": record.status,
        "category": record.category,
        "title": record.title,
        "summary": record.summary,
        "intent": record.intent,
        "keywords": record.keywords,
        "target_place": record.target_place,
    }