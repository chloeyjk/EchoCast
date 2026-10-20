import pytest

from app.retrieval import service
from app.retrieval.types import RetrievedChunk


def make_chunk(chunk_id, distance=0.1):
    return RetrievedChunk(
        chunk_id=chunk_id,
        article_id=1,
        title="T",
        url="https://a.com",
        topic="tech",
        text="t",
        position=0,
        distance=distance,
    )


class FakeSearcher:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def search(self, query_embedding, topics, limit):
        self.calls.append((query_embedding, topics, limit))
        return self.results[:limit]


class FakeReranker:
    def __init__(self):
        self.calls = []

    def rerank(self, query, candidates, top_k):
        self.calls.append((query, candidates, top_k))
        return candidates[:top_k]


def fake_embed(query):
    return [1.0, 0.0]


def test_rejects_empty_topics():
    with pytest.raises(ValueError):
        service.retrieve(
            None, topics=[], query="q", embed=fake_embed, reranker=FakeReranker(), candidate_k=5, final_k=5
        )


def test_rejects_blank_query():
    with pytest.raises(ValueError):
        service.retrieve(
            None, topics=["tech"], query="   ", embed=fake_embed, reranker=FakeReranker(), candidate_k=5, final_k=5
        )


def test_rejects_candidate_k_less_than_final_k():
    with pytest.raises(ValueError):
        service.retrieve(
            None, topics=["tech"], query="q", embed=fake_embed, reranker=FakeReranker(), candidate_k=2, final_k=5
        )


def test_embed_errors_propagate():
    def broken(query):
        raise RuntimeError("embedding down")

    with pytest.raises(RuntimeError):
        service.retrieve(
            None, topics=["tech"], query="q", embed=broken, reranker=FakeReranker(), candidate_k=5, final_k=3
        )


def test_returns_empty_without_calling_reranker_when_nothing_matches(monkeypatch):
    searcher = FakeSearcher([])
    monkeypatch.setattr(service, "make_searcher", lambda db: searcher)
    reranker = FakeReranker()

    result = service.retrieve(
        None, topics=["tech"], query="q", embed=fake_embed, reranker=reranker, candidate_k=5, final_k=3
    )

    assert result == []
    assert reranker.calls == []


def test_passes_candidate_k_to_search_and_returns_final_k(monkeypatch):
    candidates = [make_chunk(i) for i in range(5)]
    searcher = FakeSearcher(candidates)
    monkeypatch.setattr(service, "make_searcher", lambda db: searcher)
    reranker = FakeReranker()

    result = service.retrieve(
        None, topics=["tech"], query="q", embed=fake_embed, reranker=reranker, candidate_k=5, final_k=3
    )

    assert searcher.calls == [([1.0, 0.0], ["tech"], 5)]
    assert reranker.calls[0][2] == 3
    assert [c.chunk_id for c in result] == [0, 1, 2]
