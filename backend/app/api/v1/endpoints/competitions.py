"""
Competitions & Categories Endpoints (Eager-Loaded & Pre-Encoded)
"""
from typing import List, Optional
from fastapi import APIRouter, Header, Query
from pydantic import TypeAdapter
from sqlalchemy.orm import joinedload
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from app.core.cache import cache_service, dump_validated_json
from app.core.config import settings
from app.database.connection import get_db_context
from app.models.entities import Competition
from app.schemas.api_schemas import CompetitionResponse

router = APIRouter()
_COMPETITIONS_ADAPTER = TypeAdapter(List[CompetitionResponse])


def _load_all_competitions():
    with get_db_context() as db:
        comps = db.query(Competition).options(joinedload(Competition.category)).all()
        return [
            {
                "competition_id": c.competition_id,
                "competition_name": c.competition_name,
                "type": c.type,
                "gender": c.gender,
                "category_id": c.category_id,
                "category_name": c.category.category_name if c.category else "General",
                "parent_id": c.parent_id,
            }
            for c in comps
        ]


@router.get("", response_model=List[CompetitionResponse])
async def get_competitions(
    type_filter: Optional[str] = Query(None, description="e.g. doubles or singles"),
    category_id: Optional[str] = Query(None),
    accept_encoding: Optional[str] = Header(None),
):
    """Lists competitions with category names and parent-child hierarchy (pre-encoded)."""
    if not type_filter and not category_id:
        def _build():
            items = cache_service.get_or_compute(
                "catalog:competitions:v1",
                settings.CACHE_TTL_CATALOG,
                _load_all_competitions,
                should_cache=bool,
            )
            return items, dump_validated_json(_COMPETITIONS_ADAPTER, items)

        encoded = await cache_service.get_or_encode_async(
            "encoded:catalog:competitions:v1",
            settings.CACHE_TTL_CATALOG,
            _build,
            should_cache=bool,
        )
        return encoded.to_response(accept_encoding)

    all_comps = await cache_service.get_or_compute_async(
        "catalog:competitions:v1",
        settings.CACHE_TTL_CATALOG,
        _load_all_competitions,
        should_cache=bool,
    )
    t_lower = type_filter.lower() if type_filter else None
    return [
        c for c in all_comps
        if (not t_lower or (c["type"] or "").lower() == t_lower)
        and (not category_id or c["category_id"] == category_id)
    ]
