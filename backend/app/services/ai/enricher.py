import json
import logging
from typing import Optional, List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from app.services.extractors.url_unfurler import url_unfurler

from app.core.config import settings
from app.schemas.memory import (
    MemoryEnrichRequest,
    MemoryEnrichResponse,
    MemoryCategory,
    TargetPlace,
)

logger = logging.getLogger(__name__)


class AIEnrichedMemory(BaseModel):
    category: MemoryCategory = Field(description="One of PLACE, EVENT, RECIPE, TOOL, TOPIC, PRODUCT, OTHER")
    title: str = Field(description="Short meaningful title, max 6 words")
    summary: str = Field(description="Concise 1-2 sentence breakdown")
    intent: str = Field(description="Actionable user intention, e.g., 'Visit this cafe'")
    keywords: List[str] = Field(description="3-6 relevant search tags")
    target_place: Optional[TargetPlace] = Field(
        default=None,
        description="Location name and coordinates if category is PLACE, otherwise null",
    )


SYSTEM_PROMPT = """
You are the AI extraction engine for Echo, an app capturing user intentions from shared mobile content.
Analyze the user's captured content and extract:
1. category: One of [PLACE, EVENT, RECIPE, TOOL, TOPIC, PRODUCT, OTHER]
2. title: Short, meaningful title (max 6 words).
3. summary: Concise 1-2 sentence breakdown.
4. intent: Actionable user intention (e.g., 'Visit this cafe', 'Read this article', 'Try this library').
5. keywords: 3-6 relevant search tags.
6. target_place: If category is PLACE, extract the place name and estimate coordinates (latitude/longitude) if identifiable. Otherwise null.
"""


class GeminiEnricher:
    def __init__(self):
        self.client = None
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def _fallback_response(self, request: MemoryEnrichRequest) -> MemoryEnrichResponse:
        return MemoryEnrichResponse(
            client_id=request.client_id,
            category=MemoryCategory.OTHER,
            title=request.raw_content[:30].strip() or "Saved Memory",
            summary=request.raw_content[:100],
            intent="Review saved item",
            keywords=["review"],
            target_place=None,
            status="ENRICHED",
        )

    async def enrich(self, request: MemoryEnrichRequest) -> MemoryEnrichResponse:
        if not self.client:
            logger.warning("GEMINI_API_KEY not configured. Falling back to default enrichment.")
            return self._fallback_response(request)

        # Unfurl link metadata if URL is available
        unfurl_target = request.source_url or url_unfurler.extract_first_url(request.raw_content)
        metadata_context = ""
        if unfurl_target:
            metadata = await url_unfurler.fetch_metadata(unfurl_target)
            details = []
            if metadata.title:
                details.append(f"Webpage Title: {metadata.title}")
            if metadata.description:
                details.append(f"Webpage Description: {metadata.description}")
            if metadata.site_name:
                details.append(f"Platform: {metadata.site_name}")
            if details:
                metadata_context = "\nExtracted Web Metadata:\n" + "\n".join(details)

        prompt = f"""
Source Type: {request.source_type}
Source URL: {request.source_url or 'N/A'}
Captured Content:
{request.raw_content}
{metadata_context}
"""
        try:
            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=AIEnrichedMemory,
                ),
            )
            ai_data = json.loads(response.text)
            return MemoryEnrichResponse(
                client_id=request.client_id,
                category=ai_data.get("category", MemoryCategory.OTHER),
                title=ai_data.get("title", "Saved Memory"),
                summary=ai_data.get("summary", request.raw_content[:100]),
                intent=ai_data.get("intent", "Review saved item"),
                keywords=ai_data.get("keywords", []),
                target_place=ai_data.get("target_place"),
                status="ENRICHED",
            )
        except Exception as exc:
            logger.error("Gemini enrichment failed: %s", exc, exc_info=True)
            return self._fallback_response(request)


enricher_service = GeminiEnricher()