"""
Real Notification & Identity Verification Service
1. Real Gmail SMTP (SSL smtp.gmail.com:465) for 6-digit Email OTP verification
2. Free SMS Gateways (Textbelt free tier, Textbee Android SIM gateway, or Twilio trial)
3. Official Google OAuth 2.0 ID Token Verification (oauth2.googleapis.com/tokeninfo)
"""
import html
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any
import httpx
from fastapi import HTTPException, status

from app.core.config import settings


class NotificationService:
    @staticmethod
    def send_email_otp(to_email: str, otp_code: str, full_name: str = "Analyst") -> Dict[str, Any]:
        """Sends a real 6-digit OTP email using Gmail SMTP."""
        if not settings.is_gmail_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Gmail SMTP is not configured on the server yet. "
                    "Add SMTP_EMAIL and your 16-character Gmail App Password to the .env file "
                    "(https://myaccount.google.com/apppasswords) and restart the backend."
                ),
            )

        safe_name = html.escape(full_name or "Analyst")
        subject = f"{otp_code} is your Tennis Intelligence Platform verification code"

        plain_body = (
            f"Hello {full_name or 'Analyst'},\n\n"
            f"Your Tennis Intelligence Platform verification code is: {otp_code}\n\n"
            f"This code expires in 10 minutes. Never share this code with anyone.\n\n"
            f"- Tennis Intelligence Platform"
        )

        html_body = f"""
        <div style="background:#0B1220;padding:32px;font-family:Arial,sans-serif;color:#E2E8F0;">
          <div style="max-width:480px;margin:0 auto;background:#111A2E;border:1px solid #24324D;border-radius:16px;padding:28px;">
            <div style="font-size:20px;font-weight:800;letter-spacing:0.5px;color:#FFFFFF;margin-bottom:16px;">
              TENNIS<span style="color:#B7F34A;">INTEL</span>
            </div>
            <p style="font-size:14px;color:#CBD5E1;line-height:1.5;">
              Hi <strong>{safe_name}</strong>,
            </p>
            <p style="font-size:14px;color:#CBD5E1;line-height:1.5;">
              Use the 6-digit verification code below to verify your Gmail address and activate your analyst workspace:
            </p>
            <div style="margin:24px 0;padding:18px;text-align:center;background:#0B1220;border:1px solid #B7F34A;border-radius:12px;">
              <span style="font-family:monospace;font-size:32px;font-weight:900;letter-spacing:8px;color:#B7F34A;">
                {otp_code}
              </span>
            </div>
            <p style="font-size:12px;color:#94A3B8;line-height:1.5;">
              This code is valid for <strong>10 minutes</strong>. If you did not request this verification, you can safely ignore this email.
            </p>
          </div>
        </div>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Tennis Intelligence Platform <{settings.SMTP_EMAIL}>"
        msg["To"] = to_email
        msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            if settings.SMTP_PORT == 587:
                context = ssl.create_default_context()
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                    server.starttls(context=context)
                    server.login(settings.SMTP_EMAIL, settings.SMTP_APP_PASSWORD)
                    server.sendmail(settings.SMTP_EMAIL, to_email, msg.as_string())
            else:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context, timeout=15) as server:
                    server.login(settings.SMTP_EMAIL, settings.SMTP_APP_PASSWORD)
                    server.sendmail(settings.SMTP_EMAIL, to_email, msg.as_string())
            return {"delivered": True, "provider": "gmail_smtp"}
        except smtplib.SMTPAuthenticationError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "Gmail rejected SMTP login. Ensure 2-Step Verification is enabled and you are using "
                    "a 16-character Gmail App Password (not your regular Gmail password)."
                ),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to deliver email OTP via Gmail SMTP: {str(e)}",
            )

    @staticmethod
    def send_sms_otp(phone_number: str, otp_code: str) -> Dict[str, Any]:
        """
        Dispatches SMS OTP via configured free-tier SMS gateway:
        - textbelt: 1 free SMS/day per IP with key='textbelt'
        - textbee: 300 free SMS/month via your own Android phone SIM
        - twilio: Twilio trial credits
        """
        provider = settings.SMS_PROVIDER
        sms_text = f"Your Tennis Intelligence Platform verification code is {otp_code}. Valid for 10 minutes."

        if provider == "textbelt":
            if not settings.TEXTBELT_API_KEY:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="TEXTBELT_API_KEY is not configured.",
                )
            try:
                resp = httpx.post(
                    "https://textbelt.com/text",
                    data={
                        "phone": phone_number,
                        "message": sms_text,
                        "key": settings.TEXTBELT_API_KEY,
                    },
                    timeout=15.0,
                )
                data = resp.json()
                if not data.get("success"):
                    err_msg = data.get("error", "SMS delivery failed.")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=(
                            f"Textbelt SMS error: {err_msg} "
                            "(Note: Textbelt free tier allows 1 SMS/day and restricts some international routes; "
                            "configure Textbee Android Gateway or Twilio in .env for higher volume.)"
                        ),
                    )
                return {
                    "delivered": True,
                    "provider": "textbelt",
                    "quota_remaining": data.get("quotaRemaining"),
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Textbelt SMS request failed: {str(e)}",
                )

        elif provider == "textbee":
            if not (settings.TEXTBEE_API_KEY and settings.TEXTBEE_DEVICE_ID):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Textbee credentials (TEXTBEE_API_KEY, TEXTBEE_DEVICE_ID) are missing in .env.",
                )
            try:
                url = f"https://api.textbee.dev/api/v1/gateway/devices/{settings.TEXTBEE_DEVICE_ID}/send-sms"
                resp = httpx.post(
                    url,
                    headers={"x-api-key": settings.TEXTBEE_API_KEY},
                    json={"recipients": [phone_number], "message": sms_text},
                    timeout=15.0,
                )
                if resp.status_code >= 400:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Textbee API error ({resp.status_code}): {resp.text}",
                    )
                return {"delivered": True, "provider": "textbee"}
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Textbee SMS request failed: {str(e)}",
                )

        elif provider == "twilio":
            if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_PHONE_NUMBER):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Twilio credentials are missing in .env.",
                )
            try:
                url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
                resp = httpx.post(
                    url,
                    auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                    data={
                        "From": settings.TWILIO_PHONE_NUMBER,
                        "To": phone_number,
                        "Body": sms_text,
                    },
                    timeout=15.0,
                )
                if resp.status_code >= 400:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Twilio API error ({resp.status_code}): {resp.text}",
                    )
                return {"delivered": True, "provider": "twilio"}
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Twilio SMS request failed: {str(e)}",
                )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unsupported SMS_PROVIDER '{provider}'. Choose textbelt, textbee, or twilio.",
        )

    @staticmethod
    def verify_google_id_token(id_token: str) -> Dict[str, Any]:
        """
        Verifies a Google Identity Services ID token directly against Google's tokeninfo endpoint
        and checks audience (GOOGLE_CLIENT_ID) + email_verified.
        """
        if not settings.is_google_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Google OAuth is not configured on the server yet. "
                    "Add GOOGLE_CLIENT_ID from Google Cloud Console to .env and VITE_GOOGLE_CLIENT_ID to frontend/.env."
                ),
            )

        try:
            resp = httpx.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token},
                timeout=10.0,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Could not contact Google token verification server: {str(e)}",
            )

        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired Google credential token.",
            )

        payload = resp.json()
        aud = payload.get("aud")
        if aud != settings.GOOGLE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google token audience mismatch (Client ID does not match this app).",
            )

        email_verified = str(payload.get("email_verified", "")).lower() == "true"
        if not email_verified or not payload.get("email"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google account email is not verified.",
            )

        return {
            "google_id": payload.get("sub"),
            "email": payload.get("email").strip().lower(),
            "full_name": payload.get("name") or payload.get("email").split("@")[0],
            "avatar_url": payload.get("picture"),
        }
