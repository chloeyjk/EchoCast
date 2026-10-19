import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.ingest import service

WORDS = " ".join(f"word{i}" for i in range(30))


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    models.Base.metadata.create_all(bind=engine)
    with sessionmaker(bind=engine)() as session:
        yield session


def fake_embed(texts):
    return [[float(len(t)), 0.0] for t in texts]


def ingest(db, url="https://a.com/story", text=WORDS, embed=fake_embed, **kwargs):
    return service.ingest_article(
        db, title="T", url=url, topic="technology", text=text,
        embed=embed, chunk_words=10, overlap_words=2, **kwargs,
    )


def test_creates_article_with_embedded_chunks(db):
    outcome = ingest(db)

    article = db.query(models.Article).one()
    chunks = db.query(models.Chunk).order_by(models.Chunk.position).all()
    assert outcome == service.CREATED
    assert article.topic == "technology"
    assert [c.position for c in chunks] == list(range(len(chunks)))
    assert len(chunks) == 4
    assert all(c.embedding is not None for c in chunks)


def test_duplicate_url_creates_no_second_article_and_skips_embedding(db):
    ingest(db)
    calls = []

    outcome = ingest(db, url="https://A.com/story/?utm_source=x", embed=lambda t: calls.append(t) or [])

    assert outcome == service.DUPLICATE
    assert db.query(models.Article).count() == 1
    assert calls == []


def test_same_text_at_a_different_url_is_a_duplicate(db):
    ingest(db, url="https://a.com/one")

    outcome = ingest(db, url="https://b.com/two")

    assert outcome == service.DUPLICATE
    assert db.query(models.Article).count() == 1


def test_blank_text_is_skipped(db):
    outcome = ingest(db, text="   ")

    assert outcome == service.EMPTY
    assert db.query(models.Article).count() == 0


def test_embedding_failure_leaves_no_partial_rows(db):
    def broken(texts):
        raise RuntimeError("openai down")

    with pytest.raises(RuntimeError):
        ingest(db, embed=broken)

    assert db.query(models.Article).count() == 0
    assert db.query(models.Chunk).count() == 0
