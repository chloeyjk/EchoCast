import os
from celery import Celery
from dotenv import load_dotenv
load_dotenv()
celery_app = Celery(
    "podcast_tasks",
    broker="redis://localhost:6379/0",   # Redis broker
    backend="redis://localhost:6379/1"   # Redis backend (optional)
)

celery_app.conf.task_routes = {
    "tasks.fetch_news": {"queue": "news"},
    "tasks.summarize_article": {"queue": "summary"},
}
celery_app.autodiscover_tasks(["app"])