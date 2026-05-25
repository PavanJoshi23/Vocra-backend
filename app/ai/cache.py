import hashlib

from sqlalchemy.orm import Session

from app.models.ai_cache import AiCache


def make_hash(prompt: str) -> str:
    """Return SHA256 hex digest of the prompt string."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def get_cached(db: Session, prompt_hash: str) -> str | None:
    """Return cached response for the given prompt hash, or None on miss."""
    row = db.query(AiCache).filter_by(prompt_hash=prompt_hash).first()
    return row.response if row else None


def store_cached(db: Session, prompt_hash: str, cache_key: str, response: str) -> None:
    """Insert or update a cache entry keyed by cache_key."""
    row = db.query(AiCache).filter_by(cache_key=cache_key).first()
    if row:
        row.prompt_hash = prompt_hash
        row.response = response
    else:
        db.add(AiCache(cache_key=cache_key, prompt_hash=prompt_hash, response=response))
