from typing import Callable

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ingest.chunking import chunk_text
from app.ingest.dedup import content_hash, normalize_url
from app.models import Article, Chunk

CREATED = "created"
DUPLICATE = "duplicate"
EMPTY = "empty"

Embedder = Callable[[list[str]], list[list[float]]]


def _already_stored(db: Session, url: str, digest: str) -> bool:
    match = db.query(Article.id).filter((Article.url == url) | (Article.content_hash == digest)).first()
    return match is not None


def ingest_article(
    db: Session,
    *,
    title: str,
    url: str,
    topic: str,
    text: str,
    embed: Embedder,
    chunk_words: int,
    overlap_words: int,
) -> str:
    """Store an article and its embedded chunks unless it is empty or already known."""
    body = text.strip()
    if not body:
        return EMPTY

    normalized = normalize_url(url)
    digest = content_hash(body)
    if _already_stored(db, normalized, digest):
        return DUPLICATE

    pieces = chunk_text(body, size=chunk_words, overlap=overlap_words)
    vectors = embed(pieces)

    article = Article(url=normalized, title=title, topic=topic, content=body, content_hash=digest)
    article.chunks = [
        Chunk(position=i, text=piece, embedding=vector)
        for i, (piece, vector) in enumerate(zip(pieces, vectors))
    ]
    db.add(article)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return DUPLICATE
    return CREATED
