from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models, tasks


@pytest.fixture()
def session_factory(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    models.Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(tasks, "SessionLocal", factory)
    return factory


def _fake_completion(text):
    message = SimpleNamespace(content=text)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_fetch_news_queues_at_most_five_articles(monkeypatch):
    articles = [{"title": f"t{i}", "url": f"u{i}", "content": "c"} for i in range(8)]
    monkeypatch.setattr(tasks.requests, "get", lambda url: MagicMock(json=lambda: {"articles": articles}))
    delay = MagicMock()
    monkeypatch.setattr(tasks.summarize_article, "delay", delay)

    result = tasks.fetch_news("technology")

    assert delay.call_count == 5
    assert "technology" in result


def test_summarize_article_skips_empty_content(session_factory):
    assert tasks.summarize_article("title", "url", None) is None


def test_summarize_article_persists_summary_using_configured_model(monkeypatch, session_factory):
    create = MagicMock(return_value=_fake_completion("  short summary  "))
    monkeypatch.setattr(tasks.client.chat.completions, "create", create)

    tasks.summarize_article("Title", "http://x", "body text")

    assert create.call_args.kwargs["model"] == tasks.settings.openai_model
    with session_factory() as db:
        saved = db.query(models.ArticleSummary).one()
    assert (saved.title, saved.summary) == ("Title", "short summary")
