import os
import requests
from openai import OpenAI
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ArticleSummary
from celery_app import celery_app
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

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
        model="gpt-4o-mini",
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
