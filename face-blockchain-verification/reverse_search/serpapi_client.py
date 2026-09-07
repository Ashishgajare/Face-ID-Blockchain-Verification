from __future__ import annotations
import requests
from typing import Any, Dict
import config
import logging

logger = logging.getLogger(__name__)


SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"
TEMP_UPLOAD_URL = "https://uguu.se/upload.php"


def _upload_image_for_search(image_path: str, timeout: int) -> str:
    with open(image_path, "rb") as image_file:
        response = requests.post(
            TEMP_UPLOAD_URL,
            files={"files[]": (image_path, image_file)},
            timeout=timeout,
        )
    response.raise_for_status()
    return response.json()["files"][0]["url"]


def reverse_image_search(image_path: str, timeout: int | None = None) -> Dict[str, Any]:
    """Upload the image temporarily and search its public URL with SerpApi."""
    config.require_serpapi_key()
    timeout = timeout or config.SERPAPI_TIMEOUT

    image_url = _upload_image_for_search(image_path, timeout)
    params = {
        "engine": "google_reverse_image",
        "image_url": image_url,
        "api_key": config.SERPAPI_KEY,
    }

    try:
        resp = requests.get(SERPAPI_SEARCH_URL, params=params, timeout=timeout)
    except requests.RequestException as e:
        logger.exception("SerpApi request failed: %s", e)
        raise

    if resp.status_code != 200:
        raise RuntimeError(f"SerpApi returned HTTP {resp.status_code}: {resp.text}")

    try:
        return resp.json()
    except Exception as e:
        logger.exception("Failed to decode SerpApi JSON response: %s", e)
        raise
