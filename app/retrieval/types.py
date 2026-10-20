from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk returned by retrieval, with the article context needed to cite it."""

    chunk_id: int
    article_id: int
    title: str
    url: str
    topic: str
    text: str
    position: int
    distance: float
