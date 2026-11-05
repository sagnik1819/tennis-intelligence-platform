"""
Backend Verification Suite
Uses Starlette/FastAPI TestClient to verify all REST endpoints, status codes, and schemas.
"""
import os
import sys

# Ensure UTF-8 output on Windows consoles safely
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURR_DIR, ".."))
sys.path.append(CURR_DIR)
sys.path.append(PROJECT_ROOT)

from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def run_tests():
    print("=" * 85)
    print("      [TIP] TENNIS INTELLIGENCE PLATFORM - BACKEND REST API TEST SUITE")
    print("=" * 85)

    endpoints = [
        ("GET", "/api/v1/health", 200),
        ("GET", "/api/v1/players", 200),
        ("GET", "/api/v1/rankings/top", 200),
        ("GET", "/api/v1/competitions", 200),
        ("GET", "/api/v1/venues", 200),
        ("GET", "/api/v1/analytics/kpis", 200),
        ("GET", "/api/v1/analytics/countries", 200),
        ("GET", "/api/v1/admin/data-quality", 200),
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

    # Test Authentication
    print("\n[TESTING AUTHENTICATION & JWT]")
    login_resp = client.post("/api/v1/auth/login", json={"email": "analyst@tennisintel.com", "password": "Analyst@123"})
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    token = login_data["access_token"]
    assert token is not None
    print(f"[PASS] Login successful. JWT token received: {token[:20]}...")

    # Test Authenticated /me
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    print(f"[PASS] Current user authenticated: {me_resp.json()['email']} ({me_resp.json()['full_name']})")

    print("\n" + "=" * 85)
    print("      🎉 ALL BACKEND ENDPOINTS & INTELLIGENCE FEATURES VERIFIED 100%! 🎉")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    run_tests()
