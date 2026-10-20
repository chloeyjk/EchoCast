import math
from typing import Protocol, Sequence

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import Article, Chunk
from app.retrieval.types import RetrievedChunk


class ChunkSearcher(Protocol):
    def search(self, query_embedding: Sequence[float], topics: list[str], limit: int) -> list[RetrievedChunk]: ...


def _to_retrieved_chunk(chunk: Chunk, article: Article, distance: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk.id,
        article_id=article.id,
        title=article.title,
        url=article.url,
        topic=article.topic,
        text=chunk.text,
        position=chunk.position,
        distance=distance,
    )


class PgVectorSearcher:
    """Nearest-neighbor search over `chunks.embedding` using pgvector's cosine distance."""

    def __init__(self, db: Session):
        self._db = db

    def search(self, query_embedding: Sequence[float], topics: list[str], limit: int) -> list[RetrievedChunk]:
        # relaxed_order trades a small amount of recall for a much faster HNSW scan; needs pgvector 0.8+.
        self._db.execute(text("SET LOCAL hnsw.iterative_scan = 'relaxed_order'"))
        distance = Chunk.embedding.cosine_distance(list(query_embedding))
        stmt = (
            select(Chunk, Article, distance.label("distance"))
            .join(Article, Chunk.article_id == Article.id)
            .where(Article.topic.in_(topics))
            .order_by(distance, Chunk.id)
            .limit(limit)
        )
        rows = self._db.execute(stmt).all()
        return [_to_retrieved_chunk(chunk, article, float(dist)) for chunk, article, dist in rows]


def _cosine_distance(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 1.0
    return 1.0 - dot / (norm_a * norm_b)


class InMemorySearcher:
    """Same ordering as `PgVectorSearcher`, computed in Python; used on SQLite."""

    def __init__(self, db: Session):
        self._db = db

    def search(self, query_embedding: Sequence[float], topics: list[str], limit: int) -> list[RetrievedChunk]:
        rows = (
            self._db.query(Chunk, Article)
            .join(Article, Chunk.article_id == Article.id)
            .filter(Article.topic.in_(topics))
            .all()
        )
        scored = [(_cosine_distance(query_embedding, chunk.embedding), chunk, article) for chunk, article in rows]
        scored.sort(key=lambda item: (item[0], item[1].id))
        return [_to_retrieved_chunk(chunk, article, distance) for distance, chunk, article in scored[:limit]]


def make_searcher(db: Session) -> ChunkSearcher:
    """Pick the searcher implementation matching the bound database dialect."""
    if db.bind.dialect.name == "postgresql":
        return PgVectorSearcher(db)
    return InMemorySearcher(db)
