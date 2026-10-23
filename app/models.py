from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    preferences = relationship("PodcastPreference", back_populates="owner")

class PodcastPreference(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="preferences")


EMBEDDING_DIMENSIONS = 1536


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    topic = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    chunks = relationship("Chunk", back_populates="article", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), index=True, nullable=False)
    position = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    # JSON stands in for pgvector on SQLite so tests run without Postgres.
    embedding = Column(Vector(EMBEDDING_DIMENSIONS).with_variant(JSON, "sqlite"), nullable=False)

    article = relationship("Article", back_populates="chunks")


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    claims = relationship("Claim", back_populates="summary", cascade="all, delete-orphan")


class Claim(Base):
    """A single citation-grounded claim, carrying the chunk id it was generated from."""

    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    summary_id = Column(Integer, ForeignKey("summaries.id", ondelete="CASCADE"), index=True, nullable=False)
    text = Column(Text, nullable=False)
    source_chunk_id = Column(Integer, ForeignKey("chunks.id", ondelete="CASCADE"), index=True, nullable=False)
    position = Column(Integer, nullable=False)

    summary = relationship("Summary", back_populates="claims")
    source_chunk = relationship("Chunk")
