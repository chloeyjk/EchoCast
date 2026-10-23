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


def test_summarize_topic_calls_summarize_service_and_closes_session(monkeypatch, session_factory):
    fake_summary = SimpleNamespace(id=7, claims=[object(), object()])
    summarize = MagicMock(return_value=fake_summary)
    monkeypatch.setattr(tasks.summarize_service, "summarize", summarize)
    close = MagicMock(wraps=session_factory().close)
    monkeypatch.setattr(tasks, "SessionLocal", lambda: SimpleNamespace(close=close))

    result = tasks.summarize_topic("technology")

    assert summarize.call_args.kwargs["topics"] == ["technology"]
    assert "technology" in summarize.call_args.kwargs["query"]
    assert close.called
    assert "7" in result
    assert "2" in result


def test_summarize_topic_closes_session_even_when_summarize_raises(monkeypatch, session_factory):
    monkeypatch.setattr(tasks.summarize_service, "summarize", MagicMock(side_effect=RuntimeError("boom")))
    close = MagicMock(wraps=session_factory().close)
    monkeypatch.setattr(tasks, "SessionLocal", lambda: SimpleNamespace(close=close))

    with pytest.raises(RuntimeError):
        tasks.summarize_topic("technology")

    assert close.called
