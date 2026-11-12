"""
Rankings Endpoints (Pre-Encoded Cached Fast-Path)
"""
from typing import List, Optional
from fastapi import APIRouter, Header, Query
from pydantic import TypeAdapter
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from app.core.cache import cache_service, dump_validated_json
from app.core.config import settings
from app.schemas.api_schemas import CompetitorSummary
from app.services.analytics_service import AnalyticsService

router = APIRouter()
_TOP_RANKINGS_ADAPTER = TypeAdapter(List[CompetitorSummary])


@router.get("/top", response_model=List[CompetitorSummary])
async def get_top_rankings(
    limit: int = Query(5, ge=1, le=50),
    accept_encoding: Optional[str] = Header(None),
):
    """Returns top-ranked tennis competitors from pre-encoded L1 cache."""
    def _build():
        bundle = AnalyticsService.get_players_bundle()
        items = bundle["items"][:limit]
        return items, dump_validated_json(_TOP_RANKINGS_ADAPTER, items)

    encoded = await cache_service.get_or_encode_async(
        f"encoded:rankings:top:{limit}",
        settings.CACHE_TTL_PLAYERS,
        _build,
        should_cache=bool,
    )
    return encoded.to_response(accept_encoding)
