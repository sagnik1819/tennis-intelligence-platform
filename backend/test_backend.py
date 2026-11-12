"""
Backend Verification Suite
Uses Starlette/FastAPI TestClient (with lifespan context) to verify all REST endpoints,
analytics, AI assistant, JWT auth, Gmail OTP verification, Google OAuth, and Phone SMS OTP.
"""
import os
import sys
from unittest.mock import patch

# Ensure UTF-8 output on Windows consoles safely
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURR_DIR, ".."))
sys.path.append(CURR_DIR)
sys.path.append(PROJECT_ROOT)

from starlette.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.database.connection import SessionLocal
from app.models.entities import User, OTPVerification


def run_tests():
    print("=" * 85)
    print("      [TIP] TENNIS INTELLIGENCE PLATFORM - BACKEND REST API TEST SUITE")
    print("=" * 85)

    with TestClient(app) as client:
        endpoints = [
            ("GET", "/api/v1/health", 200),
            ("GET", "/api/v1/players", 200),
            ("GET", "/api/v1/rankings/top", 200),
            ("GET", "/api/v1/competitions", 200),
            ("GET", "/api/v1/venues", 200),
            ("GET", "/api/v1/analytics/kpis", 200),
            ("GET", "/api/v1/analytics/countries", 200),
            ("GET", "/api/v1/admin/data-quality", 200),
            ("GET", "/api/v1/auth/providers", 200),
        ]

        for method, path, expected_status in endpoints:
            resp = client.get(path)
            assert resp.status_code == expected_status, f"Failed {path}: {resp.status_code} - {resp.text}"
            print(f"[PASS] {method:<4} {path:<32} -> {resp.status_code} OK")

        # Test Player Profile with Radar Traits
        print("\n[TESTING PLAYER DETAIL & RADAR TRAITS]")
        players_resp = client.get("/api/v1/players")
        players = players_resp.json()["items"]
        assert len(players) > 0
        p1 = players[0]
        p1_id = p1["competitor_id"]

        detail_resp = client.get(f"/api/v1/players/{p1_id}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert "traits" in detail
        assert "consistency" in detail["traits"]
        assert "similar_players" in detail
        print(f"[PASS] Profile for '{detail['name']}' verified:")
        print(f"       Traits: Consistency: {detail['traits']['consistency']}, Power: {detail['traits']['power_volume']}")
        print(f"       Cluster Tier: {detail['cluster_tier']}")
        print(f"       Similar Players Found: {len(detail['similar_players'])}")

        # Test Smart Comparison
        if len(players) >= 2:
            print("\n[TESTING SMART PLAYER COMPARISON]")
            p2_id = players[1]["competitor_id"]
            cmp_resp = client.get(f"/api/v1/analytics/compare?player_a={p1_id}&player_b={p2_id}")
            assert cmp_resp.status_code == 200
            cmp_data = cmp_resp.json()
            assert "metrics_table" in cmp_data
            assert "ai_comparison_analysis" in cmp_data
            print(f"[PASS] Compared '{cmp_data['player_a']['name']}' vs '{cmp_data['player_b']['name']}':")
            print(f"       AI Analysis: {cmp_data['ai_comparison_analysis'][:100]}...")

        # Test AI Assistant Chatbot
        print("\n[TESTING AI TENNIS ASSISTANT CHAT]")
        chat_resp = client.post("/api/v1/assistant/chat", json={"prompt": "Who are the top players?"})
        assert chat_resp.status_code == 200
        chat_data = chat_resp.json()
        assert "response" in chat_data
        assert len(chat_data["citations"]) > 0
        print(f"[PASS] Assistant response: {chat_data['response'][:120]}...")
        print(f"       Citations: {len(chat_data['citations'])} real entities cited.")

        # Test Authentication (Demo User)
        print("\n[TESTING AUTHENTICATION & JWT]")
        login_resp = client.post("/api/v1/auth/login", json={"email": "analyst@tennisintel.com", "password": "Analyst@123"})
        assert login_resp.status_code == 200, login_resp.text
        login_data = login_resp.json()
        token = login_data["access_token"]
        assert token is not None
        print(f"[PASS] Login successful. JWT token received: {token[:20]}...")

        # Test Authenticated /me
        me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["is_email_verified"] is True
        print(f"[PASS] Current user authenticated: {me_resp.json()['email']} (Verified: {me_resp.json()['is_email_verified']})")

        # Test Gmail OTP Registration & Verification Workflow
        print("\n[TESTING GMAIL OTP REGISTRATION, VERIFICATION & PHONE SMS OTP]")
        test_email = "test.student@gmail.com"
        test_google_email = "google.student@gmail.com"
        test_phone = "+919876543210"

        # Clean prior test artifacts if present
        db = SessionLocal()
        try:
            db.query(OTPVerification).filter(OTPVerification.target.in_([test_email, test_phone])).delete(synchronize_session=False)
            db.query(User).filter(User.email.in_([test_email, test_google_email])).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

        captured = {}

        def fake_send_email_otp(to_email, otp_code, full_name="Analyst"):
            captured["email_otp"] = otp_code
            return {"delivered": True, "provider": "gmail_smtp"}

        def fake_send_sms_otp(phone_number, otp_code):
            captured["sms_otp"] = otp_code
            return {"delivered": True, "provider": "textbelt", "quota_remaining": 1}

        def fake_google_verify(id_token):
            assert id_token == "mock_valid_google_id_token"
            return {
                "google_id": "google-uid-9999",
                "email": test_google_email,
                "full_name": "Google Student",
                "avatar_url": "https://example.com/avatar.png",
            }

        with patch.object(settings, "SMTP_EMAIL", "sender@gmail.com"), \
             patch.object(settings, "SMTP_APP_PASSWORD", "abcd1234abcd1234"), \
             patch("app.api.v1.endpoints.auth.NotificationService.send_email_otp", side_effect=fake_send_email_otp), \
             patch("app.api.v1.endpoints.auth.NotificationService.send_sms_otp", side_effect=fake_send_sms_otp), \
             patch("app.api.v1.endpoints.auth.NotificationService.verify_google_id_token", side_effect=fake_google_verify):

            # 1. Register unverified user -> sends 6-digit OTP
            reg_resp = client.post("/api/v1/auth/register", json={
                "email": test_email,
                "password": "Password@123",
                "full_name": "Test Student",
                "phone_number": test_phone,
            })
            assert reg_resp.status_code == 200, reg_resp.text
            assert reg_resp.json()["requires_verification"] is True
            assert len(captured["email_otp"]) == 6
            print(f"[PASS] Registration created unverified account & dispatched 6-digit Gmail OTP: {captured['email_otp']}")

            # 2. Unverified login must be blocked with 403 EMAIL_NOT_VERIFIED
            blocked_login = client.post("/api/v1/auth/login", json={"email": test_email, "password": "Password@123"})
            assert blocked_login.status_code == 403
            assert blocked_login.json()["detail"] == "EMAIL_NOT_VERIFIED"
            print("[PASS] Unverified user blocked at login with 403 EMAIL_NOT_VERIFIED")

            # 3. Wrong OTP rejected
            bad_otp = client.post("/api/v1/auth/verify-email-otp", json={"email": test_email, "otp": "000000"})
            if captured["email_otp"] != "000000":
                assert bad_otp.status_code == 400
                print("[PASS] Incorrect OTP rejected & attempt recorded")

            # 4. Correct OTP verifies user and returns JWT
            ok_otp = client.post("/api/v1/auth/verify-email-otp", json={"email": test_email, "otp": captured["email_otp"]})
            assert ok_otp.status_code == 200, ok_otp.text
            student_token = ok_otp.json()["access_token"]
            assert ok_otp.json()["user"]["is_email_verified"] is True
            print("[PASS] Correct Gmail OTP verified user & issued JWT")

            # 5. Send & verify Phone SMS OTP
            sms_send_resp = client.post(
                "/api/v1/auth/send-phone-otp",
                json={"phone_number": test_phone},
                headers={"Authorization": f"Bearer {student_token}"},
            )
            assert sms_send_resp.status_code == 200, sms_send_resp.text
            assert len(captured["sms_otp"]) == 6

            sms_verify_resp = client.post(
                "/api/v1/auth/verify-phone-otp",
                json={"phone_number": test_phone, "otp": captured["sms_otp"]},
                headers={"Authorization": f"Bearer {student_token}"},
            )
            assert sms_verify_resp.status_code == 200, sms_verify_resp.text
            assert sms_verify_resp.json()["is_phone_verified"] is True
            print(f"[PASS] Phone SMS OTP verified ({test_phone} -> is_phone_verified=True)")

            # 6. Google Sign-In / Register with Google
            g_resp = client.post("/api/v1/auth/google", json={"credential": "mock_valid_google_id_token"})
            assert g_resp.status_code == 200, g_resp.text
            assert g_resp.json()["user"]["auth_provider"] == "google"
            assert g_resp.json()["user"]["is_email_verified"] is True
            print(f"[PASS] Google OAuth sign-in created verified user: {g_resp.json()['user']['email']}")

        # Cleanup synthetic test users after verification
        db = SessionLocal()
        try:
            db.query(OTPVerification).filter(OTPVerification.target.in_([test_email, test_phone])).delete(synchronize_session=False)
            db.query(User).filter(User.email.in_([test_email, test_google_email])).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

    print("\n" + "=" * 85)
    print("      ALL BACKEND ENDPOINTS, GMAIL OTP, GOOGLE OAUTH & SMS VERIFIED 100%!")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    run_tests()
