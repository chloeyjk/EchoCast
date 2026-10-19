from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models, tasks
from celery_app import celery_app


@pytest.fixture()
def session_factory(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    models.Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(tasks, "SessionLocal", factory)
    return factory


def test_ingest_topics_queues_each_distinct_preference_topic_once(session_factory, monkeypatch):
    with session_factory() as db:
        db.add_all([models.PodcastPreference(topic=t) for t in ["science", "health", "science"]])
        db.commit()
    delay = MagicMock()
    monkeypatch.setattr(tasks.ingest_topic, "delay", delay)

    tasks.ingest_topics()

    assert sorted(c.args[0] for c in delay.call_args_list) == ["health", "science"]


def test_ingest_topic_queues_ingest_for_each_headline(monkeypatch):
    articles = [{"title": f"t{i}", "url": f"u{i}", "content": "c"} for i in range(3)]
    monkeypatch.setattr(tasks.requests, "get", lambda url, **kw: MagicMock(json=lambda: {"articles": articles}))
    delay = MagicMock()
    monkeypatch.setattr(tasks.ingest_article, "delay", delay)

    result = tasks.ingest_topic("science")

    assert delay.call_count == 3
    assert "science" in result


def test_ingest_article_falls_back_to_newsapi_content_when_fetch_fails(session_factory, monkeypatch):
    monkeypatch.setattr(tasks, "fetch_full_text", lambda url: None)
    monkeypatch.setattr(tasks, "embed_texts", lambda client, texts, model: [[0.0]] * len(texts))

    result = tasks.ingest_article("Title", "https://a.com/x", "science", "fallback body text")

    assert result == "created"
    with session_factory() as db:
        assert db.query(models.Article).one().content == "fallback body text"


def test_ingest_article_reports_duplicate(session_factory, monkeypatch):
    monkeypatch.setattr(tasks, "fetch_full_text", lambda url: "some article body")
    monkeypatch.setattr(tasks, "embed_texts", lambda client, texts, model: [[0.0]] * len(texts))

    tasks.ingest_article("Title", "https://a.com/x", "science", None)
    result = tasks.ingest_article("Title", "https://a.com/x", "science", None)

    assert result == "duplicate"


def test_beat_schedule_runs_ingest_topics_at_configured_interval():
    entry = celery_app.conf.beat_schedule["ingest-topics"]

    assert entry["task"] == "app.tasks.ingest_topics"
    assert entry["schedule"] == tasks.settings.ingest_interval_minutes * 60
