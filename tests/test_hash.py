from app.vector_store import content_hash


def test_content_hash_is_deterministic():
    assert content_hash("hello") == content_hash("hello")
    assert content_hash("hello") != content_hash("world")
