import requests
from openai import OpenAI
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ArticleSummary
from app.config import get_settings
from celery_app import celery_app

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)
NEWS_API_KEY = settings.news_api_key

# still keep your test
@celery_app.task(name="app.tasks.add")
def add(x, y):
    return x + y

@celery_app.task(name="app.tasks.fetch_news")
def fetch_news(topic="technology"):
    url = f"https://newsapi.org/v2/top-headlines?apiKey={NEWS_API_KEY}&category={topic}&language=en"
    resp = requests.get(url).json()
    articles = resp.get("articles", [])
    for article in articles[:5]:
        summarize_article.delay(article["title"], article["url"], article["content"])
    return f"Queued {len(articles)} articles for {topic}"

@celery_app.task(name="app.tasks.summarize_article")
def summarize_article(title, url, content):
    if not content:
        return None
    resp = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": f"Summarize this article:\n\n{content}"}],
        max_tokens=150,
    )
    summary = resp.choices[0].message.content.strip()

    db = SessionLocal()
    try:
        article_obj = ArticleSummary(title=title, url=url, summary=summary)
        db.add(article_obj)
        db.commit()
    finally:
        db.close()
    return f"Saved summary for {title}"
