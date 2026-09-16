"""Parse a B-roll keyword input file into a list of BrollBlock.

Supported formats (auto-detected from content):
  1. Markdown table, e.g. the "Bước 6" table the `tinviet` skill outputs:
         | Khối | Nội dung khối (tóm tắt) | Từ khóa VN (...) | Loại tư liệu gợi ý |
         |------|--------------------------|-------------------|-----------------------|
         | 1    | ...                      | kw1, kw2, "kw 3"  | stock footage / photo |
  2. Heading + bullet list:
         ## Khối 1: Hook
         - keyword one
         - keyword two
  3. JSON: [{"block": 1, "title": "...", "keywords": ["kw1", "kw2"], "media_type": "video"}]
  4. Flat text: one keyword per non-empty line (no blocks).
"""

import json
import re
import unicodedata

from .models import BrollBlock

_KEYWORD_SPLIT_RE = re.compile(r"[,;]")
_QUOTE_CHARS = '"“”‘’\''


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_text).strip("_").lower()
    return slug or "keyword"


def _clean_keyword(raw: str) -> str:
    return raw.strip().strip(_QUOTE_CHARS).strip()


def _split_keywords(cell: str) -> list[str]:
    parts = [_clean_keyword(p) for p in _KEYWORD_SPLIT_RE.split(cell)]
    return [p for p in parts if p]


def _detect_media_hint(cell: str) -> set[str]:
    text = cell.lower()
    hint = set()
    if any(w in text for w in ("video", "footage", "clip")):
        hint.add("video")
    if any(w in text for w in ("photo", "ảnh", "image", "picture")):
        hint.add("photo")
    return hint or {"video", "photo"}


def _is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in cells if c.strip())


def _parse_markdown_table(text: str) -> list[BrollBlock]:
    rows = [
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith("|") and line.strip().endswith("|")
    ]
    if not rows:
        return []

    header_cells = [c.strip() for c in rows[0].strip("|").split("|")]
    header_lower = [c.lower() for c in header_cells]

    def find_col(*needles: str) -> int:
        for i, h in enumerate(header_lower):
            if any(n in h for n in needles):
                return i
        return -1

    block_col = find_col("khối", "block")
    title_col = find_col("nội dung", "tóm tắt", "title", "content")
    keyword_col = find_col("từ khóa", "keyword")
    media_col = find_col("loại", "tư liệu", "type")

    if keyword_col == -1:
        return []

    blocks: list[BrollBlock] = []
    data_rows = rows[1:]
    auto_index = 0
    for row in data_rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        if _is_separator_row(cells):
            continue
        if keyword_col >= len(cells):
            continue

        auto_index += 1
        raw_block_num = cells[block_col].strip() if 0 <= block_col < len(cells) else ""
        try:
            index = int(re.sub(r"\D", "", raw_block_num) or auto_index)
        except ValueError:
            index = auto_index

        title = cells[title_col].strip() if 0 <= title_col < len(cells) else f"Khối {index}"
        keywords = _split_keywords(cells[keyword_col])
        media_hint = (
            _detect_media_hint(cells[media_col]) if 0 <= media_col < len(cells) else {"video", "photo"}
        )

        if keywords:
            blocks.append(BrollBlock(index=index, title=title or f"Khối {index}", keywords=keywords, media_hint=media_hint))

    return blocks


def _parse_headings(text: str) -> list[BrollBlock]:
    blocks: list[BrollBlock] = []
    current: BrollBlock | None = None
    auto_index = 0

    heading_re = re.compile(r"^#{1,6}\s*(?:khối\s*)?(\d+)?\s*[:.\-]?\s*(.*)$", re.IGNORECASE)
    bullet_re = re.compile(r"^[-*•]\s*(.+)$")

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        heading_match = heading_re.match(stripped) if stripped.startswith("#") else None
        if heading_match:
            auto_index += 1
            index = int(heading_match.group(1)) if heading_match.group(1) else auto_index
            title = heading_match.group(2).strip() or f"Khối {index}"
            current = BrollBlock(index=index, title=title)
            blocks.append(current)
            continue

        bullet_match = bullet_re.match(stripped)
        if bullet_match:
            keyword = _clean_keyword(bullet_match.group(1))
            if not keyword:
                continue
            if current is None:
                auto_index += 1
                current = BrollBlock(index=auto_index, title=f"Khối {auto_index}")
                blocks.append(current)
            current.keywords.append(keyword)

    return [b for b in blocks if b.keywords]


def _parse_json(text: str) -> list[BrollBlock]:
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("JSON input must be a list of block objects.")

    blocks = []
    for i, item in enumerate(data, start=1):
        keywords = item.get("keywords") or []
        if isinstance(keywords, str):
            keywords = _split_keywords(keywords)
        media_type = item.get("media_type") or item.get("media_hint")
        media_hint = _detect_media_hint(media_type) if isinstance(media_type, str) else {"video", "photo"}
        if isinstance(media_type, list):
            media_hint = set(media_type) & {"video", "photo"} or {"video", "photo"}

        blocks.append(
            BrollBlock(
                index=int(item.get("block", i)),
                title=str(item.get("title", f"Khối {i}")),
                keywords=[_clean_keyword(k) for k in keywords if _clean_keyword(k)],
                media_hint=media_hint,
            )
        )
    return [b for b in blocks if b.keywords]


def _parse_flat_list(text: str) -> list[BrollBlock]:
    keywords = [_clean_keyword(line) for line in text.splitlines()]
    keywords = [k for k in keywords if k]
    if not keywords:
        return []
    return [BrollBlock(index=1, title="Từ khóa", keywords=keywords)]


def parse_input(text: str, file_hint: str = "") -> list[BrollBlock]:
    """Auto-detect the input format and parse it into BrollBlocks."""

    stripped = text.strip()
    if not stripped:
        return []

    if file_hint.endswith(".json") or stripped.startswith("[") or stripped.startswith("{"):
        try:
            return _parse_json(stripped)
        except (json.JSONDecodeError, ValueError):
            pass

    table_blocks = _parse_markdown_table(text)
    if table_blocks:
        return table_blocks

    heading_blocks = _parse_headings(text)
    if heading_blocks:
        return heading_blocks

    return _parse_flat_list(text)
