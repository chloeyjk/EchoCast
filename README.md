# EchoCast - Podcast Backend API

A backend service for personalized podcast content generation, featuring JWT authentication, asynchronous task processing, and AI-powered article summarization.

## 🚀 Features

- **User Authentication & Authorization**: JWT-based secure authentication with OAuth2 password flow
- **User Preference Management**: Store and retrieve personalized podcast topic preferences
- **Asynchronous News Aggregation**: Celery-powered background tasks for fetching news from multiple categories
- **AI-Powered Summarization**: OpenAI LLM integration (configurable via `OPENAI_MODEL`, default `gpt-6-luna`) for intelligent article summarization
- **RESTful API**: Clean, well-documented endpoints built with FastAPI
- **Database Migration Support**: Alembic for version-controlled schema management

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: SQLAlchemy ORM with PostgreSQL/SQLite
- **Authentication**: JWT (python-jose), OAuth2, Passlib (bcrypt)
- **Task Queue**: Celery with Redis broker
- **AI Integration**: OpenAI (`gpt-6-luna` by default)
- **External API**: NewsAPI for real-time news fetching
- **Migration Tool**: Alembic

## 📋 Prerequisites

- Python 3.12+
- Redis (for Celery broker)
- OpenAI API key
- NewsAPI key

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/chloeyjk/EchoCast.git
   cd podcast_backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install fastapi uvicorn sqlalchemy alembic celery redis openai python-jose passlib python-multipart httpx python-dotenv
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your_secret_key_here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   OPENAI_API_KEY=your_openai_api_key
   NEWS_API_KEY=your_news_api_key
   DATABASE_URL=sqlite:///./podcast.db
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

## 🐳 Quick Start with Docker

```bash
cp .env.example .env   # fill in SECRET_KEY, OPENAI_API_KEY, NEWS_API_KEY
docker compose up --build
```

This starts PostgreSQL (with the `pgvector` extension), Redis, the FastAPI service
(http://localhost:8000/docs, migrations run on startup) a Celery worker and a Celery beat scheduler.

Run the tests locally with `pip install -r requirements-dev.txt && pytest --cov=app`.

## 🚦 Running the Application

1. **Start Redis server**
   ```bash
   redis-server
   ```

2. **Start Celery worker**
   ```bash
   celery -A celery_app worker --loglevel=info
   ```

3. **Start FastAPI server**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

Interactive API documentation: `http://localhost:8000/docs`

## 📡 API Endpoints

### Authentication
- `POST /register` - Register a new user
- `POST /token` - Login and receive JWT access token

### User Preferences
- `POST /preferences` - Add a new podcast topic preference (authenticated)
- `GET /preferences` - Retrieve user's topic preferences (authenticated)

### Background Tasks
- News fetching and summarization run asynchronously via Celery
- Celery beat runs `ingest_topics` every `INGEST_INTERVAL_MINUTES` (default 60): for each user preference topic it fetches headlines, downloads the full article text, skips articles whose normalized URL or text hash is already stored, splits the text into overlapping chunks, embeds them, and saves `articles` and `chunks` (pgvector)
- `summarize_topic` retrieves grounded chunks for a topic, has the configured OpenAI model write citation-backed claims, and persists them as a `Summary` and its `Claim`s

### Retrieval
`app/retrieval` is an internal library (no HTTP endpoint yet) that, given a user's
topics and a query string, returns the best matching chunks for grounding a summary:
1. Embed the query and fetch the `RETRIEVAL_CANDIDATE_K` nearest chunks (default 20)
   whose article topic is in the requested list, ordered by pgvector cosine distance
   (an HNSW index backs this on Postgres; plain Python cosine distance is used on SQLite).
2. Re-rank the candidates with an LLM call and keep the top `RETRIEVAL_FINAL_K` (default 5).
   Any re-ranker failure (bad JSON, wrong length, out-of-range score, API error) falls back
   to the vector order.

### Citation-grounded summaries
`app/summarize` turns retrieved chunks into claims that can't drift from their sources:
1. `LLMWriter` asks the model for one claim per line, each ending in the `[chunk_id]` of the
   single chunk it's grounded in, with the candidate chunk text wrapped in delimiters the
   model is told to treat as data, not instructions.
2. The response is parsed into `GeneratedClaim`s and validated against the retrieved chunk
   ids — any claim citing an id outside that set raises `UngroundedClaimError` instead of
   being silently dropped or made up.
3. Validated claims are persisted as a `Summary` row with child `Claim` rows, each keeping
   its `source_chunk_id` for later display or fact-checking.

## 🏗️ Architecture

```
podcast_backend/
├── app/
│   ├── main.py         # FastAPI application and route definitions
│   ├── models.py       # SQLAlchemy database models
│   ├── schemas.py      # Pydantic schemas for request/response validation
│   ├── auth.py         # JWT authentication and password hashing
│   ├── crud.py         # Database CRUD operations
│   ├── database.py     # Database connection and session management
│   ├── tasks.py        # Celery background tasks
│   ├── ingest/         # Fetching, dedup, chunking and embedding of articles
│   ├── retrieval/      # Nearest-chunk search and LLM re-ranking over embedded chunks
│   └── summarize/      # Citation-grounded claim generation, validation and persistence
├── alembic/            # Database migration files
├── celery_app.py       # Celery configuration
└── requirements.txt    # Project dependencies
```

## 🔑 Key Implementation Highlights

- **Secure Password Storage**: Bcrypt hashing with automatic salt generation
- **Token-Based Auth**: Stateless JWT tokens with configurable expiration
- **Async Task Processing**: Non-blocking news fetching and AI summarization
- **Database Relationships**: Proper foreign key relationships between Users and Preferences
- **API Best Practices**: Dependency injection, proper HTTP status codes, and comprehensive error handling
- **Type Safety**: Full Pydantic validation for request/response data

## 📊 Database Schema

**Users**: id, username, hashed_password

**PodcastPreference**: id, topic, user_id (FK)

**Article**: id, url, title, topic, content, content_hash, created_at

**Chunk**: id, article_id (FK), position, text, embedding (pgvector)

**Summary**: id, topic, created_at

**Claim**: id, summary_id (FK), text, source_chunk_id (FK), position

## 🔄 Background Task Flow

1. Celery beat queues `ingest_topic` for each user preference topic, which fetches headlines, dedups, chunks and embeds them into `articles` and `chunks`
2. `summarize_topic` retrieves the best matching chunks for a topic, has the LLM write one claim per chunk it cites, and rejects any claim citing a chunk outside the retrieved set
3. Validated claims are persisted as a `Summary` with its `Claim`s, each still linked to the chunk that grounds it

## 🤝 Contributing

This is a portfolio project, but feedback and suggestions are welcome! Feel free to open an issue or reach out.

## 📄 License

This project is open source and available under the MIT License.

## 👤 Author

**Junke Yang**

- GitHub: [@chloeyjk](https://github.com/chloeyjk)

---

*Built as part of my software engineering portfolio to demonstrate full-stack backend development skills, including API design, authentication, database management, asynchronous processing, and AI integration.*
