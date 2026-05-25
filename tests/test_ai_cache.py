from app.ai.cache import make_hash, get_cached, store_cached
from app.models.ai_cache import AiCache


def test_make_hash_is_deterministic():
    h1 = make_hash("hello world")
    h2 = make_hash("hello world")
    assert h1 == h2


def test_make_hash_is_sha256_hex():
    h = make_hash("test")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_make_hash_differs_for_different_inputs():
    assert make_hash("abc") != make_hash("xyz")


def test_get_cached_returns_none_on_miss(db):
    result = get_cached(db, "nonexistent_hash_xyz")
    assert result is None


def test_store_and_retrieve_cached_response(db):
    prompt = "What skills should I highlight for a Python role?"
    h = make_hash(prompt)
    store_cached(db, prompt_hash=h, cache_key="interview_10", response='{"topics": []}')
    db.commit()

    result = get_cached(db, h)
    assert result == '{"topics": []}'


def test_store_same_hash_twice_does_not_raise(db):
    h = make_hash("duplicate prompt")
    store_cached(db, prompt_hash=h, cache_key="key_a", response="first")
    db.commit()
    # Storing again with same cache_key should overwrite (upsert)
    store_cached(db, prompt_hash=h, cache_key="key_a", response="second")
    db.commit()
    result = get_cached(db, h)
    assert result == "second"


def test_cache_entry_stored_in_db(db):
    h = make_hash("stored check")
    store_cached(db, prompt_hash=h, cache_key="key_check", response="the response")
    db.commit()

    row = db.query(AiCache).filter_by(cache_key="key_check").first()
    assert row is not None
    assert row.response == "the response"
    assert row.prompt_hash == h
