"""
Module 5: Core Application Configuration
Loads environment variables from .env, manages CORS domains, SMTP/Gmail OTP,
Google OAuth 2.0, and Free SMS OTP providers.
"""
import os
from typing import List
from dotenv import load_dotenv

# Automatically load .env from project root if present
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(ENV_PATH, override=False)


class Settings:
    PROJECT_NAME: str = "Tennis Intelligence Platform API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # CORS Origins - Allow React frontend (Vite default: 5173, CRA: 3000, production)
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # High-Concurrency Caching (L1 In-Memory + Optional L2 Redis)
    REDIS_URL: str = os.getenv("REDIS_URL", "").strip()
    CACHE_MAX_ENTRIES: int = int(os.getenv("CACHE_MAX_ENTRIES", "2048"))
    CACHE_TTL_PLAYERS: int = int(os.getenv("CACHE_TTL_PLAYERS", "120"))
    CACHE_TTL_ANALYTICS: int = int(os.getenv("CACHE_TTL_ANALYTICS", "120"))
    CACHE_TTL_CATALOG: int = int(os.getenv("CACHE_TTL_CATALOG", "300"))
    CDN_MAX_AGE: int = int(os.getenv("CDN_MAX_AGE", "60"))
    CDN_S_MAXAGE: int = int(os.getenv("CDN_S_MAXAGE", "120"))

    # Tiered Rate Limiting (Protects Origin Under Spikes / Brute Force)
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").strip().lower() in ("1", "true", "yes")
    TRUST_PROXY_HEADERS: bool = os.getenv("TRUST_PROXY_HEADERS", "true").strip().lower() in ("1", "true", "yes")
    RATE_LIMIT_READ_PER_MIN: int = int(os.getenv("RATE_LIMIT_READ_PER_MIN", "12000"))
    RATE_LIMIT_AUTH_PER_MIN: int = int(os.getenv("RATE_LIMIT_AUTH_PER_MIN", "30"))
    RATE_LIMIT_CHAT_PER_MIN: int = int(os.getenv("RATE_LIMIT_CHAT_PER_MIN", "60"))

    # Database Pool Tuning (PostgreSQL / Neon PgBouncer)
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "40"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "15"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "300"))

    # Gmail SMTP (Real Email OTP Verification)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SMTP_EMAIL: str = os.getenv("SMTP_EMAIL", "").strip()
    SMTP_APP_PASSWORD: str = os.getenv("SMTP_APP_PASSWORD", "").strip()

    # Google OAuth 2.0
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "").strip()

    # Free Phone SMS OTP Providers
    SMS_PROVIDER: str = os.getenv("SMS_PROVIDER", "textbelt").strip().lower()
    TEXTBELT_API_KEY: str = os.getenv("TEXTBELT_API_KEY", "textbelt").strip()
    TEXTBEE_API_KEY: str = os.getenv("TEXTBEE_API_KEY", "").strip()
    TEXTBEE_DEVICE_ID: str = os.getenv("TEXTBEE_DEVICE_ID", "").strip()
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "").strip()

    @property
    def is_gmail_configured(self) -> bool:
        return bool(
            self.SMTP_EMAIL
            and self.SMTP_APP_PASSWORD
            and "your_" not in self.SMTP_EMAIL
            and "your_" not in self.SMTP_APP_PASSWORD
        )

    @property
    def is_google_configured(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID and "your_" not in self.GOOGLE_CLIENT_ID)

    @property
    def is_sms_configured(self) -> bool:
        if self.SMS_PROVIDER == "textbelt":
            return bool(self.TEXTBELT_API_KEY)
        if self.SMS_PROVIDER == "textbee":
            return bool(self.TEXTBEE_API_KEY and self.TEXTBEE_DEVICE_ID)
        if self.SMS_PROVIDER == "twilio":
            return bool(self.TWILIO_ACCOUNT_SID and self.TWILIO_AUTH_TOKEN and self.TWILIO_PHONE_NUMBER)
        return False


settings = Settings()
