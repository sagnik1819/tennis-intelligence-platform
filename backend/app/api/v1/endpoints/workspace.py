"""
User Workspace & Favourites Endpoints
Manages bookmarked players, user personalized workspace, and export features.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
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
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """UNIQUE FEATURE 6: Retrieves all players saved to current user's workspace."""
    fav_ids = [
        f.competitor_id for f in db.query(UserFavourite.competitor_id).filter(
            UserFavourite.user_id == current_user.user_id
        ).all()
    ]
    
    if not fav_ids:
        return []

    profiled = AnalyticsService.get_all_players_profiled(db)
    return [p for p in profiled if p["competitor_id"] in fav_ids]


@router.post("/favourites/{competitor_id}", response_model=FavouriteToggleResponse)
def toggle_favourite(
    competitor_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggles bookmarking of a tennis competitor."""
    existing = db.query(UserFavourite).filter(
        UserFavourite.user_id == current_user.user_id,
        UserFavourite.competitor_id == competitor_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {
            "competitor_id": competitor_id,
            "is_favourite": False,
            "message": "Player removed from your workspace."
        }
    else:
        # Check competitor exists
        comp = db.query(Competitor).filter(Competitor.competitor_id == competitor_id).first()
        if not comp:
            raise HTTPException(status_code=404, detail="Competitor ID not found")

        fav = UserFavourite(user_id=current_user.user_id, competitor_id=competitor_id)
        db.add(fav)
        db.commit()
        return {
            "competitor_id": competitor_id,
            "is_favourite": True,
            "message": f"{comp.name} added to your workspace favourites!"
        }
