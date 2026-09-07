from urllib.parse import urlparse

DEFAULT_SOCIAL_DOMAINS = [
    "instagram.com",
    "facebook.com",
    "x.com",
    "twitter.com",
    "linkedin.com",
    "youtube.com",
    "tiktok.com",
    "reddit.com",
]


def _domain_from_url(url):
    if not url:
        return None
    try:
        parsed = urlparse(url)
        return (parsed.netloc or "").lower().removeprefix("www.") or None
    except Exception:
        return None


def filter_social_results(results, domains=None):
    domains = {
        domain.lower().removeprefix("www.")
        for domain in (domains or DEFAULT_SOCIAL_DOMAINS)
    }

    filtered = []
    for result in results:
        url = result.get("link") or result.get("image") or result.get("source") or ""
        domain = _domain_from_url(url)
        if domain and (domain in domains or any(domain.endswith(f".{item}") for item in domains)):
            platform = domain.split(".")[-2] if "." in domain else domain
            if platform == "twitter":
                platform = "twitter"
            if platform == "x":
                platform = "x"
            filtered.append({
                "platform": platform,
                "url": url,
                "title": result.get("title"),
                "image_url": result.get("thumbnail") or result.get("image"),
                "raw": result,
            })
    return filtered
