"""
Venues & Complexes Endpoints (Eager-Loaded & Pre-Encoded)
"""
from typing import List, Optional
from fastapi import APIRouter, Header, Query
from pydantic import TypeAdapter
from sqlalchemy.orm import joinedload, selectinload
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from app.core.cache import cache_service, dump_validated_json
from app.core.config import settings
from app.database.connection import get_db_context
from app.models.entities import Venue, Complex
from app.schemas.api_schemas import VenueResponse, ComplexResponse

router = APIRouter()
_VENUES_ADAPTER = TypeAdapter(List[VenueResponse])
_COMPLEXES_ADAPTER = TypeAdapter(List[ComplexResponse])


def _load_all_venues():
    with get_db_context() as db:
        venues = db.query(Venue).options(joinedload(Venue.complex)).all()
        return [
            {
                "venue_id": v.venue_id,
                "venue_name": v.venue_name,
                "city_name": v.city_name,
                "country_name": v.country_name,
                "country_code": v.country_code,
                "timezone": v.timezone,
                "complex_name": v.complex.complex_name if v.complex else "Unknown Complex",
            }
            for v in venues
        ]


def _load_all_complexes():
    with get_db_context() as db:
        complexes = db.query(Complex).options(selectinload(Complex.venues)).all()
        return [
            {
                "complex_id": cx.complex_id,
                "complex_name": cx.complex_name,
                "venues_count": len(cx.venues),
                "venues": [
                    {
                        "venue_id": v.venue_id,
                        "venue_name": v.venue_name,
                        "city": v.city_name,
                        "country": v.country_name,
                    }
                    for v in cx.venues
                ],
            }
            for cx in complexes
        ]


@router.get("", response_model=List[VenueResponse])
async def get_venues(
    country: Optional[str] = Query(None),
    accept_encoding: Optional[str] = Header(None),
):
    """Lists tennis court venues with their complex names, cities, and timezones (pre-encoded)."""
    if not country:
        def _build():
            items = cache_service.get_or_compute(
                "catalog:venues:v1",
                settings.CACHE_TTL_CATALOG,
                _load_all_venues,
                should_cache=bool,
            )
            return items, dump_validated_json(_VENUES_ADAPTER, items)

        encoded = await cache_service.get_or_encode_async(
            "encoded:catalog:venues:v1",
            settings.CACHE_TTL_CATALOG,
            _build,
            should_cache=bool,
        )
        return encoded.to_response(accept_encoding)

    venues = await cache_service.get_or_compute_async(
        "catalog:venues:v1",
        settings.CACHE_TTL_CATALOG,
        _load_all_venues,
        should_cache=bool,
    )
    c_lower = country.lower()
    return [v for v in venues if c_lower in v["country_name"].lower()]


@router.get("/complexes", response_model=List[ComplexResponse])
async def get_complexes(accept_encoding: Optional[str] = Header(None)):
    """Lists tennis complexes with their court venue counts (pre-encoded)."""
    def _build():
        items = cache_service.get_or_compute(
            "catalog:complexes:v1",
            settings.CACHE_TTL_CATALOG,
            _load_all_complexes,
            should_cache=bool,
        )
        return items, dump_validated_json(_COMPLEXES_ADAPTER, items)

    encoded = await cache_service.get_or_encode_async(
        "encoded:catalog:complexes:v1",
        settings.CACHE_TTL_CATALOG,
        _build,
        should_cache=bool,
    )
    return encoded.to_response(accept_encoding)
