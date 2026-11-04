"""
Players & Intelligence Profile Endpoints
Supports search, country filter, pagination, radar traits, and similar competitors.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import sys
import os

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURR_DIR, "..", "..", "..", ".."))
sys.path.append(os.path.join(PROJECT_ROOT, "backend"))
sys.path.append(os.path.join(PROJECT_ROOT, "machine-learning", "models"))

from app.database.connection import get_db
from app.models.entities import Competitor, CompetitorRanking, UserFavourite
from app.schemas.api_schemas import PaginatedPlayersResponse, PlayerDetailResponse, CompetitorSummary
from app.services.analytics_service import AnalyticsService
from app.core.security import get_optional_user
from cluster_engine import ml_engine

router = APIRouter()


@router.get("", response_model=PaginatedPlayersResponse)
def get_players(
    search: Optional[str] = Query(None, description="Search player name or country"),
    country: Optional[str] = Query(None, description="Filter by country name"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Returns paginated, searchable, ML-profiled tennis competitors."""
    profiled_players = AnalyticsService.get_all_players_profiled(db)

    # Filter by search
    if search:
        s_lower = search.lower()
        profiled_players = [
            p for p in profiled_players
            if s_lower in p["name"].lower() or s_lower in p["country"].lower() or s_lower in p["abbreviation"].lower()
        ]

    # Filter by country
    if country:
        profiled_players = [
            p for p in profiled_players
            if p["country"].lower() == country.lower()
        ]

    total = len(profiled_players)
    pages = max(1, (total + limit - 1) // limit)
    offset = (page - 1) * limit
    paginated_items = profiled_players[offset: offset + limit]

    return {
        "items": paginated_items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }


@router.get("/{competitor_id}", response_model=PlayerDetailResponse)
def get_player_intelligence(
    competitor_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """
    UNIQUE FEATURE 1: Comprehensive Player Intelligence Profile.
    Includes 5-axis radar traits, similar-player recommendations, and AI summary.
    """
    profiled_players = AnalyticsService.get_all_players_profiled(db)
    target = next((p for p in profiled_players if p["competitor_id"] == competitor_id), None)

    if not target:
        raise HTTPException(status_code=404, detail="Competitor not found")

    # Similar players from ML Engine
    similar_players = ml_engine.get_similar_players(competitor_id, profiled_players, top_n=3)

    # Check if favourite
    is_fav = False
    if current_user:
        fav_exists = db.query(UserFavourite).filter(
            UserFavourite.user_id == current_user.user_id,
            UserFavourite.competitor_id == competitor_id
        ).first()
        is_fav = bool(fav_exists)

    # AI Summary
    ai_summary = (
        f"{target['name']} ({target['country']}) currently holds world rank #{target['rank']} with {target['points']:,} points. "
        f"Classified into the {target['cluster_tier']} with a consistency rating of {target['traits']['consistency']}/100 "
        f"and power volume of {target['traits']['power_volume']}/100 across {target['competitions_played']} competitions played."
    )

    ranking_detail = {
        "rank": target["rank"],
        "movement": target["movement"],
        "points": target["points"],
        "competitions_played": target["competitions_played"]
    }

    return {
        "competitor_id": target["competitor_id"],
        "name": target["name"],
        "country": target["country"],
        "country_code": target["country_code"],
        "abbreviation": target["abbreviation"],
        "ranking": ranking_detail,
        "traits": target["traits"],
        "cluster_tier": target["cluster_tier"],
        "ai_summary": ai_summary,
        "similar_players": similar_players,
        "is_favourite": is_fav
    }
