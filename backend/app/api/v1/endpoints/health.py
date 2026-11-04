"""
Health Check Endpoint
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from app.database.connection import get_db
from app.schemas.api_schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)):
    """Returns system status, version, and database connection state."""
    db_status = "connected"
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unreachable: {e}"

    return {
        "status": "online",
        "version": "1.0.0",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
