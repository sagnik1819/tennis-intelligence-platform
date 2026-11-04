"""
Module 2: Data Synchronization Manager
Coordinates multi-endpoint data extraction from SportRadar, calculates metrics,
tracks last sync timestamp, and outputs data freshness metadata.
"""
import os
import sys
import time
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sportradar_client import SportRadarClient

logger = logging.getLogger("SyncManager")


class SyncManager:
    """
    Manages end-to-end extraction from SportRadar endpoints,
    validates response payloads, and stores sync history & freshness metadata.
    """
    def __init__(self, client: SportRadarClient, status_file: str = "sync_status.json"):
        self.client = client
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        self.status_file_path = os.path.join(curr_dir, status_file)

    def execute_full_sync(self) -> Dict[str, Any]:
        """Runs full synchronization across all required tennis domains."""
        start_time = time.time()
        sync_timestamp = datetime.now(timezone.utc).isoformat()
        logger.info(f"Initiating full Tennis Intelligence Platform sync at {sync_timestamp}")

        sync_results = {
            "last_sync_timestamp": sync_timestamp,
            "status": "IN_PROGRESS",
            "categories_count": 0,
            "competitions_count": 0,
            "complexes_count": 0,
            "venues_count": 0,
            "rankings_count": 0,
            "competitors_count": 0,
            "errors": [],
            "duration_seconds": 0.0,
            "data_mode": "LIVE" if (self.client.api_key and self.client.api_key != "your_sportradar_api_key_here") else "FIXTURE_MOCK"
        }

        try:
            # 1. Fetch Competitions & Categories
            logger.info("Extracting Competitions & Categories...")
            comp_data = self.client.get_competitions()
            sync_results["categories_count"] = len(comp_data.get("categories", []))
            sync_results["competitions_count"] = len(comp_data.get("competitions", []))

            # 2. Fetch Complexes & Venues
            logger.info("Extracting Complexes & Venues...")
            complex_data = self.client.get_complexes()
            complexes = complex_data.get("complexes", [])
            sync_results["complexes_count"] = len(complexes)
            total_venues = sum(len(c.get("venues", [])) for c in complexes)
            sync_results["venues_count"] = total_venues

            # 3. Fetch Doubles Rankings & Competitors
            logger.info("Extracting Doubles Rankings & Competitor Details...")
            rank_data = self.client.get_doubles_rankings()
            rankings = rank_data.get("rankings", [])
            sync_results["rankings_count"] = len(rankings)
            sync_results["competitors_count"] = len(rankings)

            sync_results["status"] = "SUCCESS"
            logger.info("All endpoints extracted successfully.")

        except Exception as e:
            logger.error(f"Sync failed with error: {e}")
            sync_results["status"] = "FAILED"
            sync_results["errors"].append(str(e))

        finally:
            duration = round(time.time() - start_time, 2)
            sync_results["duration_seconds"] = duration
            self._save_sync_status(sync_results)
            logger.info(f"Sync finalized in {duration}s. Status: {sync_results['status']}")

        return sync_results

    def _save_sync_status(self, results: Dict[str, Any]):
        """Persists the latest sync result to disk for admin dashboard monitoring."""
        try:
            with open(self.status_file_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Sync status saved to {self.status_file_path}")
        except Exception as e:
            logger.error(f"Failed to persist sync status: {e}")

    def get_last_sync_info(self) -> Dict[str, Any]:
        """Returns the last saved sync metadata."""
        if os.path.exists(self.status_file_path):
            with open(self.status_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"status": "NEVER_RUN", "last_sync_timestamp": None}
