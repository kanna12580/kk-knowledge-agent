from app.services.chunk_service import split_text


def test_split_text_prefers_paragraphs():
    chunks = split_text("第一段。\n\n第二段。", chunk_size=20, chunk_overlap=5)

    assert chunks == ["第一段。\n\n第二段。"]


def test_split_text_splits_long_paragraph_with_overlap():
    chunks = split_text("abcdefghij", chunk_size=4, chunk_overlap=1)

    assert chunks == ["abcd", "defg", "ghij", "j"]

