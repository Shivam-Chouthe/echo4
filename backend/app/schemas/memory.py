from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class SourceType(str, Enum):
    TEXT = "TEXT"
    URL = "URL"
    IMAGE_OCR = "IMAGE_OCR"
    INSTAGRAM = "INSTAGRAM"
    YOUTUBE = "YOUTUBE"
    SCREENSHOT = "SCREENSHOT"


class MemoryCategory(str, Enum):
    PLACE = "PLACE"
    EVENT = "EVENT"
    RECIPE = "RECIPE"
    TOOL = "TOOL"
    TOPIC = "TOPIC"
    PRODUCT = "PRODUCT"
    OTHER = "OTHER"


class TargetPlace(BaseModel):
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class MemoryEnrichRequest(BaseModel):
    client_id: str = Field(..., description="UUID generated locally by Room")
    raw_content: str = Field(..., min_length=1, description="Raw captured text or transcript")
    source_url: Optional[str] = Field(None, description="Original source link if captured from share sheet")
    source_type: SourceType = Field(default=SourceType.TEXT)
    client_timestamp: int = Field(..., description="Epoch millis from device")


class MemoryEnrichResponse(BaseModel):
    client_id: str
    category: MemoryCategory
    title: str
    summary: str
    intent: str
    keywords: List[str] = []
    target_place: Optional[TargetPlace] = None
    status: str = "ENRICHED"

class MemoryIngestResponse(BaseModel):
    client_id: str
    status: str = "PENDING"
    message: str = "Memory ingestion scheduled for processing"


class MemoryListItem(BaseModel):
    client_id: str
    category: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    intent: Optional[str] = None
    keywords: List[str] = []
    target_place: Optional[TargetPlace] = None
    status: str
    source_type: str
    source_url: Optional[str] = None
    client_timestamp: int
    created_at: datetime


class MemoryListResponse(BaseModel):
    total: int
    items: List[MemoryListItem]
    limit: int
    offset: int