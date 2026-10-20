from typing import Callable

from sqlalchemy.orm import Session

from app.retrieval.rerank import Reranker
from app.retrieval.search import make_searcher
from app.retrieval.types import RetrievedChunk

QueryEmbedder = Callable[[str], list[float]]


def retrieve(
    db: Session,
    *,
    topics: list[str],
    query: str,
    embed: QueryEmbedder,
    reranker: Reranker,
    candidate_k: int,
    final_k: int,
) -> list[RetrievedChunk]:
    """Return the best `final_k` chunks for `query` among the given topics."""
    if not topics:
        raise ValueError("topics must not be empty")
    if not query.strip():
        raise ValueError("query must not be blank")
    if candidate_k < final_k:
        raise ValueError("candidate_k must be >= final_k")

    query_embedding = embed(query)

    candidates = make_searcher(db).search(query_embedding, topics, candidate_k)
    if not candidates:
        return []

    return reranker.rerank(query, candidates, final_k)
