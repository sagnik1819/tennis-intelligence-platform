"""
Module 4: Database Connection Engine
Provides connection pooling, session lifecycle management, and transparent fallback
between PostgreSQL (Production / Supabase / Neon) and SQLite (Offline Local Development).
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=False)

# Database URL from environment or default local SQLite database
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL or DATABASE_URL.strip() == "":
    db_path = os.path.join(BASE_DIR, "tennis_intelligence.db")
    DATABASE_URL = f"sqlite:///{db_path}"
elif DATABASE_URL.startswith("postgres://"):
    # SQLAlchemy 2.0 requires postgresql:// instead of postgres://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite requires 'check_same_thread: False'
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_schema_migrations():
    """
    Safely adds newly introduced auth/OTP columns to pre-existing databases
    without dropping existing data.
    """
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        return

    existing_cols = {col["name"] for col in inspector.get_columns("users")}
    migrations = [
        ("phone_number", "VARCHAR(30)"),
        ("auth_provider", "VARCHAR(20) NOT NULL DEFAULT 'local'"),
        ("google_id", "VARCHAR(255)"),
        ("avatar_url", "VARCHAR(500)"),
        ("is_email_verified", "BOOLEAN NOT NULL DEFAULT TRUE" if not DATABASE_URL.startswith("sqlite") else "BOOLEAN NOT NULL DEFAULT 1"),
        ("is_phone_verified", "BOOLEAN NOT NULL DEFAULT FALSE" if not DATABASE_URL.startswith("sqlite") else "BOOLEAN NOT NULL DEFAULT 0"),
    ]

    with engine.begin() as conn:
        for col_name, col_def in migrations:
            if col_name not in existing_cols:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
        # Create unique index on google_id if missing
        existing_indexes = {idx["name"] for idx in inspector.get_indexes("users")}
        if "ix_users_google_id" not in existing_indexes:
            try:
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id)"))
            except Exception:
                pass


def get_db():
    """FastAPI Dependency injection for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
