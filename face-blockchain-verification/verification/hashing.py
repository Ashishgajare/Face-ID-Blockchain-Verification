from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .models import VerificationRecord


def hash_verification_record(record: VerificationRecord | Mapping[str, Any]) -> str:
    """Hash a verification record using canonical UTF-8 JSON."""
    payload = record.model_dump(mode="json") if isinstance(record, VerificationRecord) else dict(record)
    canonical_json = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
