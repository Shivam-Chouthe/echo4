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

    # Nullable fields while in PENDING state
    category: Optional[str] = Field(default=None, index=True, nullable=True)
    title: Optional[str] = Field(default=None, nullable=True)
    summary: Optional[str] = Field(default=None, nullable=True)
    intent: Optional[str] = Field(default=None, nullable=True)
    keywords_json: str = Field(default="[]")
    target_place_json: Optional[str] = Field(default=None, nullable=True)
    status: str = "PENDING"  # PENDING, ENRICHED, FAILED

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