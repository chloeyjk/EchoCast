from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or `.env`."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True)

    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    openai_api_key: str
    openai_model: str = "gpt-6-luna"
    news_api_key: str

    embedding_model: str = "text-embedding-3-small"
    chunk_words: int = 600
    chunk_overlap_words: int = 75
    ingest_interval_minutes: int = 60
    ingest_articles_per_topic: int = 10

    retrieval_candidate_k: int = 20
    retrieval_final_k: int = 5

    redis_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
