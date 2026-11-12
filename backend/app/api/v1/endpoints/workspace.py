"""
User Workspace & Favourites Endpoints
Manages bookmarked players with O(1) profile resolution from cache.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from app.database.connection import get_db
from app.models.entities import UserFavourite, Competitor
from app.schemas.api_schemas import CompetitorSummary, FavouriteToggleResponse
from app.core.security import get_current_user
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/favourites", response_model=List[CompetitorSummary])
def get_user_favourites(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """UNIQUE FEATURE 6: Retrieves all players saved to current user's workspace using O(1) lookup."""
    fav_ids = [
        row[0]
        for row in db.query(UserFavourite.competitor_id)
        .filter(UserFavourite.user_id == current_user.user_id)
        .all()
    ]
    if not fav_ids:
        return []

    by_id = AnalyticsService.get_players_bundle(db)["by_id"]
    return [by_id[cid] for cid in fav_ids if cid in by_id]


@router.post("/favourites/{competitor_id}", response_model=FavouriteToggleResponse)
def toggle_favourite(
    competitor_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Toggles bookmarking of a tennis competitor."""
    existing = db.query(UserFavourite).filter(
        UserFavourite.user_id == current_user.user_id,
        UserFavourite.competitor_id == competitor_id,
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {
            "competitor_id": competitor_id,
            "is_favourite": False,
            "message": "Player removed from your workspace.",
        }

    comp = db.query(Competitor).filter(Competitor.competitor_id == competitor_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Competitor ID not found")

    fav = UserFavourite(user_id=current_user.user_id, competitor_id=competitor_id)
    db.add(fav)
    db.commit()
    return {
        "competitor_id": competitor_id,
        "is_favourite": True,
        "message": f"{comp.name} added to your workspace favourites!",
    }
