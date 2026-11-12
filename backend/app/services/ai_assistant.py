"""
Module 9: AI Tennis Assistant Engine
Implements context-grounded sports intelligence with strict read-only parameterized tools.
Reads from the L1/L2 cache layer and logs telemetry asynchronously in the background.
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.core.cache import cache_service
from app.core.config import settings
from app.database.connection import get_db_context
from app.models.entities import Competition, AIInteraction
from app.services.analytics_service import AnalyticsService


def persist_ai_interaction(user_id: Optional[int], prompt: str, response_text: str) -> None:
    """Persists chat telemetry out-of-band using an independent DB session."""
    with get_db_context() as local_db:
        try:
            interaction = AIInteraction(
                user_id=user_id,
                prompt=prompt,
                response=response_text,
            )
            local_db.add(interaction)
            local_db.commit()
        except Exception:
            local_db.rollback()


def _get_cached_competitions_summary(db: Optional[Session] = None):
    def _load():
        def _query(session: Session):
            comps = session.query(Competition).options(joinedload(Competition.category)).all()
            return [
                {
                    "competition_id": c.competition_id,
                    "competition_name": c.competition_name,
                    "type": c.type,
                    "gender": c.gender,
                }
                for c in comps
            ]
        if db is not None:
            return _query(db)
        with get_db_context() as local_db:
            return _query(local_db)

    return cache_service.get_or_compute(
        "assistant:competitions_summary:v1",
        settings.CACHE_TTL_CATALOG,
        _load,
        should_cache=bool,
    )


class AITennisAssistant:
    @staticmethod
    def answer_query(
        db: Optional[Session],
        prompt: str,
        user_id: Optional[int] = None,
        background_tasks: Any = None,
    ) -> Dict[str, Any]:
        """
        Processes user query through grounded intent extraction and cached read-only lookups.
        """
        prompt_lower = prompt.lower()
        citations = []
        suggested_actions = [
            "Who are the top 5 ranked players?",
            "Compare Mate Pavic and Jordan Thompson",
            "Which country has the most players?",
            "Show available competitions",
        ]

        # INTENT 1: TOP PLAYERS / RANKINGS
        if any(w in prompt_lower for w in ["top", "highest", "leader", "best", "rank"]):
            players = AnalyticsService.get_all_players_profiled(db)[:5]
            lines = ["Here are the top ranked players in the official SportRadar rankings:"]
            for p in players:
                lines.append(
                    f"• #{p['rank']} {p['name']} ({p['country']}) - {p['points']:,} pts | "
                    f"{p['competitions_played']} tournaments | Tier: {p['cluster_tier']}"
                )
                citations.append({"entity": "competitor", "reference_id": p["competitor_id"], "label": p["name"]})

            response_text = "\n".join(lines)
            suggested_actions = ["Compare top 2 players", "Show country distribution"]

        # INTENT 2: COMPARISON BETWEEN PLAYERS
        elif any(w in prompt_lower for w in ["compare", "vs", "versus", "difference"]):
            bundle = AnalyticsService.get_players_bundle(db)
            all_players = bundle["items"]
            matched = []
            for p in all_players:
                names = p["name"].lower().replace(",", "").split()
                if any(n in prompt_lower for n in names if len(n) > 3):
                    matched.append(p)

            if len(matched) >= 2:
                p_a, p_b = matched[0], matched[1]
                comp_data = AnalyticsService.compare_players_from_bundle(bundle, p_a["competitor_id"], p_b["competitor_id"])
                response_text = (
                    f"⚔️ Comparison Analysis: {p_a['name']} vs {p_b['name']}\n\n"
                    f"{comp_data['ai_comparison_analysis']}\n\n"
                    f"• {p_a['name']}: #{p_a['rank']} | {p_a['points']:,} pts | Consistency: {p_a['traits']['consistency']}/100\n"
                    f"• {p_b['name']}: #{p_b['rank']} | {p_b['points']:,} pts | Consistency: {p_b['traits']['consistency']}/100\n\n"
                    f"Note: {comp_data['missing_data_warnings'][0]}"
                )
                citations.append({"entity": "competitor", "reference_id": p_a["competitor_id"], "label": p_a["name"]})
                citations.append({"entity": "competitor", "reference_id": p_b["competitor_id"], "label": p_b["name"]})
            elif len(all_players) >= 2:
                p_a, p_b = all_players[0], all_players[1]
                comp_data = AnalyticsService.compare_players_from_bundle(bundle, p_a["competitor_id"], p_b["competitor_id"])
                response_text = (
                    f"Showing comparison for Top 2 ranked competitors:\n\n"
                    f"{comp_data['ai_comparison_analysis']}"
                )
            else:
                response_text = "Not enough player records available to perform comparison."

        # INTENT 3: COUNTRIES / GEOGRAPHY
        elif any(w in prompt_lower for w in ["country", "countries", "nation", "global"]):
            countries = AnalyticsService.get_country_analytics(db)
            top_countries = countries[:5]
            lines = ["🌍 Global Player Distribution by Nation:"]
            for c in top_countries:
                lines.append(
                    f"• {c['country']} ({c['country_code']}): {c['player_count']} player(s), "
                    f"{c['total_points']:,} total points (avg {c['avg_points']} pts)"
                )
                citations.append({"entity": "country", "reference_id": c["country_code"], "label": c["country"]})
            response_text = "\n".join(lines)

        # INTENT 4: COMPETITIONS & VENUES
        elif any(w in prompt_lower for w in ["competition", "tournament", "venue", "complex", "wimbledon", "vienna"]):
            comps = _get_cached_competitions_summary(db)[:5]
            lines = ["🏆 Available Competitions & Tournaments:"]
            for c in comps:
                lines.append(f"• {c['competition_name']} ({c['type'].capitalize()}, {c['gender'].capitalize()})")
                citations.append({"entity": "competition", "reference_id": c["competition_id"], "label": c["competition_name"]})
            response_text = "\n".join(lines)

        # DEFAULT INTENT: GENERAL SUMMARY
        else:
            kpis = AnalyticsService.get_platform_kpis(db)
            response_text = (
                f"🎾 Tennis Intelligence Summary: Tracking {kpis['total_players']} professional competitors "
                f"across {kpis['countries_represented']} countries and {kpis['total_competitions']} tournaments. "
                f"Current highest ranked competitor holds {kpis['highest_points']:,} points. "
                f"You can ask me to compare specific players, show country rankings, or list tournament venues."
            )

        # Offload conversation persistence so response returns immediately
        if background_tasks is not None:
            background_tasks.add_task(persist_ai_interaction, user_id, prompt, response_text)
        else:
            persist_ai_interaction(user_id, prompt, response_text)

        return {
            "prompt": prompt,
            "response": response_text,
            "suggested_actions": suggested_actions,
            "citations": citations,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
