import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.retrieval.types import RetrievedChunk
from app.summarize import service
from app.summarize.types import GeneratedClaim
from app.summarize.validator import UngroundedClaimError


@pytest.fixture()
def session_factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    models.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)


@pytest.fixture()
def chunk_id(session_factory):
    with session_factory() as db:
        article = models.Article(
            url="https://example.com/a",
            title="A",
            topic="tech",
            content="body",
            content_hash="hash1",
        )
        db.add(article)
        db.flush()
        chunk = models.Chunk(article_id=article.id, position=0, text="chunk text", embedding=[0.0])
        db.add(chunk)
        db.commit()
        return chunk.id


def test_persist_summary_round_trip(session_factory, chunk_id):
    claims = [GeneratedClaim(text="Claim one.", source_chunk_id=chunk_id)]

    with session_factory() as db:
        summary = service.persist_summary(db, topic="tech", claims=claims)
        summary_id = summary.id

    with session_factory() as db:
        reloaded = db.query(models.Summary).filter_by(id=summary_id).one()
        assert reloaded.topic == "tech"
        assert [(c.text, c.source_chunk_id, c.position) for c in reloaded.claims] == [
            ("Claim one.", chunk_id, 0)
        ]


class FakeWriter:
    def __init__(self, claims):
        self.claims = claims
        self.calls = []

    def generate(self, query, chunks):
        self.calls.append((query, chunks))
        return self.claims


class RaisingWriter:
    def generate(self, query, chunks):
        raise UngroundedClaimError("invented id")


def fake_embed(query):
    return [1.0, 0.0]


class FakeReranker:
    def rerank(self, query, candidates, top_k):
        return candidates[:top_k]


def _fake_retrieved(chunk_id):
    return RetrievedChunk(
        chunk_id=chunk_id,
        article_id=1,
        title="A",
        url="https://example.com/a",
        topic="tech",
        text="chunk text",
        position=0,
        distance=0.1,
    )


def test_summarize_retrieves_writes_and_persists(monkeypatch, session_factory, chunk_id):
    retrieved = [_fake_retrieved(chunk_id)]
    monkeypatch.setattr(service.retrieval_service, "retrieve", lambda *a, **k: retrieved)
    writer = FakeWriter([GeneratedClaim(text="Claim.", source_chunk_id=chunk_id)])

    with session_factory() as db:
        summary = service.summarize(
            db,
            topics=["tech", "finance"],
            query="latest news",
            embed=fake_embed,
            reranker=FakeReranker(),
            writer=writer,
            candidate_k=5,
            final_k=3,
        )

        assert summary.topic == "tech,finance"
        assert writer.calls == [("latest news", retrieved)]
        assert [c.source_chunk_id for c in summary.claims] == [chunk_id]


def test_summarize_raises_without_calling_writer_when_nothing_retrieved(monkeypatch, session_factory):
    monkeypatch.setattr(service.retrieval_service, "retrieve", lambda *a, **k: [])
    writer = FakeWriter([])

    with session_factory() as db, pytest.raises(ValueError):
        service.summarize(
            db,
            topics=["tech"],
            query="latest news",
            embed=fake_embed,
            reranker=FakeReranker(),
            writer=writer,
            candidate_k=5,
            final_k=3,
        )

    assert writer.calls == []


def test_summarize_propagates_ungrounded_claim_error(monkeypatch, session_factory, chunk_id):
    monkeypatch.setattr(service.retrieval_service, "retrieve", lambda *a, **k: [_fake_retrieved(chunk_id)])

    with session_factory() as db, pytest.raises(UngroundedClaimError):
        service.summarize(
            db,
            topics=["tech"],
            query="latest news",
            embed=fake_embed,
            reranker=FakeReranker(),
            writer=RaisingWriter(),
            candidate_k=5,
            final_k=3,
        )
