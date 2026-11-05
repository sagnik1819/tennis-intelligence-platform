"""Quick test to verify all API endpoints are live."""
import urllib.request
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://localhost:8000"

def test(name, path):
    try:
        r = urllib.request.urlopen(f"{BASE}{path}")
        data = json.loads(r.read())
        print(f"[OK] {name}: {path}")
        return data
    except Exception as e:
        print(f"[FAIL] {name}: {path} -> {e}")
        return None

# Test endpoints
root = test("Root", "/")
health = test("Health", "/api/v1/health")
players = test("Players", "/api/v1/players")
rankings = test("Rankings", "/api/v1/rankings/top")
competitions = test("Competitions", "/api/v1/competitions")
venues = test("Venues", "/api/v1/venues")
kpis = test("KPIs", "/api/v1/analytics/kpis")
countries = test("Countries", "/api/v1/analytics/countries")

if players:
    items = players.get("items", []) if isinstance(players, dict) else players
    print(f"\n  Total players returned: {len(items)}")
    for p in items[:3]:
        print(f"  - {p['name']} ({p.get('country','?')}) Rank: {p.get('rank','N/A')}")

if health:
    print(f"\n  DB status: {health.get('database','?')}")

print("\n=== BACKEND IS LIVE! ===")
