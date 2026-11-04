"""
Module 2 Verification Script: Test SportRadar API Extraction & Sync Manager
Run this script to test and verify the extraction layer.
"""
import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sportradar_client import SportRadarClient
from sync_manager import SyncManager


def run_verification():
    print("=" * 85)
    print("      🎾 TENNIS INTELLIGENCE PLATFORM - MODULE 2 API EXTRACTION VERIFICATION 🎾")
    print("=" * 85)

    # Initialize client (will automatically use .env if available, or fallback mode)
    client = SportRadarClient()
    manager = SyncManager(client)

    print(f"\n[1] Executing full synchronization...")
    results = manager.execute_full_sync()

    print("\n[2] Extraction Results Summary:")
    print("-" * 85)
    print(f"Status               : {results['status']}")
    print(f"Data Mode            : {results['data_mode']}")
    print(f"Timestamp (UTC)      : {results['last_sync_timestamp']}")
    print(f"Duration             : {results['duration_seconds']} seconds")
    print("-" * 85)
    print(f"Categories Extracted : {results['categories_count']}")
    print(f"Competitions Count   : {results['competitions_count']}")
    print(f"Complexes Count      : {results['complexes_count']}")
    print(f"Venues Count         : {results['venues_count']}")
    print(f"Rankings Count       : {results['rankings_count']}")
    print(f"Competitors Count    : {results['competitors_count']}")
    print("=" * 85)

    # Retrieve and verify persistence
    last_info = manager.get_last_sync_info()
    assert last_info["status"] == "SUCCESS", "Sync status did not persist properly!"
    print("[SUCCESS] Module 2 verification passed! Sync status file persisted cleanly.\n")


if __name__ == "__main__":
    run_verification()
