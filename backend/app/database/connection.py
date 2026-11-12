"""
Module 4: Database Connection Engine
Provides high-concurrency connection pooling, SQLite WAL mode, session lifecycle management,
and transparent fallback between PostgreSQL (Production / Neon PgBouncer) and SQLite (Local Dev).
"""
from contextlib import contextmanager
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, event, inspect, text
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

IS_SQLITE = DATABASE_URL.startswith("sqlite")

if IS_SQLITE:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 15},
        echo=False,
    )

    @event.listens_for(engine, "connect")
    def _configure_sqlite_wal(dbapi_connection, connection_record):
        """Enable SQLite WAL mode so concurrent reads never block writes locally."""
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA busy_timeout=15000;")
        finally:
            cursor.close()
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "40")),
        pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "15")),
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "300")),
        pool_pre_ping=True,
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_schema_migrations():
    """
    Safely adds newly introduced auth/OTP columns and high-concurrency indexes
    to pre-existing databases without dropping existing data.
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
        ("is_email_verified", "BOOLEAN NOT NULL DEFAULT TRUE" if not IS_SQLITE else "BOOLEAN NOT NULL DEFAULT 1"),
        ("is_phone_verified", "BOOLEAN NOT NULL DEFAULT FALSE" if not IS_SQLITE else "BOOLEAN NOT NULL DEFAULT 0"),
    ]

    with engine.begin() as conn:
        for col_name, col_def in migrations:
            if col_name not in existing_cols:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))

        existing_indexes = {idx["name"] for idx in inspector.get_indexes("users")}
        if "ix_users_google_id" not in existing_indexes:
            try:
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id)"))
            except Exception:
                pass

        # High-concurrency lookup indexes
        if inspector.has_table("ai_interactions"):
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ai_interactions_user_id ON ai_interactions (user_id)"))
            except Exception:
                pass
        if inspector.has_table("otp_verifications"):
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_otp_lookup ON otp_verifications (target, channel, is_used)"))
            except Exception:
                pass


@contextmanager
def get_db_context():
    """Context-managed session used on cache misses and background tasks."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db():
    """FastAPI Dependency injection for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
