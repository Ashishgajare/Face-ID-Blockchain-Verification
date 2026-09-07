from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class VerificationRecord(BaseModel):
    schema_version: str = "1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    platform: str
    post_url: str
    similarity: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)
    search_provider: str = "Google Reverse Image via SerpApi"
    status: str
    image_sha256: Optional[str] = Field(default=None, min_length=64, max_length=64)
