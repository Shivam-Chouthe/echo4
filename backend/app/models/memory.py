from datetime import datetime, timezone
import json
from typing import List, Optional
from sqlmodel import Field, SQLModel


class MemoryRecord(SQLModel, table=True):
    __tablename__ = "memories"

    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: str = Field(index=True, unique=True)
    raw_content: str
    source_url: Optional[str] = None
    source_type: str = "TEXT"
    client_timestamp: int

    # AI Extracted fields
    category: str = Field(index=True)
    title: str
    summary: str
    intent: str
    keywords_json: str = Field(default="[]")
    target_place_json: Optional[str] = None
    status: str = "ENRICHED"

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def keywords(self) -> List[str]:
        return json.loads(self.keywords_json)

    @keywords.setter
    def keywords(self, value: List[str]) -> None:
        self.keywords_json = json.dumps(value)

    @property
    def target_place(self) -> Optional[dict]:
        return json.loads(self.target_place_json) if self.target_place_json else None

    @target_place.setter
    def target_place(self, value: Optional[dict]) -> None:
        self.target_place_json = json.dumps(value) if value else None