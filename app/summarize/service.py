from typing import Callable, Protocol

from sqlalchemy.orm import Session

from app.models import Claim, Summary
from app.retrieval import service as retrieval_service
from app.retrieval.rerank import Reranker
from app.retrieval.types import RetrievedChunk
from app.summarize.types import GeneratedClaim

QueryEmbedder = Callable[[str], list[float]]


class ClaimWriter(Protocol):
    def generate(self, query: str, chunks: list[RetrievedChunk]) -> list[GeneratedClaim]: ...


def persist_summary(db: Session, *, topic: str, claims: list[GeneratedClaim]) -> Summary:
    """Store a summary and its claims, each keeping the chunk id it cites."""
    summary = Summary(topic=topic)
    db.add(summary)
    db.flush()
    for position, claim in enumerate(claims):
        db.add(
            Claim(
                summary_id=summary.id,
                text=claim.text,
                source_chunk_id=claim.source_chunk_id,
                position=position,
            )
        )
    db.commit()
    db.refresh(summary)
    return summary


def summarize(
    db: Session,
    *,
    topics: list[str],
    query: str,
    embed: QueryEmbedder,
    reranker: Reranker,
    writer: ClaimWriter,
    candidate_k: int,
    final_k: int,
) -> Summary:
    """Retrieve chunks for `query`, write grounded claims, and persist the result."""
    chunks = retrieval_service.retrieve(
        db,
        topics=topics,
        query=query,
        embed=embed,
        reranker=reranker,
        candidate_k=candidate_k,
        final_k=final_k,
    )
    if not chunks:
        raise ValueError("no chunks retrieved for the given topics/query")

    claims = writer.generate(query, chunks)
    return persist_summary(db, topic=",".join(topics), claims=claims)
