from fastapi import APIRouter, status
from app.schemas.memory import (
    MemoryEnrichRequest,
    MemoryEnrichResponse,
    MemoryCategory,
    TargetPlace,
)

router = APIRouter()


@router.post(
    "/memories/enrich",
    response_model=MemoryEnrichResponse,
    status_code=status.HTTP_200_OK,
    tags=["Memories"],
    summary="Enrich a captured memory item with intent and categorization",
)
async def enrich_memory(payload: MemoryEnrichRequest) -> MemoryEnrichResponse:
    content_lower = payload.raw_content.lower()

    if any(k in content_lower for k in ["cafe", "restaurant", "food", "ramen", "park", "hotel", "visit"]):
        category = MemoryCategory.PLACE
        title = "Saved Location / Spot"
        intent = "Visit this place"
        target_place = TargetPlace(name="Sample Location", latitude=18.5204, longitude=73.8567)
        keywords = ["visit", "location", "explore"]
    elif any(k in content_lower for k in ["recipe", "cook", "bake", "ingredients", "tablespoon"]):
        category = MemoryCategory.RECIPE
        title = "Saved Recipe"
        intent = "Cook this dish"
        target_place = None
        keywords = ["food", "recipe", "cooking"]
    elif any(k in content_lower for k in ["tool", "library", "github", "framework", "app"]):
        category = MemoryCategory.TOOL
        title = "Saved Developer / Productivity Tool"
        intent = "Try or integrate this tool"
        target_place = None
        keywords = ["tool", "utility", "software"]
    else:
        category = MemoryCategory.OTHER
        title = payload.raw_content[:30].strip() or "Saved Memory"
        intent = "Review saved item"
        target_place = None
        keywords = ["review", "general"]

    summary = (
        f"Summary: {payload.raw_content[:80]}..."
        if len(payload.raw_content) > 80
        else payload.raw_content
    )

    return MemoryEnrichResponse(
        client_id=payload.client_id,
        category=category,
        title=title,
        summary=summary,
        intent=intent,
        keywords=keywords,
        target_place=target_place,
        status="ENRICHED",
    )