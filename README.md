# EchoCast - Podcast Backend API

A backend service for personalized podcast content generation, featuring JWT authentication, asynchronous task processing, and AI-powered article summarization.

## 🚀 Features

- **User Authentication & Authorization**: JWT-based secure authentication with OAuth2 password flow
- **User Preference Management**: Store and retrieve personalized podcast topic preferences
- **Asynchronous News Aggregation**: Celery-powered background tasks for fetching news from multiple categories
- **AI-Powered Summarization**: OpenAI GPT-4 integration for intelligent article summarization
- **RESTful API**: Clean, well-documented endpoints built with FastAPI
- **Database Migration Support**: Alembic for version-controlled schema management

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: SQLAlchemy ORM with PostgreSQL/SQLite
- **Authentication**: JWT (python-jose), OAuth2, Passlib (bcrypt)
- **Task Queue**: Celery with Redis broker
- **AI Integration**: OpenAI GPT-4
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
- News fetching and article summarization run asynchronously via Celery
- Articles are automatically summarized using GPT-4 and stored in the database

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
│   └── tasks.py        # Celery background tasks
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

**ArticleSummary**: id, title, url, summary

## 🔄 Background Task Flow

1. Celery task fetches top headlines from NewsAPI based on topic
2. Articles are queued for summarization
3. OpenAI GPT-4 generates concise summaries
4. Summaries are persisted to database for future retrieval

## 🤝 Contributing

This is a portfolio project, but feedback and suggestions are welcome! Feel free to open an issue or reach out.

## 📄 License

This project is open source and available under the MIT License.

## 👤 Author

**Junke Yang**

- GitHub: [@chloeyjk](https://github.com/chloeyjk)

---

*Built as part of my software engineering portfolio to demonstrate full-stack backend development skills, including API design, authentication, database management, asynchronous processing, and AI integration.*
