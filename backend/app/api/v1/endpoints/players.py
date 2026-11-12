"""
Players & Intelligence Profile Endpoints (Pre-Encoded High-Concurrency Edition)
Supports search, country filter, pagination, O(1) lookup, pre-compressed GZip payloads,
and zero-DB anonymous reads.
"""
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Query
import jwt
from pydantic import TypeAdapter
import sys
import os
from starlette.concurrency import run_in_threadpool

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURR_DIR, "..", "..", "..", ".."))
sys.path.append(os.path.join(PROJECT_ROOT, "backend"))
sys.path.append(os.path.join(PROJECT_ROOT, "machine-learning", "models"))

from app.core.cache import cache_service, dump_validated_json
from app.core.config import settings
from app.core.security import ALGORITHM, SECRET_KEY
from app.database.connection import get_db_context
from app.models.entities import User, UserFavourite
from app.schemas.api_schemas import PaginatedPlayersResponse, PlayerDetailResponse
from app.services.analytics_service import AnalyticsService
from cluster_engine import ml_engine

router = APIRouter()

_PLAYERS_PAGE_ADAPTER = TypeAdapter(PaginatedPlayersResponse)
_PLAYER_DETAIL_ADAPTER = TypeAdapter(PlayerDetailResponse)


def _check_is_favourite(authorization: str, competitor_id: str) -> bool:
    if not authorization or not authorization.startswith("Bearer "):
        return False
    token = authorization[7:].strip()
    if not token:
        return False
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return False
    except Exception:
        return False

    with get_db_context() as db:
        fav = (
            db.query(UserFavourite.fav_id)
            .join(User, UserFavourite.user_id == User.user_id)
            .filter(User.email == email, UserFavourite.competitor_id == competitor_id)
            .first()
        )
        return bool(fav)


def _build_player_detail_dict(bundle: dict, competitor_id: str, is_fav: bool) -> dict:
    by_id = bundle["by_id"]
    target = by_id.get(competitor_id)
    if not target:
        raise HTTPException(status_code=404, detail="Competitor not found")

    similar_players = ml_engine.get_similar_players(
        competitor_id, bundle["items"], top_n=3, player_lookup=by_id
    )
    ai_summary = (
        f"{target['name']} ({target['country']}) currently holds world rank #{target['rank']} with {target['points']:,} points. "
        f"Classified into the {target['cluster_tier']} with a consistency rating of {target['traits']['consistency']}/100 "
        f"and power volume of {target['traits']['power_volume']}/100 across {target['competitions_played']} competitions played."
    )
    return {
        "competitor_id": target["competitor_id"],
        "name": target["name"],
        "country": target["country"],
        "country_code": target["country_code"],
        "abbreviation": target["abbreviation"],
        "ranking": {
            "rank": target["rank"],
            "movement": target["movement"],
            "points": target["points"],
            "competitions_played": target["competitions_played"],
        },
        "traits": target["traits"],
        "cluster_tier": target["cluster_tier"],
        "ai_summary": ai_summary,
        "similar_players": similar_players,
        "is_favourite": is_fav,
    }


@router.get("", response_model=PaginatedPlayersResponse)
async def get_players(
    search: Optional[str] = Query(None, description="Search player name or country"),
    country: Optional[str] = Query(None, description="Filter by country name"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    accept_encoding: Optional[str] = Header(None),
):
    """Returns paginated, searchable, ML-profiled tennis competitors with zero-copy cache hits."""
    if not search and not country:
        def _build_page():
            bundle = AnalyticsService.get_players_bundle()
            items = bundle["items"]
            total = len(items)
            pages = max(1, (total + limit - 1) // limit)
            offset = (page - 1) * limit
            result = {
                "items": items[offset: offset + limit],
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages,
            }
            return result, dump_validated_json(_PLAYERS_PAGE_ADAPTER, result)

        encoded = await cache_service.get_or_encode_async(
            f"encoded:players:p={page}:l={limit}",
            settings.CACHE_TTL_PLAYERS,
            _build_page,
            should_cache=lambda d: bool(d.get("items")),
        )
        return encoded.to_response(accept_encoding)

    bundle = await AnalyticsService.get_players_bundle_async()
    profiled_players = bundle["items"]
    s_lower = search.lower() if search else None
    c_lower = country.lower() if country else None
    filtered = []
    for p in profiled_players:
        if s_lower and not (
            s_lower in p["name"].lower()
            or s_lower in p["country"].lower()
            or s_lower in p["abbreviation"].lower()
        ):
            continue
        if c_lower and p["country"].lower() != c_lower:
            continue
        filtered.append(p)

    total = len(filtered)
    pages = max(1, (total + limit - 1) // limit)
    offset = (page - 1) * limit
    return {
        "items": filtered[offset: offset + limit],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get("/{competitor_id}", response_model=PlayerDetailResponse)
async def get_player_intelligence(
    competitor_id: str,
    authorization: Optional[str] = Header(None),
    accept_encoding: Optional[str] = Header(None),
):
    """
    UNIQUE FEATURE 1: Comprehensive Player Intelligence Profile.
    Anonymous visitors receive pre-serialized GZip responses from L1 RAM with zero DB queries.
    """
    if not authorization or not authorization.startswith("Bearer "):
        def _build_anon_detail():
            bundle = AnalyticsService.get_players_bundle()
            detail = _build_player_detail_dict(bundle, competitor_id, is_fav=False)
            return detail, dump_validated_json(_PLAYER_DETAIL_ADAPTER, detail)

        encoded = await cache_service.get_or_encode_async(
            f"encoded:player_detail:{competitor_id}",
            settings.CACHE_TTL_PLAYERS,
            _build_anon_detail,
            should_cache=bool,
        )
        return encoded.to_response(accept_encoding)

    bundle = await AnalyticsService.get_players_bundle_async()
    is_fav = await run_in_threadpool(_check_is_favourite, authorization, competitor_id)
    return _build_player_detail_dict(bundle, competitor_id, is_fav=is_fav)
