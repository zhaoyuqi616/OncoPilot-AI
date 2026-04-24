from oncopilot_ai.utils.text import chunk_text


def test_short_text_is_single_chunk():
    text = "hello world"
    chunks = chunk_text(text, chunk_size_words=10, overlap_words=2)
    assert chunks == ["hello world"]


def test_long_text_is_chunked():
    text = " ".join([f"w{i}" for i in range(50)])
    chunks = chunk_text(text, chunk_size_words=10, overlap_words=2)
    assert len(chunks) > 1
