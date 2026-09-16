import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from broll_finder.parser import parse_input, slugify

TINVIET_TABLE = """
| Khối | Nội dung khối (tóm tắt) | Từ khóa VN (cho Google Hình ảnh/YouTube) | Loại tư liệu gợi ý |
|------|--------------------------|-------------------------------------------|----------------------|
| 1 | Hook mở đầu | "họp báo doanh nhân", lừa đảo, mặt nạ rơi khỏi tượng | stock footage / motion graphic |
| 2 | Bối cảnh | đếm tiền cận cảnh; biểu đồ tăng trưởng | stock photo |
"""

HEADING_LIST = """
## Khối 1: Hook mở đầu
- họp báo doanh nhân
- lừa đảo

## Khối 2: Bối cảnh
- đếm tiền cận cảnh
"""

FLAT_LIST = """
đếm tiền cận cảnh
biểu đồ tăng trưởng
hành lang bệnh viện vắng
"""


def test_parse_markdown_table():
    blocks = parse_input(TINVIET_TABLE)
    assert len(blocks) == 2
    assert blocks[0].index == 1
    assert blocks[0].keywords == ["họp báo doanh nhân", "lừa đảo", "mặt nạ rơi khỏi tượng"]
    assert blocks[0].media_hint == {"video"}
    assert blocks[1].media_hint == {"photo"}


def test_parse_headings():
    blocks = parse_input(HEADING_LIST)
    assert len(blocks) == 2
    assert blocks[0].title == "Hook mở đầu"
    assert blocks[0].keywords == ["họp báo doanh nhân", "lừa đảo"]
    assert blocks[1].keywords == ["đếm tiền cận cảnh"]


def test_parse_flat_list():
    blocks = parse_input(FLAT_LIST)
    assert len(blocks) == 1
    assert len(blocks[0].keywords) == 3


def test_parse_json():
    data = json.dumps([{"block": 1, "title": "Hook", "keywords": ["a", "b"], "media_type": "video"}])
    blocks = parse_input(data, file_hint="keywords.json")
    assert len(blocks) == 1
    assert blocks[0].keywords == ["a", "b"]
    assert blocks[0].media_hint == {"video"}


def test_slugify():
    assert slugify("họp báo doanh nhân") == "hop_bao_doanh_nhan"
    assert slugify("") == "keyword"


if __name__ == "__main__":
    test_parse_markdown_table()
    test_parse_headings()
    test_parse_flat_list()
    test_parse_json()
    test_slugify()
    print("OK")
