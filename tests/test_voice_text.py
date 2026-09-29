from voice_clone.text import split_text


def test_split_merges_short_sentences():
    assert split_text("Xin chào. Tôi là Tùng.", 100) == ["Xin chào. Tôi là Tùng."]


def test_split_respects_max_chars():
    text = "Câu một khá dài. " * 30
    chunks = split_text(text, 80)
    assert all(len(c) <= 80 for c in chunks)
    assert " ".join(chunks).replace("  ", " ") == text.strip()


def test_long_sentence_is_cut():
    chunks = split_text("từ " * 200, 50)
    assert all(len(c) <= 50 for c in chunks)


def test_empty():
    assert split_text("  \n ") == []
