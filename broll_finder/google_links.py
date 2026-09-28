"""Build ready-to-click Google Images search links for B-roll keywords.

Google has no free official API for downloading arbitrary web images for reuse —
images found this way generally belong to the original site (news outlets,
blogs, etc.), not a royalty-free stock library. So instead of scraping or
auto-downloading, this module only builds the search URL; a person opens it,
checks the source/rights of whichever photo they want, and saves it themselves.
"""

from pathlib import Path
from urllib.parse import urlencode

from .models import BrollBlock


def build_google_images_url(keyword: str, *, large_only: bool = True) -> str:
    params = {"tbm": "isch", "q": keyword}
    if large_only:
        params["tbs"] = "isz:l"
    return "https://www.google.com/search?" + urlencode(params)


def write_google_links_file(blocks: list[BrollBlock], path: Path) -> None:
    lines = ["# Link tìm Google Hình ảnh theo từ khóa B-roll", ""]
    lines.append(
        "Bấm từng link để mở Google Hình ảnh, tự chọn và tải ảnh phù hợp — "
        "kiểm tra nguồn/quyền sử dụng trước khi dùng vào video."
    )
    lines.append("")

    for block in blocks:
        lines.append(f"## Khối {block.index} — {block.title}")
        lines.append("")
        for keyword in block.keywords:
            url = build_google_images_url(keyword)
            lines.append(f"- [{keyword}]({url})")
        lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
