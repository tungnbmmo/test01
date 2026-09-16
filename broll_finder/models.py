from dataclasses import dataclass, field


@dataclass
class BrollBlock:
    """One script block (e.g. "Khối 1 - Hook") and the keywords to find footage for."""

    index: int
    title: str
    keywords: list[str] = field(default_factory=list)
    media_hint: set[str] = field(default_factory=lambda: {"video", "photo"})


@dataclass
class MediaResult:
    """A single search hit, normalized across providers."""

    source: str  # "pexels" | "pixabay"
    media_type: str  # "video" | "photo"
    id: str
    download_url: str
    page_url: str
    author: str
    width: int = 0
    height: int = 0
