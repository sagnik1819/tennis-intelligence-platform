"""
Module 7: Analytics Service (High-Concurrency Cached Edition)
Computes platform KPIs, country distributions, ML player profiles, and comparisons
using L1/L2 caching with single-flight locking so KMeans & SQL aggregations run
once per TTL window rather than per HTTP request.
"""
import sys
import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURR_DIR, "..", "..", ".."))
sys.path.append(os.path.join(PROJECT_ROOT, "backend"))
sys.path.append(os.path.join(PROJECT_ROOT, "machine-learning", "models"))

from app.core.cache import cache_service
from app.core.config import settings
from app.database.connection import get_db_context
from app.models.entities import Competitor, CompetitorRanking, Competition, Complex, Venue
from cluster_engine import ml_engine

CACHE_KEY_PLAYERS_BUNDLE = "analytics:players_bundle:v1"
CACHE_KEY_KPIS = "analytics:kpis:v1"
CACHE_KEY_COUNTRIES = "analytics:countries:v1"


def _compute_players_bundle(db: Optional[Session] = None) -> Dict[str, Any]:
    def _query(session: Session) -> Dict[str, Any]:
        records = (
            session.query(Competitor, CompetitorRanking)
            .outerjoin(CompetitorRanking, Competitor.competitor_id == CompetitorRanking.competitor_id)
            .order_by(CompetitorRanking.rank.asc())
            .all()
        )
        raw_players = [
            {
                "competitor_id": comp.competitor_id,
                "name": comp.name,
                "country": comp.country,
                "country_code": comp.country_code,
                "abbreviation": comp.abbreviation,
                "rank": rank.rank if rank else 999,
                "points": rank.points if rank else 0,
                "movement": rank.movement if rank else 0,
                "competitions_played": rank.competitions_played if rank else 0,
            }
            for comp, rank in records
        ]
        profiled = ml_engine.fit_and_profile(raw_players)
        by_id = {p["competitor_id"]: p for p in profiled}
        return {"items": profiled, "by_id": by_id}

    if db is not None:
        return _query(db)
    with get_db_context() as local_db:
        return _query(local_db)


def _compute_platform_kpis(db: Optional[Session] = None) -> Dict[str, Any]:
    def _query(session: Session) -> Dict[str, Any]:
        total_players = session.query(Competitor).count()
        total_competitions = session.query(Competition).count()
        total_complexes = session.query(Complex).count()
        total_venues = session.query(Venue).count()
        countries_count = session.query(func.count(func.distinct(Competitor.country))).scalar() or 0

        highest_rank_record = (
            session.query(Competitor.name, CompetitorRanking.points)
            .join(CompetitorRanking, Competitor.competitor_id == CompetitorRanking.competitor_id)
            .order_by(CompetitorRanking.points.desc())
            .first()
        )
        avg_pts = session.query(func.avg(CompetitorRanking.points)).scalar() or 0.0

        return {
            "total_players": total_players,
            "total_competitions": total_competitions,
            "total_complexes": total_complexes,
            "total_venues": total_venues,
            "countries_represented": countries_count,
            "highest_points": highest_rank_record[1] if highest_rank_record else 0,
            "highest_points_player": highest_rank_record[0] if highest_rank_record else "N/A",
            "average_points": round(float(avg_pts), 1),
            "last_sync_timestamp": "2026-11-04T10:00:00Z",
            "system_status": "OPERATIONAL",
        }

    if db is not None:
        return _query(db)
    with get_db_context() as local_db:
        return _query(local_db)


def _compute_country_analytics(db: Optional[Session] = None) -> List[Dict[str, Any]]:
    def _query(session: Session) -> List[Dict[str, Any]]:
        results = (
            session.query(
                Competitor.country,
                Competitor.country_code,
                func.count(Competitor.competitor_id).label("player_count"),
                func.coalesce(func.sum(CompetitorRanking.points), 0).label("total_points"),
                func.coalesce(func.avg(CompetitorRanking.points), 0.0).label("avg_points"),
            )
            .outerjoin(CompetitorRanking, Competitor.competitor_id == CompetitorRanking.competitor_id)
            .group_by(Competitor.country, Competitor.country_code)
            .order_by(desc("player_count"), desc("total_points"))
            .all()
        )
        return [
            {
                "country": r[0],
                "country_code": r[1],
                "player_count": int(r[2]),
                "total_points": int(r[3]),
                "avg_points": round(float(r[4]), 1),
            }
            for r in results
        ]

    if db is not None:
        return _query(db)
    with get_db_context() as local_db:
        return _query(local_db)


