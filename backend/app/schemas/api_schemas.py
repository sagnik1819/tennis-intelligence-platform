"""
Module 5: Pydantic REST API Request & Response Schemas
Defines structured data contracts for endpoints, validation, and serialization.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


# ==========================================
# AUTHENTICATION SCHEMAS
# ==========================================
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password min 6 chars")
    full_name: Optional[str] = "Tennis Analyst"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class UserResponse(BaseModel):
    user_id: int
    email: str
    full_name: Optional[str]
    role: str
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==========================================
# COMPETITOR & RANKING SCHEMAS
# ==========================================
class RadarTraits(BaseModel):
    consistency: float = Field(..., description="0-100 scale")
    power_volume: float = Field(..., description="0-100 scale")
    tournament_stamina: float = Field(..., description="0-100 scale")
    rank_momentum: float = Field(..., description="0-100 scale")
    efficiency: float = Field(..., description="0-100 scale")


class PlayerRankingDetail(BaseModel):
    rank: int
    movement: int
    points: int
    competitions_played: int


class CompetitorSummary(BaseModel):
    competitor_id: str
    name: str
    country: str
    country_code: str
    abbreviation: str
    rank: Optional[int] = None
    points: Optional[int] = None
    movement: Optional[int] = None
    competitions_played: Optional[int] = None
    cluster_label: Optional[str] = "Tier Contender"
    traits: Optional[RadarTraits] = None


class PlayerDetailResponse(BaseModel):
    competitor_id: str
    name: str
    country: str
    country_code: str
    abbreviation: str
    ranking: Optional[PlayerRankingDetail] = None
    traits: RadarTraits
    cluster_tier: str
    ai_summary: str
    similar_players: List[CompetitorSummary] = []
    is_favourite: bool = False


class PaginatedPlayersResponse(BaseModel):
    items: List[CompetitorSummary]
    total: int
    page: int
    limit: int
    pages: int


# ==========================================
# COMPETITION & VENUE SCHEMAS
# ==========================================
class CompetitionResponse(BaseModel):
    competition_id: str
    competition_name: str
    type: str
    gender: str
    category_name: str
    parent_id: Optional[str] = None


class VenueResponse(BaseModel):
    venue_id: str
    venue_name: str
    city_name: str
    country_name: str
    country_code: str
    timezone: str
    complex_name: str


class ComplexResponse(BaseModel):
    complex_id: str
    complex_name: str
    venues_count: int
    venues: List[Dict[str, Any]] = []


# ==========================================
# ANALYTICS & COMPARISON SCHEMAS
# ==========================================
class CountryAnalyticsItem(BaseModel):
    country: str
    country_code: str
    player_count: int
    total_points: int
    avg_points: float


class MetricComparison(BaseModel):
    metric: str
    player_a_value: Any
    player_b_value: Any
    advantage: str  # "player_a", "player_b", or "equal"
    difference: str


class PlayerComparisonResponse(BaseModel):
    player_a: CompetitorSummary
    player_b: CompetitorSummary
    metrics_table: List[MetricComparison]
    ai_comparison_analysis: str
    missing_data_warnings: List[str] = []


class PlatformKPIs(BaseModel):
    total_players: int
    total_competitions: int
    total_complexes: int
    total_venues: int
    countries_represented: int
    highest_points: int
    highest_points_player: str
    average_points: float
    last_sync_timestamp: Optional[str]
    system_status: str


# ==========================================
# AI ASSISTANT SCHEMAS
# ==========================================
class ChatQueryRequest(BaseModel):
    prompt: str = Field(..., min_length=2, description="User question or prompt")


class DataCitation(BaseModel):
    entity: str
    reference_id: str
    label: str


class ChatQueryResponse(BaseModel):
    prompt: str
    response: str
    suggested_actions: List[str] = []
    citations: List[DataCitation] = []
    created_at: str


# ==========================================
# WORKSPACE & SYSTEM SCHEMAS
# ==========================================
class FavouriteToggleResponse(BaseModel):
    competitor_id: str
    is_favourite: bool
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    timestamp: str
