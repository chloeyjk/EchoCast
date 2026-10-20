import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.retrieval.search import InMemorySearcher, PgVectorSearcher, make_searcher


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    models.Base.metadata.create_all(bind=engine)
    with sessionmaker(bind=engine)() as session:
        yield session


def add_chunk(db, *, topic, embedding, url, title="T", text="chunk text", position=0):
    article = db.query(models.Article).filter_by(url=url).one_or_none()
    if article is None:
        article = models.Article(url=url, title=title, topic=topic, content=text, content_hash=f"hash-{url}")
        db.add(article)
        db.flush()
    chunk = models.Chunk(article_id=article.id, position=position, text=text, embedding=embedding)
    db.add(chunk)
    db.commit()
    return chunk


def test_make_searcher_picks_in_memory_for_sqlite(db):
    assert isinstance(make_searcher(db), InMemorySearcher)


class _FakeDialect:
    def __init__(self, name):
        self.name = name


class _FakeBind:
    def __init__(self, dialect_name):
        self.dialect = _FakeDialect(dialect_name)


class _FakeDb:
    def __init__(self, dialect_name):
        self.bind = _FakeBind(dialect_name)


def test_make_searcher_picks_pgvector_for_postgresql():
    assert isinstance(make_searcher(_FakeDb("postgresql")), PgVectorSearcher)


def test_nearest_first(db):
    add_chunk(db, topic="tech", embedding=[1.0, 0.0], url="https://a.com/1")
    add_chunk(db, topic="tech", embedding=[0.0, 1.0], url="https://a.com/2")
    add_chunk(db, topic="tech", embedding=[0.9, 0.1], url="https://a.com/3")

    results = make_searcher(db).search([1.0, 0.0], ["tech"], limit=3)

    assert [r.url for r in results] == ["https://a.com/1", "https://a.com/3", "https://a.com/2"]
    assert results[0].distance <= results[1].distance <= results[2].distance


def test_excludes_other_topics(db):
    add_chunk(db, topic="tech", embedding=[1.0, 0.0], url="https://a.com/1")
    add_chunk(db, topic="sports", embedding=[1.0, 0.0], url="https://a.com/2")

    results = make_searcher(db).search([1.0, 0.0], ["tech"], limit=10)

    assert [r.url for r in results] == ["https://a.com/1"]


def test_respects_limit_and_returns_fewer_when_fewer_match(db):
    add_chunk(db, topic="tech", embedding=[1.0, 0.0], url="https://a.com/1")
    add_chunk(db, topic="tech", embedding=[0.0, 1.0], url="https://a.com/2")

    assert len(make_searcher(db).search([1.0, 0.0], ["tech"], limit=1)) == 1
    assert len(make_searcher(db).search([1.0, 0.0], ["tech"], limit=10)) == 2


def test_deterministic_ties_break_by_chunk_id(db):
    c1 = add_chunk(db, topic="tech", embedding=[1.0, 0.0], url="https://a.com/1")
    c2 = add_chunk(db, topic="tech", embedding=[1.0, 0.0], url="https://a.com/2")

    results = make_searcher(db).search([1.0, 0.0], ["tech"], limit=2)

    assert [r.chunk_id for r in results] == sorted([c1.id, c2.id])


def test_matches_only_requested_topics_among_several(db):
    add_chunk(db, topic="tech", embedding=[1.0, 0.0], url="https://a.com/1")
    add_chunk(db, topic="sports", embedding=[1.0, 0.0], url="https://a.com/2")
    add_chunk(db, topic="finance", embedding=[1.0, 0.0], url="https://a.com/3")

    results = make_searcher(db).search([1.0, 0.0], ["tech", "finance"], limit=10)

    assert sorted(r.url for r in results) == ["https://a.com/1", "https://a.com/3"]
