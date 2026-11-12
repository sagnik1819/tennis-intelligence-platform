"""
Analytics Endpoints: KPIs, Country-wise Intelligence, and Smart Player Comparison
All read analytics use pre-encoded L1/L2 caching with single-flight protection.
"""
from typing import List, Optional
from fastapi import APIRouter, Header, Query, HTTPException
from pydantic import TypeAdapter
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from app.core.cache import cache_service, dump_validated_json
from app.core.config import settings
from app.schemas.api_schemas import PlatformKPIs, CountryAnalyticsItem, PlayerComparisonResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter()

_KPIS_ADAPTER = TypeAdapter(PlatformKPIs)
_COUNTRIES_ADAPTER = TypeAdapter(List[CountryAnalyticsItem])
_COMPARE_ADAPTER = TypeAdapter(PlayerComparisonResponse)


@router.get("/kpis", response_model=PlatformKPIs)
async def get_kpis(accept_encoding: Optional[str] = Header(None)):
    """Global headline metrics for the dashboard."""
    def _build():
        data = AnalyticsService.get_platform_kpis()
        return data, dump_validated_json(_KPIS_ADAPTER, data)

    encoded = await cache_service.get_or_encode_async(
        "encoded:analytics:kpis:v1",
        settings.CACHE_TTL_ANALYTICS,
        _build,
        should_cache=lambda d: bool(d and d.get("total_players", 0) > 0),
    )
    return encoded.to_response(accept_encoding)


@router.get("/countries", response_model=List[CountryAnalyticsItem])
async def get_country_analytics(accept_encoding: Optional[str] = Header(None)):
    """Country-level player counts, total points, and averages."""
    def _build():
        data = AnalyticsService.get_country_analytics()
        return data, dump_validated_json(_COUNTRIES_ADAPTER, data)

    encoded = await cache_service.get_or_encode_async(
        "encoded:analytics:countries:v1",
        settings.CACHE_TTL_ANALYTICS,
        _build,
        should_cache=bool,
    )
    return encoded.to_response(accept_encoding)


@router.get("/compare", response_model=PlayerComparisonResponse)
async def compare_players(
    player_a: str = Query(..., description="Competitor ID for first player"),
    player_b: str = Query(..., description="Competitor ID for second player"),
    accept_encoding: Optional[str] = Header(None),
):
    """
    UNIQUE FEATURE 2: Smart Player Comparison.
    Produces side-by-side metric tables, advantage indicators, and AI analysis.
    """
    try:
        def _build():
            data = AnalyticsService.compare_players(None, player_a, player_b)
            return data, dump_validated_json(_COMPARE_ADAPTER, data)

        encoded = await cache_service.get_or_encode_async(
            f"encoded:analytics:compare:{player_a}:{player_b}",
            settings.CACHE_TTL_PLAYERS,
            _build,
            should_cache=bool,
        )
        return encoded.to_response(accept_encoding)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {e}")
