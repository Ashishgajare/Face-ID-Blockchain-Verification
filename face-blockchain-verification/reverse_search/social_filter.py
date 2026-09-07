from __future__ import annotations
from typing import Iterable, List
from pydantic import BaseModel
from .result_parser import SearchResult
from urllib.parse import urlparse


DEFAULT_SOCIAL_DOMAINS = [
    "instagram.com",
    "facebook.com",
    "x.com",
    "twitter.com",
    "linkedin.com",
]


class SocialMediaCandidate(BaseModel):
    platform: str
    url: str
    title: str | None
    image_url: str | None
    raw: dict


def _domain_from_url(url: str | None) -> str | None:
    if not url:
        return None
    try:
        p = urlparse(url)
        return (p.hostname or "").lower().removeprefix("www.") or None
    except Exception:
        return None


def filter_social_results(results: Iterable[SearchResult], domains: Iterable[str] | None = None) -> List[SocialMediaCandidate]:
    domains = {domain.lower().removeprefix("www.") for domain in (domains or DEFAULT_SOCIAL_DOMAINS)}
    out: List[SocialMediaCandidate] = []
    for r in results:
        dom = _domain_from_url(r.link)
        if dom and (dom in domains or any(dom.endswith(f".{domain}") for domain in domains)):
            platform = dom.split(".")[-2] if "." in dom else dom
            if platform == "twitter":
                platform = "twitter"
            out.append(SocialMediaCandidate(platform=platform, url=r.link or "", title=r.title, image_url=r.thumbnail, raw=r.raw))
    return out
