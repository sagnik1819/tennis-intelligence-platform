"""
Analytics Endpoints: KPIs, Country-wise Intelligence, and Smart Player Comparison
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from app.database.connection import get_db
from app.schemas.api_schemas import PlatformKPIs, CountryAnalyticsItem, PlayerComparisonResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/kpis", response_model=PlatformKPIs)
def get_kpis(db: Session = Depends(get_db)):
    """Global headline metrics for the dashboard."""
    return AnalyticsService.get_platform_kpis(db)


@router.get("/countries", response_model=List[CountryAnalyticsItem])
def get_country_analytics(db: Session = Depends(get_db)):
    """Country-level player counts, total points, and averages."""
    return AnalyticsService.get_country_analytics(db)


@router.get("/compare", response_model=PlayerComparisonResponse)
def compare_players(
    player_a: str = Query(..., description="Competitor ID for first player"),
    player_b: str = Query(..., description="Competitor ID for second player"),
    db: Session = Depends(get_db)
):
    """
    UNIQUE FEATURE 2: Smart Player Comparison.
    Produces side-by-side metric tables, advantage indicators, and AI analysis.
    """
    try:
        return AnalyticsService.compare_players(db, player_a, player_b)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {e}")
