"""
Tennis Intelligence Platform (TIP) - Main FastAPI Application
"""
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Setup python paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
sys.path.append(CURRENT_DIR)
sys.path.append(PROJECT_ROOT)

from app.core.config import settings
from app.api.v1.api import api_router
from app.database.connection import engine, Base, SessionLocal
from app.models.entities import Competitor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & Shutdown lifecycle handler."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed if empty
    db = SessionLocal()
    try:
        count = db.query(Competitor).count()
        if count == 0:
            print("[INFO] Database empty. Triggering automated seed pipeline...")
            from sql.seed_database import seed_database
            seed_database()
    except Exception as e:
        print(f"[WARNING] Database check/seed error: {e}")
    finally:
        db.close()
    
    yield
    print("[INFO] Shutting down Tennis Intelligence Platform API.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "**AI-Powered Tennis Analytics, Player Intelligence, Ranking Analysis & Smart Insights**\n\n"
        "Engineered with FastAPI, PostgreSQL, Scikit-Learn, and SportRadar Tennis APIs.\n"
        "Features 100% data-grounded AI sports analysis, ML clustering, and radar trait profiling."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "documentation": "/docs",
        "health_check": f"{settings.API_V1_PREFIX}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