class AnalyticsService:
    @staticmethod
    def get_players_bundle(db: Optional[Session] = None) -> Dict[str, Any]:
        """Returns cached {items, by_id} player profiles with single-flight stampede protection."""
        return cache_service.get_or_compute(
            CACHE_KEY_PLAYERS_BUNDLE,
            settings.CACHE_TTL_PLAYERS,
            lambda: _compute_players_bundle(db),
            should_cache=lambda bundle: bool(bundle and bundle.get("items")),
        )

    @staticmethod
    async def get_players_bundle_async() -> Dict[str, Any]:
        """Zero-threadpool async fast-path on L1 hit; opens DB only on cache miss."""
        return await cache_service.get_or_compute_async(
            CACHE_KEY_PLAYERS_BUNDLE,
            settings.CACHE_TTL_PLAYERS,
            lambda: _compute_players_bundle(None),
            should_cache=lambda bundle: bool(bundle and bundle.get("items")),
        )

    @classmethod
    def get_all_players_profiled(cls, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """Queries all competitors with rankings and returns cached ML trait profiles."""
        return cls.get_players_bundle(db)["items"]

    @classmethod
    def get_platform_kpis(cls, db: Optional[Session] = None) -> Dict[str, Any]:
        """Calculates cached global KPIs for the main dashboard header."""
        return cache_service.get_or_compute(
            CACHE_KEY_KPIS,
            settings.CACHE_TTL_ANALYTICS,
            lambda: _compute_platform_kpis(db),
            should_cache=lambda k: bool(k and k.get("total_players", 0) > 0),
        )

    @staticmethod
    async def get_platform_kpis_async() -> Dict[str, Any]:
        """Async cached global KPIs (0 DB hits when warm)."""
        return await cache_service.get_or_compute_async(
            CACHE_KEY_KPIS,
            settings.CACHE_TTL_ANALYTICS,
            lambda: _compute_platform_kpis(None),
            should_cache=lambda k: bool(k and k.get("total_players", 0) > 0),
        )

    @classmethod
    def get_country_analytics(cls, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """Aggregates player metrics by country (cached)."""
        return cache_service.get_or_compute(
            CACHE_KEY_COUNTRIES,
            settings.CACHE_TTL_ANALYTICS,
            lambda: _compute_country_analytics(db),
            should_cache=bool,
        )

    @staticmethod
    async def get_country_analytics_async() -> List[Dict[str, Any]]:
        """Async cached country metrics."""
        return await cache_service.get_or_compute_async(
            CACHE_KEY_COUNTRIES,
            settings.CACHE_TTL_ANALYTICS,
            lambda: _compute_country_analytics(None),
            should_cache=bool,
        )

    @staticmethod
    def compare_players_from_bundle(bundle: Dict[str, Any], player_a_id: str, player_b_id: str) -> Dict[str, Any]:
        """O(1) comparison using cached dictionary lookup."""
        by_id = bundle["by_id"]
        p_a = by_id.get(player_a_id)
        p_b = by_id.get(player_b_id)

        if not p_a or not p_b:
            raise ValueError("One or both player IDs not found in database.")

        metrics_table = []

        # 1. Official Rank (Lower number is better)
        rank_adv = "player_a" if p_a["rank"] < p_b["rank"] else ("player_b" if p_b["rank"] < p_a["rank"] else "equal")
        metrics_table.append({
            "metric": "Official World Rank",
            "player_a_value": f"#{p_a['rank']}",
            "player_b_value": f"#{p_b['rank']}",
            "advantage": rank_adv,
            "difference": f"{abs(p_a['rank'] - p_b['rank'])} positions",
        })

        # 2. Ranking Points (Higher is better)
        pts_diff = p_a["points"] - p_b["points"]
        pts_adv = "player_a" if pts_diff > 0 else ("player_b" if pts_diff < 0 else "equal")
        metrics_table.append({
            "metric": "Ranking Points",
            "player_a_value": f"{p_a['points']:,} pts",
            "player_b_value": f"{p_b['points']:,} pts",
            "advantage": pts_adv,
            "difference": f"{abs(pts_diff):,} pts",
        })

        # 3. Competitions Played
        comp_diff = p_a["competitions_played"] - p_b["competitions_played"]
        comp_adv = "player_a" if comp_diff > 0 else ("player_b" if comp_diff < 0 else "equal")
        metrics_table.append({
            "metric": "Tournaments Played",
            "player_a_value": p_a["competitions_played"],
            "player_b_value": p_b["competitions_played"],
            "advantage": comp_adv,
            "difference": f"{abs(comp_diff)} events",
        })

        # 4. Points Per Tournament Efficiency
        eff_a = round(p_a["points"] / max(p_a["competitions_played"], 1), 1)
        eff_b = round(p_b["points"] / max(p_b["competitions_played"], 1), 1)
        eff_adv = "player_a" if eff_a > eff_b else ("player_b" if eff_b > eff_a else "equal")
        metrics_table.append({
            "metric": "Points / Tournament Efficiency",
            "player_a_value": f"{eff_a} pts/event",
            "player_b_value": f"{eff_b} pts/event",
            "advantage": eff_adv,
            "difference": f"{round(abs(eff_a - eff_b), 1)} pts/event",
        })

        # AI Comparative Explanation
        higher_pts_name = p_a["name"] if pts_diff >= 0 else p_b["name"]
        eff_name = p_a["name"] if eff_a >= eff_b else p_b["name"]
        ai_analysis = (
            f"Analytical Summary: {p_a['name']} ({p_a['country']}) vs {p_b['name']} ({p_b['country']}). "
            f"{higher_pts_name} holds the points advantage. In terms of efficiency, {eff_name} delivers "
            f"higher points output per competition played ({max(eff_a, eff_b)} vs {min(eff_a, eff_b)} pts/event). "
            f"Both competitors demonstrate strong presence in the {p_a['cluster_tier']} and {p_b['cluster_tier']}."
        )

        return {
            "player_a": p_a,
            "player_b": p_b,
            "metrics_table": metrics_table,
            "ai_comparison_analysis": ai_analysis,
            "missing_data_warnings": ["Head-to-head match scores are not covered in the doubles rankings feed."],
        }

    @classmethod
    def compare_players(cls, db: Optional[Session], player_a_id: str, player_b_id: str) -> Dict[str, Any]:
        """Compares two players side-by-side with O(1) lookup from cache."""
        bundle = cls.get_players_bundle(db)
        return cls.compare_players_from_bundle(bundle, player_a_id, player_b_id)

    @classmethod
    async def compare_players_async(cls, player_a_id: str, player_b_id: str) -> Dict[str, Any]:
        """Async O(1) player comparison."""
        bundle = await cls.get_players_bundle_async()
        return cls.compare_players_from_bundle(bundle, player_a_id, player_b_id)
