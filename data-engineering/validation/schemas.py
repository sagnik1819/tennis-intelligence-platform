"""
Module 3: Pydantic Validation Schemas for Raw Ingestion
Guarantees schema integrity, data types, and required field existence.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class CategorySchema(BaseModel):
    id: str = Field(..., description="Unique category ID")
    name: str = Field(..., min_length=1, description="Category name")


class CompetitionSchema(BaseModel):
    id: str = Field(..., description="Unique competition ID")
    name: str = Field(..., min_length=1, description="Name of the competition")
    parent_id: Optional[str] = None
    type: str = Field(default="doubles", description="Competition type (singles/doubles)")
    gender: str = Field(default="men", description="Gender category")
    category: Optional[CategorySchema] = None


class VenueSchema(BaseModel):
    id: str = Field(..., description="Unique venue ID")
    name: str = Field(..., min_length=1, description="Venue court name")
    city_name: str = Field(default="Unknown", description="City of venue")
    country_name: str = Field(default="Unknown", description="Country of venue")
    country_code: str = Field(default="UNK", max_length=3, description="ISO country code")
    timezone: str = Field(default="UTC", description="Local timezone string")


class ComplexSchema(BaseModel):
    id: str = Field(..., description="Unique sports complex ID")
    name: str = Field(..., min_length=1, description="Complex name")
    venues: List[VenueSchema] = Field(default_factory=list)


class CompetitorSchema(BaseModel):
    id: str = Field(..., description="Unique competitor ID")
    name: str = Field(..., min_length=1, description="Player full name")
    country: str = Field(default="Unknown")
    country_code: str = Field(default="UNK", max_length=3)
    abbreviation: str = Field(default="UNK", max_length=10)


class RankingItemSchema(BaseModel):
    rank: int = Field(..., ge=1, description="Current official ranking")
    movement: int = Field(default=0, description="Week-over-week movement")
    points: int = Field(default=0, ge=0, description="Total ranking points")
    competitions_played: int = Field(default=0, ge=0, description="Total competitions played")
    competitor: CompetitorSchema
