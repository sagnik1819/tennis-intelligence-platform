"""
Authentication & Verification Endpoints:
- Email/Password Registration + Real Gmail 6-digit OTP Verification
- Resend Email OTP (with 30s cooldown)
- Google OAuth 2.0 Sign-In / Sign-Up (ID token verified via Google)
- Free Phone SMS OTP Verification (Textbelt / Textbee / Twilio)
- Login & Authenticated Profile (/me)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from app.core.config import settings
from app.database.connection import get_db
from app.models.entities import User
from app.schemas.api_schemas import (
    UserRegister,
    RegisterPendingResponse,
    VerifyEmailOTPRequest,
    ResendEmailOTPRequest,
    GoogleAuthRequest,
    SendPhoneOTPRequest,
    VerifyPhoneOTPRequest,
    AuthProvidersStatusResponse,
    UserLogin,
    TokenResponse,
    UserResponse,
)
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.services.otp_service import OTPService
from app.services.notification_service import NotificationService

router = APIRouter()


def _serialize_user(user: User) -> dict:
    return {
        "user_id": user.user_id,
        "email": user.email,
        "full_name": user.full_name,
        "phone_number": user.phone_number,
        "auth_provider": user.auth_provider,
        "avatar_url": user.avatar_url,
        "is_email_verified": user.is_email_verified,
        "is_phone_verified": user.is_phone_verified,
        "role": user.role,
    }


@router.get("/providers", response_model=AuthProvidersStatusResponse)
async def get_auth_providers_status():
    """Returns live readiness flags for Gmail OTP, Google OAuth, and Free SMS OTP."""
    return {
        "gmail_otp_enabled": settings.is_gmail_configured,
        "google_enabled": settings.is_google_configured,
        "google_client_id": settings.GOOGLE_CLIENT_ID if settings.is_google_configured else None,
        "sms_otp_enabled": settings.is_sms_configured,
        "sms_provider": settings.SMS_PROVIDER,
    }


@router.post("/register", response_model=RegisterPendingResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Registers a user as unverified and dispatches a real 6-digit OTP to their Gmail/email.
    JWT token is only issued after OTP verification succeeds.
    """
    normalized_email = user_data.email.strip().lower()
    existing = db.query(User).filter(User.email == normalized_email).first()

    if existing and existing.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in.",
        )

    if existing and not existing.is_email_verified:
        # Update details for re-attempted unverified registration
        existing.hashed_password = hash_password(user_data.password)
        existing.full_name = user_data.full_name or existing.full_name
        if user_data.phone_number:
            existing.phone_number = user_data.phone_number.strip()
        target_user = existing
    else:
        target_user = User(
            email=normalized_email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            phone_number=user_data.phone_number.strip() if user_data.phone_number else None,
            auth_provider="local",
            is_email_verified=False,
            is_phone_verified=False,
            role="user",
        )
        db.add(target_user)

    db.commit()
    db.refresh(target_user)

    otp_code = OTPService.generate_and_store_otp(
        db,
        target=normalized_email,
        channel="email",
        purpose="register",
        enforce_cooldown=bool(existing),
    )

    dev_otp = None
    if settings.is_gmail_configured:
        try:
            NotificationService.send_email_otp(
                to_email=normalized_email,
                otp_code=otp_code,
                full_name=target_user.full_name or "Analyst",
            )
            msg = f"A 6-digit verification code has been sent to {normalized_email}. Please check your inbox (and Spam folder)."
        except Exception as e:
            print(f"[OTP WARNING] Gmail delivery error: {e}. Fallback code: {otp_code}")
            dev_otp = otp_code
            msg = f"Verification code: {otp_code} (Gmail delivery issue: {e})"
    else:
        print(f"[OTP DEV MODE] 🔑 6-Digit OTP for {normalized_email}: {otp_code}")
        dev_otp = otp_code
        msg = f"6-digit verification code: {otp_code} (Gmail SMTP not configured in .env, code shown for quick testing)."

    return {
        "requires_verification": True,
        "email": normalized_email,
        "message": msg,
        "dev_otp": dev_otp,
    }


@router.post("/verify-email-otp", response_model=TokenResponse)
def verify_email_otp(payload: VerifyEmailOTPRequest, db: Session = Depends(get_db)):
    """Verifies the 6-digit Gmail OTP, activates the account, and returns a JWT."""
    normalized_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending registration found for this email.",
        )

    OTPService.verify_otp(db, target=normalized_email, channel="email", code=payload.otp)

    user.is_email_verified = True
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _serialize_user(user),
    }


