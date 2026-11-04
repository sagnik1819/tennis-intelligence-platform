"""
Module 4: Database Connection Engine
Provides connection pooling, session lifecycle management, and transparent fallback
between PostgreSQL (Production / Supabase / Neon) and SQLite (Offline Local Development).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Database URL from environment or default local SQLite database
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL or DATABASE_URL.strip() == "":
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    db_path = os.path.join(BASE_DIR, "tennis_intelligence.db")
    DATABASE_URL = f"sqlite:///{db_path}"

# SQLite requires 'check_same_thread: False'
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI Dependency injection for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
