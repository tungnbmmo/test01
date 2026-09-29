"""Chia văn bản dài thành các đoạn ngắn để XTTS đọc ổn định."""
import re

_SENT_SPLIT = re.compile(r"(?<=[.!?…。])\s+|\n+")


def split_text(text: str, max_chars: int = 220) -> list[str]:
    """Tách theo câu, gộp các câu ngắn cho tới ~max_chars ký tự mỗi đoạn."""
    sentences = [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]
    chunks: list[str] = []
    cur = ""
    for s in sentences:
        # Câu quá dài: cắt tiếp theo dấu phẩy / khoảng trắng.
        while len(s) > max_chars:
            cut = max(s.rfind(",", 0, max_chars), s.rfind(" ", 0, max_chars))
            cut = cut if cut > 0 else max_chars
            piece, s = s[:cut + 1].strip(), s[cut + 1:].strip()
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(piece)
        if cur and len(cur) + 1 + len(s) > max_chars:
            chunks.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        chunks.append(cur)
    return chunks
