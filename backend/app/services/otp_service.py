"""
OTP Security Service
Generates cryptographically secure 6-digit codes, hashes them with SHA-256,
enforces expiration (10 mins), resend cooldown (30s), and max verification attempts.
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import SECRET_KEY
from app.models.entities import OTPVerification

OTP_EXPIRY_MINUTES = 10
OTP_RESEND_COOLDOWN_SECONDS = 30
MAX_OTP_ATTEMPTS = 5


def _ensure_utc(dt: datetime) -> datetime:
    """Normalizes naive SQLite datetimes and tz-aware PostgreSQL datetimes to UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _hash_otp(target: str, channel: str, code: str) -> str:
    payload = f"{target.strip().lower()}:{channel}:{code}:{SECRET_KEY}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class OTPService:
    @staticmethod
    def generate_and_store_otp(
        db: Session,
        target: str,
        channel: str,
        purpose: str = "register",
        enforce_cooldown: bool = True,
    ) -> str:
        """Creates a new 6-digit OTP, invalidates prior unused OTPs, and returns plain code."""
        normalized_target = target.strip().lower() if channel == "email" else target.strip()
        now = datetime.now(timezone.utc)

        if enforce_cooldown:
            latest = (
                db.query(OTPVerification)
                .filter(
                    OTPVerification.target == normalized_target,
                    OTPVerification.channel == channel,
                    OTPVerification.is_used == False,  # noqa: E712
                )
                .order_by(OTPVerification.created_at.desc())
                .first()
            )
            if latest and latest.created_at:
                elapsed = (now - _ensure_utc(latest.created_at)).total_seconds()
                if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
                    wait_sec = int(OTP_RESEND_COOLDOWN_SECONDS - elapsed) + 1
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Please wait {wait_sec} seconds before requesting a new OTP.",
                    )

        # Invalidate any prior unused OTPs for this target+channel
        db.query(OTPVerification).filter(
            OTPVerification.target == normalized_target,
            OTPVerification.channel == channel,
            OTPVerification.is_used == False,  # noqa: E712
        ).update({"is_used": True})

        plain_code = "".join(str(secrets.randbelow(10)) for _ in range(6))
        record = OTPVerification(
            target=normalized_target,
            channel=channel,
            purpose=purpose,
            otp_hash=_hash_otp(normalized_target, channel, plain_code),
            attempts=0,
            is_used=False,
            expires_at=now + timedelta(minutes=OTP_EXPIRY_MINUTES),
            created_at=now,
        )
        db.add(record)
        db.commit()
        return plain_code

    @staticmethod
    def verify_otp(db: Session, target: str, channel: str, code: str) -> bool:
        """Verifies a 6-digit OTP against the latest active hashed record."""
        normalized_target = target.strip().lower() if channel == "email" else target.strip()
        now = datetime.now(timezone.utc)

        record = (
            db.query(OTPVerification)
            .filter(
                OTPVerification.target == normalized_target,
                OTPVerification.channel == channel,
                OTPVerification.is_used == False,  # noqa: E712
            )
            .order_by(OTPVerification.created_at.desc())
            .first()
        )

        if not record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active OTP found. Please request a new verification code.",
            )

        if _ensure_utc(record.expires_at) < now:
            record.is_used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired (10 minute limit). Please request a new code.",
            )

        if record.attempts >= MAX_OTP_ATTEMPTS:
            record.is_used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many incorrect OTP attempts. Please request a new verification code.",
            )

        expected_hash = _hash_otp(normalized_target, channel, code.strip())
        if not hmac.compare_digest(record.otp_hash, expected_hash):
            record.attempts += 1
            db.commit()
            remaining = MAX_OTP_ATTEMPTS - record.attempts
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid OTP code. {remaining} attempt(s) remaining.",
            )

        record.is_used = True
        db.commit()
        return True
