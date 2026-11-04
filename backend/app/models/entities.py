"""
Module 4: SQLAlchemy Relational ORM Models
Defines all 10 entities, foreign keys, relationships, and table constraints.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database")))
from connection import Base


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(String(50), primary_key=True, index=True)
    category_name = Column(String(100), nullable=False)

    competitions = relationship("Competition", back_populates="category", cascade="all, delete-orphan")


class Competition(Base):
    __tablename__ = "competitions"

    competition_id = Column(String(50), primary_key=True, index=True)
    competition_name = Column(String(100), nullable=False)
    parent_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=True)
    type = Column(String(20), nullable=False, default="doubles")
    gender = Column(String(10), nullable=False, default="men")
    category_id = Column(String(50), ForeignKey("categories.category_id"), nullable=False, index=True)

    category = relationship("Category", back_populates="competitions")
    sub_competitions = relationship("Competition", backref="parent_competition", remote_side=[competition_id])


class Complex(Base):
    __tablename__ = "complexes"

    complex_id = Column(String(50), primary_key=True, index=True)
    complex_name = Column(String(100), nullable=False)

    venues = relationship("Venue", back_populates="complex", cascade="all, delete-orphan")


class Venue(Base):
    __tablename__ = "venues"

    venue_id = Column(String(50), primary_key=True, index=True)
    venue_name = Column(String(100), nullable=False)
    city_name = Column(String(100), nullable=False)
    country_name = Column(String(100), nullable=False, index=True)
    country_code = Column(String(3), nullable=False)
    timezone = Column(String(100), nullable=False, default="UTC")
    complex_id = Column(String(50), ForeignKey("complexes.complex_id"), nullable=False, index=True)

    complex = relationship("Complex", back_populates="venues")


class Competitor(Base):
    __tablename__ = "competitors"

    competitor_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False, index=True)
    country_code = Column(String(3), nullable=False)
    abbreviation = Column(String(10), nullable=False)

    rankings = relationship("CompetitorRanking", back_populates="competitor", cascade="all, delete-orphan")
    favourited_by = relationship("UserFavourite", back_populates="competitor", cascade="all, delete-orphan")


class CompetitorRanking(Base):
    __tablename__ = "competitor_rankings"

    rank_id = Column(Integer, primary_key=True, autoincrement=True)
    rank = Column(Integer, nullable=False, index=True)
    movement = Column(Integer, nullable=False, default=0)
    points = Column(Integer, nullable=False, index=True)
    competitions_played = Column(Integer, nullable=False, default=0)
    competitor_id = Column(String(50), ForeignKey("competitors.competitor_id"), nullable=False, index=True)

    competitor = relationship("Competitor", back_populates="rankings")


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), nullable=False, default="user")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    favourites = relationship("UserFavourite", back_populates="user", cascade="all, delete-orphan")
    ai_interactions = relationship("AIInteraction", back_populates="user")


class UserFavourite(Base):
    __tablename__ = "user_favourites"

    fav_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    competitor_id = Column(String(50), ForeignKey("competitors.competitor_id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("user_id", "competitor_id", name="uq_user_competitor"),)

    user = relationship("User", back_populates="favourites")
    competitor = relationship("Competitor", back_populates="favourited_by")


class AIInteraction(Base):
    __tablename__ = "ai_interactions"

    interaction_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="ai_interactions")


class SyncLog(Base):
    __tablename__ = "sync_logs"

    sync_id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(50), nullable=False)
    data_mode = Column(String(50), nullable=False)
    records_processed = Column(Integer, nullable=False, default=0)
    duration_seconds = Column(Numeric(6, 2), default=0.0)
    synced_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
