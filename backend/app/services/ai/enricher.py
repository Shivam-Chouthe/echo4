import asyncio
import json
import logging
from typing import Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.core.config import settings
from app.schemas.memory import (
    MemoryCategory,
    MemoryEnrichRequest,
    MemoryEnrichResponse,
    TargetPlace,
)
from app.services.extractors.url_unfurler import URLUnfurler

logger = logging.getLogger(__name__)

CANDIDATE_MODELS = [
    settings.GEMINI_MODEL,
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]

unfurler_service = URLUnfurler()


class EnricherService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def enrich(self, request: MemoryEnrichRequest) -> MemoryEnrichResponse:
        content_to_analyze = request.raw_content

        # 1. Unfurl metadata using the correct fetch_metadata method
        if request.source_url or "http" in request.raw_content:
            url = request.source_url or unfurler_service.extract_first_url(request.raw_content)
            if url:
                metadata = await unfurler_service.fetch_metadata(url)
                if metadata and metadata.title:
                    content_to_analyze = (
                        f"Original Content: {request.raw_content}\n"
                        f"URL: {url}\n"
                        f"Page Title: {metadata.title}\n"
                        f"Description: {metadata.description or ''}\n"
                        f"Site: {metadata.site_name or ''}"
                    )

        prompt = (
            "Analyze the captured content and extract structured memory fields.\n"
            f"client_id must be: \"{request.client_id}\"\n"
            "Identify category (PLACE, EVENT, RECIPE, TOOL, TOPIC, PRODUCT, OTHER).\n"
            "Summarize in 1-2 sentences. Keep title under 6 words.\n"
            "Extract 3-5 keywords. If category is PLACE, extract target place name and approximate coordinates.\n\n"
            f"Content:\n{content_to_analyze}"
        )

        # 2. Try candidate models with fallback backoff
        for model_name in CANDIDATE_MODELS:
            for attempt in range(2):
                try:
                    logger.info("Attempting enrichment with %s (attempt %d)", model_name, attempt + 1)
                    response = await asyncio.to_thread(
                        self.client.models.generate_content,
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=MemoryEnrichResponse,
                            temperature=0.2,
                        ),
                    )
                    parsed_json = json.loads(response.text)
                    parsed_json["client_id"] = request.client_id
                    return MemoryEnrichResponse(**parsed_json)
                except (APIError, Exception) as exc:
                    logger.warning("Model %s failed attempt %d: %s", model_name, attempt + 1, exc)
                    await asyncio.sleep(1.0)
                    break

        logger.error("Gemini models unavailable. Executing deterministic fallback.")
        return self._heuristic_fallback(request)

    def _heuristic_fallback(self, request: MemoryEnrichRequest) -> MemoryEnrichResponse:
        clean_text = request.raw_content.strip()
        first_line = clean_text.split("\n")[0][:40]

        lowered = clean_text.lower()
        if any(w in lowered for w in ["cafe", "restaurant", "palace", "visit", "hotel", "street"]):
            category = MemoryCategory.PLACE
        elif any(w in lowered for w in ["recipe", "cook", "bake", "soup", "curry", "ingredients"]):
            category = MemoryCategory.RECIPE
        elif any(w in lowered for w in ["tool", "library", "sdk", "github", "package"]):
            category = MemoryCategory.TOOL
        else:
            category = MemoryCategory.TOPIC

        words = [w.strip(".,!?:") for w in clean_text.split() if len(w) > 4][:5]

        return MemoryEnrichResponse(
            client_id=request.client_id,
            category=category,
            title=first_line if first_line else "Captured Memory",
            summary=clean_text[:160],
            intent="Review saved content",
            keywords=words,
            target_place=None,
        )


enricher_service = EnricherService()