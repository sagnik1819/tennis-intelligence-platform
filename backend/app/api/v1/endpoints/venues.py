"""
Venues & Complexes Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from app.database.connection import get_db
from app.models.entities import Venue, Complex
from app.schemas.api_schemas import VenueResponse, ComplexResponse

router = APIRouter()

@router.get("", response_model=List[VenueResponse])
def get_venues(
    country: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Lists tennis court venues with their complex names, cities, and timezones."""
    query = db.query(Venue).join(Complex, Venue.complex_id == Complex.complex_id)
    if country:
        query = query.filter(Venue.country_name.ilike(f"%{country}%"))
    
    venues = query.all()
    return [
        {
            "venue_id": v.venue_id,
            "venue_name": v.venue_name,
            "city_name": v.city_name,
            "country_name": v.country_name,
            "country_code": v.country_code,
            "timezone": v.timezone,
            "complex_name": v.complex.complex_name if v.complex else "Unknown Complex"
        }
        for v in venues
    ]

@router.get("/complexes", response_model=List[ComplexResponse])
def get_complexes(db: Session = Depends(get_db)):
    """Lists tennis complexes with their court venue counts."""
    complexes = db.query(Complex).all()
    results = []
    for cx in complexes:
        venues_list = [
            {"venue_id": v.venue_id, "venue_name": v.venue_name, "city": v.city_name, "country": v.country_name}
            for v in cx.venues
        ]
        results.append({
            "complex_id": cx.complex_id,
            "complex_name": cx.complex_name,
            "venues_count": len(cx.venues),
            "venues": venues_list
        })
    return results
