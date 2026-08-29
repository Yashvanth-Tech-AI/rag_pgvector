from app.text_splitter import split_text


def test_split_text_creates_chunks():
    text = "a" * 1000
    chunks = split_text(text, chunk_size=200, chunk_overlap=20)

    assert len(chunks) > 1
    assert all(len(chunk) <= 200 for chunk in chunks)
