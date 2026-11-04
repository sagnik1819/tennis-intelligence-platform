"""
Competitions & Categories Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from app.database.connection import get_db
from app.models.entities import Competition, Category
from app.schemas.api_schemas import CompetitionResponse

router = APIRouter()

@router.get("", response_model=List[CompetitionResponse])
def get_competitions(
    type_filter: Optional[str] = Query(None, description="e.g. doubles or singles"),
    category_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Lists competitions with category names and parent-child hierarchy."""
    query = db.query(Competition).join(Category, Competition.category_id == Category.category_id)
    
    if type_filter:
        query = query.filter(Competition.type == type_filter.lower())
    if category_id:
        query = query.filter(Competition.category_id == category_id)

    comps = query.all()
    results = []
    for c in comps:
        results.append({
            "competition_id": c.competition_id,
            "competition_name": c.competition_name,
            "type": c.type,
            "gender": c.gender,
            "category_name": c.category.category_name if c.category else "General",
            "parent_id": c.parent_id
        })
    return results
