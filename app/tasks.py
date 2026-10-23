import requests
from openai import OpenAI
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import PodcastPreference
from app.config import get_settings
from app.ingest import service as ingest_service
from app.ingest.embeddings import embed_texts
from app.ingest.fetcher import fetch_full_text
from app.retrieval.rerank import LLMReranker
from app.summarize import service as summarize_service
from app.summarize.writer import LLMWriter
from celery_app import celery_app

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)
NEWS_API_KEY = settings.news_api_key

# still keep your test
@celery_app.task(name="app.tasks.add")
def add(x, y):
    return x + y


@celery_app.task(name="app.tasks.summarize_topic")
def summarize_topic(topic):
    """Write and store a citation-grounded summary for one topic's ingested chunks."""
    db = SessionLocal()
    try:
        summary = summarize_service.summarize(
            db,
            topics=[topic],
            query=f"Latest news on {topic}",
            embed=lambda text: embed_texts(client, [text], model=settings.embedding_model)[0],
            reranker=LLMReranker(client, settings.openai_model),
            writer=LLMWriter(client, settings.openai_model),
            candidate_k=settings.retrieval_candidate_k,
            final_k=settings.retrieval_final_k,
        )
    finally:
        db.close()
    return f"Saved summary {summary.id} for {topic} with {len(summary.claims)} claims"


NEWS_REQUEST_TIMEOUT_SECONDS = 10


@celery_app.task(name="app.tasks.ingest_topics")
def ingest_topics():
    """Beat entry point: queue one ingest per distinct user preference topic."""
    db = SessionLocal()
    try:
        topics = sorted({row[0] for row in db.query(PodcastPreference.topic).distinct()})
    finally:
        db.close()
    for topic in topics:
        ingest_topic.delay(topic)
    return f"Queued {len(topics)} topics"


@celery_app.task(name="app.tasks.ingest_topic")
def ingest_topic(topic):
    url = f"https://newsapi.org/v2/top-headlines?apiKey={NEWS_API_KEY}&category={topic}&language=en"
    articles = requests.get(url, timeout=NEWS_REQUEST_TIMEOUT_SECONDS).json().get("articles", [])
    selected = articles[:settings.ingest_articles_per_topic]
    for article in selected:
        ingest_article.delay(article["title"], article["url"], topic, article.get("content"))
    return f"Queued {len(selected)} articles for {topic}"


@celery_app.task(name="app.tasks.ingest_article")
def ingest_article(title, url, topic, fallback_content):
    text = fetch_full_text(url) or fallback_content or ""
    db = SessionLocal()
    try:
        return ingest_service.ingest_article(
            db,
            title=title,
            url=url,
            topic=topic,
            text=text,
            embed=lambda texts: embed_texts(client, texts, model=settings.embedding_model),
            chunk_words=settings.chunk_words,
            overlap_words=settings.chunk_overlap_words,
        )
    finally:
        db.close()
