"""CLI: read a B-roll keyword list -> search Pexels/Pixabay -> download results.

Usage:
    python -m broll_finder.cli --input keywords.md --output-dir ./broll_output
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

from .downloader import append_credit, download_media
from .google_links import build_google_images_url, write_google_links_file
from .models import MediaResult
from .parser import parse_input, slugify
from .providers import PexelsProvider, PixabayProvider

logger = logging.getLogger("broll_finder.cli")


def _load_env_file(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Tự động tìm và tải B-roll từ Pexels/Pixabay theo danh sách từ khóa.")
    p.add_argument("--input", required=True, help="File chứa bảng/danh sách từ khóa B-roll (md, txt, json).")
    p.add_argument("--output-dir", default="./broll_output", help="Thư mục lưu kết quả (mặc định ./broll_output).")
    p.add_argument("--source", choices=["pexels", "pixabay", "both"], default="both", help="Nguồn tìm kiếm.")
    p.add_argument(
        "--media-type",
        choices=["video", "photo", "both"],
        default=None,
        help="Ép kiểu tư liệu, bỏ qua gợi ý trong input. Mặc định: theo gợi ý input (hoặc cả hai).",
    )
    p.add_argument("--per-keyword", type=int, default=2, help="Số file tải về cho mỗi (từ khóa x loại tư liệu).")
    p.add_argument("--orientation", choices=["landscape", "portrait", "square", "any"], default="landscape")
    p.add_argument("--max-keywords-per-block", type=int, default=0, help="0 = không giới hạn.")
    p.add_argument("--sleep", type=float, default=0.4, help="Giây nghỉ giữa các lượt gọi API (tránh rate limit).")
    p.add_argument("--dry-run", action="store_true", help="Chỉ tìm kiếm và ghi manifest, không tải file.")
    p.add_argument(
        "--no-google-links",
        action="store_true",
        help="Không tạo file google_links.md (link Google Hình ảnh cho từng từ khóa, để tự kiểm tra bản quyền).",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def _resolve_providers(source: str) -> dict:
    providers = {}
    if source in ("pexels", "both"):
        key = os.environ.get("PEXELS_API_KEY")
        if key:
            providers["pexels"] = PexelsProvider(key)
        else:
            logger.warning("Bỏ qua Pexels: chưa đặt biến môi trường PEXELS_API_KEY.")
    if source in ("pixabay", "both"):
        key = os.environ.get("PIXABAY_API_KEY")
        if key:
            providers["pixabay"] = PixabayProvider(key)
        else:
            logger.warning("Bỏ qua Pixabay: chưa đặt biến môi trường PIXABAY_API_KEY.")
    return providers


def _search_keyword(providers: dict, keyword: str, media_types: set, per_keyword: int, orientation: str, sleep_s: float) -> list[MediaResult]:
    results: list[MediaResult] = []
    for provider in providers.values():
        for media_type in media_types:
            search_fn = provider.search_videos if media_type == "video" else provider.search_photos
            try:
                hits = search_fn(keyword, per_page=per_keyword, orientation=orientation)
            except Exception as exc:  # noqa: BLE001 - keep the pipeline going on provider errors
                logger.warning("Lỗi tìm kiếm [%s/%s] cho '%s': %s", provider.name, media_type, keyword, exc)
                hits = []
            results.extend(hits[:per_keyword])
            time.sleep(sleep_s)
            if len(results) >= per_keyword:
                break
        if len(results) >= per_keyword:
            break
    return results[:per_keyword]


def run(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")

    _load_env_file()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error("Không tìm thấy file input: %s", input_path)
        return 1

    blocks = parse_input(input_path.read_text(encoding="utf-8"), file_hint=input_path.name)
    if not blocks:
        logger.error("Không parse được từ khóa nào từ input. Kiểm tra lại định dạng file.")
        return 1

    providers = _resolve_providers(args.source)
    if not providers and not args.dry_run:
        logger.error(
            "Chưa có API key khả dụng. Đặt PEXELS_API_KEY và/hoặc PIXABAY_API_KEY trong biến môi trường "
            "hoặc file .env (xem .env.example)."
        )
        return 1

    if args.max_keywords_per_block:
        for block in blocks:
            block.keywords = block.keywords[: args.max_keywords_per_block]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []

    total_keywords = sum(len(b.keywords) for b in blocks)
    logger.info("Đã parse %d khối, %d từ khóa. Nguồn: %s.", len(blocks), total_keywords, ", ".join(providers) or "(dry-run, không có provider)")

    if not args.no_google_links:
        google_links_path = output_dir / "google_links.md"
        write_google_links_file(blocks, google_links_path)
        logger.info("Đã ghi link Google Hình ảnh cho từng từ khóa: %s", google_links_path)

    for block in blocks:
        block_slug = f"block_{block.index:02d}_{slugify(block.title)}"[:80]
        block_dir = output_dir / block_slug
        keywords = block.keywords

        if args.media_type:
            media_types = {"video", "photo"} if args.media_type == "both" else {args.media_type}
        else:
            media_types = block.media_hint

        for keyword in keywords:
            keyword_slug = slugify(keyword)
            logger.info("[Khối %d] Tìm '%s' (%s)...", block.index, keyword, "/".join(sorted(media_types)))

            google_images_url = build_google_images_url(keyword)

            if args.dry_run:
                manifest.append(
                    {
                        "block": block.index,
                        "title": block.title,
                        "keyword": keyword,
                        "media_types": sorted(media_types),
                        "google_images_url": google_images_url,
                        "downloaded": [],
                    }
                )
                continue

            hits = _search_keyword(providers, keyword, media_types, args.per_keyword, args.orientation, args.sleep)
            if not hits:
                logger.warning("  Không tìm thấy kết quả cho '%s'.", keyword)
                manifest.append(
                    {
                        "block": block.index,
                        "title": block.title,
                        "keyword": keyword,
                        "media_types": sorted(media_types),
                        "google_images_url": google_images_url,
                        "downloaded": [],
                    }
                )
                continue

            keyword_dir = block_dir / keyword_slug
            downloaded = []
            for i, item in enumerate(hits, start=1):
                stem = f"{item.source}_{item.media_type}_{item.id}_{i}"
                path = download_media(item, keyword_dir, stem)
                if path:
                    append_credit(block_dir / "credits.txt", item, path)
                    downloaded.append(
                        {"file": str(path.relative_to(output_dir)), "source": item.source, "media_type": item.media_type, "author": item.author, "page_url": item.page_url}
                    )
                    logger.info("  Đã tải: %s", path.relative_to(output_dir))

            manifest.append(
                {
                    "block": block.index,
                    "title": block.title,
                    "keyword": keyword,
                    "media_types": sorted(media_types),
                    "google_images_url": google_images_url,
                    "downloaded": downloaded,
                }
            )

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    n_downloaded = sum(len(m["downloaded"]) for m in manifest)
    logger.info("Xong. %d file đã tải (hoặc %d mục đã tìm nếu --dry-run). Manifest: %s", n_downloaded, len(manifest), manifest_path)
    return 0


if __name__ == "__main__":
    sys.exit(run())
