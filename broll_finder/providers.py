"""Search clients for Pexels and Pixabay, normalized to MediaResult."""

import logging
import time

import requests

from .models import MediaResult

logger = logging.getLogger("broll_finder.providers")

_TIMEOUT = 15
_MAX_RETRIES = 3


def _get_with_retries(url: str, *, headers: dict | None = None, params: dict | None = None) -> requests.Response | None:
    delay = 1.0
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=_TIMEOUT)
        except requests.RequestException as exc:
            logger.warning("Request failed (%s/%s): %s", attempt, _MAX_RETRIES, exc)
            time.sleep(delay)
            delay *= 2
            continue

        if resp.status_code == 429:
            logger.warning("Rate limited, backing off %.1fs", delay)
            time.sleep(delay)
            delay *= 2
            continue
        if resp.status_code >= 400:
            logger.warning("HTTP %s from %s: %s", resp.status_code, url, resp.text[:200])
            return None
        return resp
    return None


class PexelsProvider:
    name = "pexels"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._headers = {"Authorization": api_key}

    def search_videos(self, query: str, *, per_page: int = 3, orientation: str = "landscape") -> list[MediaResult]:
        params = {"query": query, "per_page": per_page, "orientation": orientation}
        resp = _get_with_retries("https://api.pexels.com/videos/search", headers=self._headers, params=params)
        if resp is None:
            return []

        results = []
        for video in resp.json().get("videos", []):
            files = sorted(
                (f for f in video.get("video_files", []) if f.get("link")),
                key=lambda f: f.get("width") or 0,
                reverse=True,
            )
            hd_files = [f for f in files if f.get("quality") == "hd"] or files
            if not hd_files:
                continue
            best = hd_files[0]
            results.append(
                MediaResult(
                    source=self.name,
                    media_type="video",
                    id=str(video["id"]),
                    download_url=best["link"],
                    page_url=video.get("url", ""),
                    author=video.get("user", {}).get("name", "unknown"),
                    width=best.get("width", 0),
                    height=best.get("height", 0),
                )
            )
        return results

    def search_photos(self, query: str, *, per_page: int = 3, orientation: str = "landscape") -> list[MediaResult]:
        params = {"query": query, "per_page": per_page, "orientation": orientation}
        resp = _get_with_retries("https://api.pexels.com/v1/search", headers=self._headers, params=params)
        if resp is None:
            return []

        results = []
        for photo in resp.json().get("photos", []):
            src = photo.get("src", {})
            url = src.get("large2x") or src.get("original") or src.get("large")
            if not url:
                continue
            results.append(
                MediaResult(
                    source=self.name,
                    media_type="photo",
                    id=str(photo["id"]),
                    download_url=url,
                    page_url=photo.get("url", ""),
                    author=photo.get("photographer", "unknown"),
                    width=photo.get("width", 0),
                    height=photo.get("height", 0),
                )
            )
        return results


class PixabayProvider:
    name = "pixabay"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search_videos(self, query: str, *, per_page: int = 3, orientation: str = "landscape") -> list[MediaResult]:
        params = {
            "key": self.api_key,
            "q": query,
            "per_page": max(per_page, 3),  # Pixabay requires per_page >= 3
        }
        resp = _get_with_retries("https://pixabay.com/api/videos/", params=params)
        if resp is None:
            return []

        results = []
        for hit in resp.json().get("hits", [])[:per_page]:
            videos = hit.get("videos", {})
            best = videos.get("large") or videos.get("medium") or videos.get("small")
            if not best or not best.get("url"):
                continue
            results.append(
                MediaResult(
                    source=self.name,
                    media_type="video",
                    id=str(hit["id"]),
                    download_url=best["url"],
                    page_url=hit.get("pageURL", ""),
                    author=hit.get("user", "unknown"),
                    width=best.get("width", 0),
                    height=best.get("height", 0),
                )
            )
        return results

    def search_photos(self, query: str, *, per_page: int = 3, orientation: str = "landscape") -> list[MediaResult]:
        pixabay_orientation = "horizontal" if orientation == "landscape" else (
            "vertical" if orientation == "portrait" else "all"
        )
        params = {
            "key": self.api_key,
            "q": query,
            "image_type": "photo",
            "orientation": pixabay_orientation,
            "per_page": max(per_page, 3),
        }
        resp = _get_with_retries("https://pixabay.com/api/", params=params)
        if resp is None:
            return []

        results = []
        for hit in resp.json().get("hits", [])[:per_page]:
            url = hit.get("largeImageURL") or hit.get("webformatURL")
            if not url:
                continue
            results.append(
                MediaResult(
                    source=self.name,
                    media_type="photo",
                    id=str(hit["id"]),
                    download_url=url,
                    page_url=hit.get("pageURL", ""),
                    author=hit.get("user", "unknown"),
                    width=hit.get("imageWidth", 0),
                    height=hit.get("imageHeight", 0),
                )
            )
        return results
