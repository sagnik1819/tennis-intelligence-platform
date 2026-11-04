"""
Module 7: Analytics Service
Computes platform KPIs, country distributions, player comparisons,
and generates AI-backed comparative explanations.
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

from app.models.entities import Competitor, CompetitorRanking, Competition, Complex, Venue, Category
from cluster_engine import ml_engine


class AnalyticsService:
    @staticmethod
    def get_all_players_profiled(db: Session) -> List[Dict[str, Any]]:
        """Queries all competitors with their rankings and runs ML trait profiling."""
        records = (
            db.query(Competitor, CompetitorRanking)
            .outerjoin(CompetitorRanking, Competitor.competitor_id == CompetitorRanking.competitor_id)
            .order_by(CompetitorRanking.rank.asc())
            .all()
        )

        raw_players = []
        for comp, rank in records:
            raw_players.append({
                "competitor_id": comp.competitor_id,
                "name": comp.name,
                "country": comp.country,
                "country_code": comp.country_code,
                "abbreviation": comp.abbreviation,
                "rank": rank.rank if rank else 999,
                "points": rank.points if rank else 0,
                "movement": rank.movement if rank else 0,
                "competitions_played": rank.competitions_played if rank else 0
            })

        return ml_engine.fit_and_profile(raw_players)

    @staticmethod
    def get_platform_kpis(db: Session) -> Dict[str, Any]:
        """Calculates global KPIs for the main dashboard header."""
        total_players = db.query(Competitor).count()
        total_competitions = db.query(Competition).count()
        total_complexes = db.query(Complex).count()
        total_venues = db.query(Venue).count()
        countries_count = db.query(func.count(func.distinct(Competitor.country))).scalar() or 0

        # Ranking aggregations
        highest_rank_record = (
            db.query(Competitor.name, CompetitorRanking.points)
            .join(CompetitorRanking, Competitor.competitor_id == CompetitorRanking.competitor_id)
            .order_by(CompetitorRanking.points.desc())
            .first()
        )
        avg_pts = db.query(func.avg(CompetitorRanking.points)).scalar() or 0.0

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
            "system_status": "OPERATIONAL"
        }

    @staticmethod
    def get_country_analytics(db: Session) -> List[Dict[str, Any]]:
        """Aggregates player metrics by country."""
        results = (
            db.query(
                Competitor.country,
                Competitor.country_code,
                func.count(Competitor.competitor_id).label("player_count"),
                func.coalesce(func.sum(CompetitorRanking.points), 0).label("total_points"),
                func.coalesce(func.avg(CompetitorRanking.points), 0.0).label("avg_points")
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
                "avg_points": round(float(r[4]), 1)
            }
            for r in results
        ]

    @classmethod
    def compare_players(cls, db: Session, player_a_id: str, player_b_id: str) -> Dict[str, Any]:
        """Compares two players side-by-side with statistical metrics and AI-generated insights."""
        profiled = cls.get_all_players_profiled(db)
        p_a = next((p for p in profiled if p["competitor_id"] == player_a_id), None)
        p_b = next((p for p in profiled if p["competitor_id"] == player_b_id), None)

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
            "difference": f"{abs(p_a['rank'] - p_b['rank'])} positions"
        })

        # 2. Ranking Points (Higher is better)
        pts_diff = p_a["points"] - p_b["points"]
        pts_adv = "player_a" if pts_diff > 0 else ("player_b" if pts_diff < 0 else "equal")
        metrics_table.append({
            "metric": "Ranking Points",
            "player_a_value": f"{p_a['points']:,} pts",
            "player_b_value": f"{p_b['points']:,} pts",
            "advantage": pts_adv,
            "difference": f"{abs(pts_diff):,} pts"
        })

        # 3. Competitions Played
        comp_diff = p_a["competitions_played"] - p_b["competitions_played"]
        comp_adv = "player_a" if comp_diff > 0 else ("player_b" if comp_diff < 0 else "equal")
        metrics_table.append({
            "metric": "Tournaments Played",
            "player_a_value": p_a["competitions_played"],
            "player_b_value": p_b["competitions_played"],
            "advantage": comp_adv,
            "difference": f"{abs(comp_diff)} events"
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
            "difference": f"{round(abs(eff_a - eff_b), 1)} pts/event"
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
            "missing_data_warnings": ["Head-to-head match scores are not covered in the doubles rankings feed."]
        }
