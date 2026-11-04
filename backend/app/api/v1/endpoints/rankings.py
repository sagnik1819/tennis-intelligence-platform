"""
Rankings Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from app.database.connection import get_db
from app.schemas.api_schemas import CompetitorSummary
from app.services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/top", response_model=List[CompetitorSummary])
def get_top_rankings(
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Returns top-ranked tennis competitors."""
    profiled = AnalyticsService.get_all_players_profiled(db)
    return profiled[:limit]
