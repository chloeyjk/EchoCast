import pytest
from pydantic import ValidationError

from app.config import Settings

REQUIRED = {
    "database_url": "postgresql+psycopg://u:p@localhost:5432/db",
    "secret_key": "s",
    "openai_api_key": "o",
    "news_api_key": "n",
}


def test_loads_values_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///x.db")
    monkeypatch.setenv("SECRET_KEY", "abc")
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    monkeypatch.setenv("NEWS_API_KEY", "n")

    settings = Settings(_env_file=None)

    assert settings.database_url == "sqlite:///x.db"
    assert settings.secret_key == "abc"


def test_applies_defaults_for_optional_values():
    settings = Settings(_env_file=None, **REQUIRED)

    assert settings.algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.redis_url == "redis://localhost:6379/0"


def test_raises_when_secret_key_is_missing(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    values = {k: v for k, v in REQUIRED.items() if k != "secret_key"}

    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)


def test_settings_are_immutable():
    settings = Settings(_env_file=None, **REQUIRED)

    with pytest.raises(ValidationError):
        settings.secret_key = "changed"