@router.post("/resend-email-otp", response_model=RegisterPendingResponse)
def resend_email_otp(payload: ResendEmailOTPRequest, db: Session = Depends(get_db)):
    """Resends a fresh 6-digit OTP to an unverified user's Gmail with cooldown protection."""
    normalized_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found for this email address.",
        )
    if user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email address is already verified. Please sign in.",
        )

    otp_code = OTPService.generate_and_store_otp(
        db,
        target=normalized_email,
        channel="email",
        purpose="register",
        enforce_cooldown=True,
    )

    dev_otp = None
    if settings.is_gmail_configured:
        try:
            NotificationService.send_email_otp(
                to_email=normalized_email,
                otp_code=otp_code,
                full_name=user.full_name or "Analyst",
            )
            msg = f"A new 6-digit verification code was sent to {normalized_email}."
        except Exception as e:
            print(f"[OTP WARNING] Gmail delivery error: {e}. Fallback code: {otp_code}")
            dev_otp = otp_code
            msg = f"New verification code: {otp_code}"
    else:
        print(f"[OTP DEV MODE] 🔑 New 6-Digit OTP for {normalized_email}: {otp_code}")
        dev_otp = otp_code
        msg = f"New verification code: {otp_code} (Demo/Dev mode active)."

    return {
        "requires_verification": True,
        "email": normalized_email,
        "message": msg,
        "dev_otp": dev_otp,
    }


@router.post("/login", response_model=TokenResponse)
def login(creds: UserLogin, db: Session = Depends(get_db)):
    """Validates user credentials, ensures email verification, and issues a JWT."""
    normalized_email = creds.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    if user.auth_provider == "google" and (not user.hashed_password or user.hashed_password == "!GOOGLE_OAUTH_ONLY!"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account was registered with Google. Please click 'Continue with Google'.",
        )

    if not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="EMAIL_NOT_VERIFIED",
        )

    token = create_access_token({"sub": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _serialize_user(user),
    }


@router.post("/google", response_model=TokenResponse)
def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Sign in or Register with Google.
    Verifies the Google ID token via Google OAuth2 tokeninfo and auto-verifies email.
    """
    google_profile = NotificationService.verify_google_id_token(payload.credential)
    email = google_profile["email"]
    google_id = google_profile["google_id"]

    user = db.query(User).filter((User.google_id == google_id) | (User.email == email)).first()

    if not user:
        user = User(
            email=email,
            hashed_password="!GOOGLE_OAUTH_ONLY!",
            full_name=google_profile.get("full_name"),
            auth_provider="google",
            google_id=google_id,
            avatar_url=google_profile.get("avatar_url"),
            is_email_verified=True,
            is_phone_verified=False,
            role="user",
        )
        db.add(user)
    else:
        user.google_id = google_id
        user.is_email_verified = True
        if not user.avatar_url and google_profile.get("avatar_url"):
            user.avatar_url = google_profile["avatar_url"]
        if not user.full_name and google_profile.get("full_name"):
            user.full_name = google_profile["full_name"]

    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _serialize_user(user),
    }


@router.post("/send-phone-otp")
def send_phone_otp(
    payload: SendPhoneOTPRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sends a 6-digit SMS OTP to the authenticated user's phone number via free SMS gateway."""
    phone = payload.phone_number.strip()
    otp_code = OTPService.generate_and_store_otp(
        db,
        target=phone,
        channel="phone",
        purpose="verify_phone",
        enforce_cooldown=True,
    )
    delivery = NotificationService.send_sms_otp(phone, otp_code)
    return {
        "sent": True,
        "phone_number": phone,
        "provider": delivery.get("provider"),
        "quota_remaining": delivery.get("quota_remaining"),
        "message": f"6-digit SMS OTP sent to {phone} via {delivery.get('provider')}.",
    }


@router.post("/verify-phone-otp", response_model=UserResponse)
def verify_phone_otp(
    payload: VerifyPhoneOTPRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verifies the 6-digit SMS OTP and marks the authenticated user's phone number as verified."""
    phone = payload.phone_number.strip()
    OTPService.verify_otp(db, target=phone, channel="phone", code=payload.otp)

    current_user.phone_number = phone
    current_user.is_phone_verified = True
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """Returns profile and verification badges for currently authenticated user."""
    return current_user
