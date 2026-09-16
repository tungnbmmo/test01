"""Download MediaResult files to disk and write per-block attribution credits."""

import logging
from pathlib import Path

import requests

from .models import MediaResult

logger = logging.getLogger("broll_finder.downloader")

_EXT_BY_TYPE = {"video": ".mp4", "photo": ".jpg"}


def download_media(item: MediaResult, dest_dir: Path, filename_stem: str) -> Path | None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    ext = _EXT_BY_TYPE.get(item.media_type, "")
    dest_path = dest_dir / f"{filename_stem}{ext}"

    try:
        with requests.get(item.download_url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1 << 16):
                    if chunk:
                        f.write(chunk)
    except requests.RequestException as exc:
        logger.warning("Download failed for %s: %s", item.download_url, exc)
        if dest_path.exists():
            dest_path.unlink(missing_ok=True)
        return None

    return dest_path


def append_credit(credits_path: Path, item: MediaResult, local_path: Path) -> None:
    credits_path.parent.mkdir(parents=True, exist_ok=True)
    line = (
        f"{local_path.name}\t"
        f"source={item.source}\t"
        f"author={item.author}\t"
        f"page={item.page_url}\n"
    )
    with open(credits_path, "a", encoding="utf-8") as f:
        f.write(line)
