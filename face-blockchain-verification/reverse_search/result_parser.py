from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from urllib.parse import urlparse


class SearchResult(BaseModel):
    title: Optional[str]
    link: Optional[str]
    source: Optional[str]
    thumbnail: Optional[str]
    position: Optional[int]
    raw: Dict[str, Any]


def parse_serpapi_response(resp: Dict[str, Any]) -> List[SearchResult]:
    results: List[SearchResult] = []

    # Common key for image-based results
    candidates = []
    if "image_results" in resp:
        candidates = resp.get("image_results") or []
    elif "inline_images" in resp:
        candidates = resp.get("inline_images") or []
    elif "similar_images" in resp:
        candidates = resp.get("similar_images") or []

    for idx, item in enumerate(candidates):
        # Attempt to canonicalize fields
        link = item.get("link") or item.get("original") or item.get("image") or item.get("source")
        title = item.get("title") or item.get("name")
        thumbnail = item.get("thumbnail") or item.get("thumbnail_link") or item.get("thumbnail_url")
        source = None
        if link:
            parsed = urlparse(link)
            source = parsed.netloc

        results.append(SearchResult(title=title, link=link, source=source, thumbnail=thumbnail, position=idx + 1, raw=item))

    return results
