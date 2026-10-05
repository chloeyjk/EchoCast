from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "podcast_tasks",
    broker=settings.redis_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.task_routes = {
    "app.tasks.fetch_news": {"queue": "news"},
    "app.tasks.summarize_article": {"queue": "summary"},
}
celery_app.autodiscover_tasks(["app"])
