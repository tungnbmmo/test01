import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from broll_finder.google_links import build_google_images_url, write_google_links_file
from broll_finder.models import BrollBlock


def test_build_google_images_url():
    url = build_google_images_url("tiệm vàng Đắk Lắk")
    assert url.startswith("https://www.google.com/search?")
    assert "tbm=isch" in url
    assert "tbs=isz%3Al" in url


def test_write_google_links_file(tmp_path):
    blocks = [BrollBlock(index=1, title="Hook", keywords=["kw one", "kw two"])]
    out_path = tmp_path / "google_links.md"
    write_google_links_file(blocks, out_path)

    content = out_path.read_text(encoding="utf-8")
    assert "Khối 1 — Hook" in content
    assert "kw one" in content
    assert "https://www.google.com/search?" in content


if __name__ == "__main__":
    test_build_google_images_url()
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        test_write_google_links_file(Path(d))
    print("OK")
