from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class VerificationRecord(BaseModel):
    image_sha256: str = Field(min_length=64, max_length=64)
    matched: bool
    similarity: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)
    candidate_url: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def verification_record_hash(record: VerificationRecord | Dict[str, Any]) -> str:
    """Return a stable SHA-256 digest for a verification record."""
    payload = record.model_dump() if isinstance(record, VerificationRecord) else record
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
