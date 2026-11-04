"""
Module 2: SportRadar API Integration Client
Handles authentication, rate-limiting, exponential backoff, error recovery,
and seamless fallback to high-fidelity offline mock data.
"""
import os
import time
import json
import logging
from typing import Dict, Any, Optional
import urllib.request
import urllib.error

# Configure standard logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s"
)
logger = logging.getLogger("SportRadarClient")


class SportRadarClient:
    """
    Client for SportRadar Tennis API v3.
    Includes rate-limiting (1 req/sec for trial tier), exponential backoff,
    and automatic fallback to offline fixtures when offline or key is missing.
    """
    BASE_URL = "https://api.sportradar.com/tennis/{access_level}/{version}/{language}"

    def __init__(
        self,
        api_key: Optional[str] = None,
        access_level: str = "trial",
        version: str = "v3",
        language: str = "en",
        format_type: str = "json",
        min_request_interval: float = 1.0,
        mock_data_dir: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("SPORTRADAR_API_KEY", "")
        self.access_level = access_level
        self.version = version
        self.language = language
        self.format_type = format_type
        self.min_request_interval = min_request_interval
        self._last_request_time = 0.0

        # Base directory for mock fixture fallbacks
        if mock_data_dir is None:
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            self.mock_data_dir = os.path.join(curr_dir, "..", "sample_data")
        else:
            self.mock_data_dir = mock_data_dir

    def _throttle(self):
        """Enforces rate limit (e.g. 1 req/sec) to avoid 429 errors on trial keys."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.min_request_interval:
            sleep_needed = self.min_request_interval - elapsed
            logger.debug(f"Throttling request for {sleep_needed:.2f}s...")
            time.sleep(sleep_needed)
        self._last_request_time = time.time()

    def _load_mock_fallback(self, fixture_name: str) -> Dict[str, Any]:
        """Loads offline mock fixture to guarantee uninterrupted development."""
        file_path = os.path.join(self.mock_data_dir, fixture_name)
        logger.warning(f"Using fallback offline fixture: {fixture_name}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Fixture file not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _execute_request(self, endpoint_path: str, fallback_fixture: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Executes HTTP GET with query params, rate throttling, and exponential backoff retry.
        If API key is missing or invalid, immediately falls back to mock fixture.
        """
        if not self.api_key or self.api_key == "your_sportradar_api_key_here":
            logger.info("No active SportRadar API key detected. Engaging offline fixture mode.")
            return self._load_mock_fallback(fallback_fixture)

        base_endpoint = self.BASE_URL.format(
            access_level=self.access_level,
            version=self.version,
            language=self.language
        )
        url = f"{base_endpoint}/{endpoint_path}.{self.format_type}?api_key={self.api_key}"

        for attempt in range(1, max_retries + 1):
            try:
                self._throttle()
                logger.info(f"Fetching API: {endpoint_path} (Attempt {attempt}/{max_retries})")
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "TennisIntelligencePlatform/1.0", "Accept": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        raw_data = resp.read().decode("utf-8")
                        logger.info(f"Successfully received data for {endpoint_path}")
                        return json.loads(raw_data)

            except urllib.error.HTTPError as he:
                logger.warning(f"HTTP Error {he.code} for {endpoint_path}: {he.reason}")
                if he.code in (429, 500, 502, 503, 504):
                    wait_time = 2 ** attempt
                    logger.warning(f"Backing off for {wait_time}s before retry...")
                    time.sleep(wait_time)
                elif he.code in (401, 403):
                    logger.error(f"Unauthorized/Forbidden (Invalid or expired API Key). Falling back to mock data.")
                    return self._load_mock_fallback(fallback_fixture)
                else:
                    break
            except urllib.error.URLError as ue:
                logger.error(f"Network connection failed: {ue.reason}. Falling back to mock data.")
                return self._load_mock_fallback(fallback_fixture)
            except Exception as e:
                logger.error(f"Unexpected error calling {endpoint_path}: {e}")
                break

        logger.warning(f"Exhausted retries or failed request for {endpoint_path}. Utilizing mock fixture.")
        return self._load_mock_fallback(fallback_fixture)

    def get_competitions(self) -> Dict[str, Any]:
        """Fetch categories and competitions hierarchy."""
        return self._execute_request("competitions", "competitions.json")

    def get_complexes(self) -> Dict[str, Any]:
        """Fetch tennis complexes and nested venues."""
        return self._execute_request("complexes", "complexes.json")

    def get_doubles_rankings(self) -> Dict[str, Any]:
        """Fetch doubles competitor rankings and competitor profiles."""
        return self._execute_request("double_competitor_rankings", "doubles_rankings.json")
