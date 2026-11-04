"""
API v1 Router Aggregator
Combines all modular endpoints under the /api/v1 namespace.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    players,
    rankings,
    competitions,
    venues,
    analytics,
    assistant,
    workspace,
    admin
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["System Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(players.router, prefix="/players", tags=["Players & Profiles"])
api_router.include_router(rankings.router, prefix="/rankings", tags=["Rankings"])
api_router.include_router(competitions.router, prefix="/competitions", tags=["Competitions"])
api_router.include_router(venues.router, prefix="/venues", tags=["Venues & Complexes"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & Comparison"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["AI Tennis Assistant"])
api_router.include_router(workspace.router, prefix="/workspace", tags=["User Workspace"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin & Data Quality"])
