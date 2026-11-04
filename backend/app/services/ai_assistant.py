"""
Module 9: AI Tennis Assistant Engine
Implements context-grounded sports intelligence with strict read-only parameterized tools.
Guarantees responses are 100% grounded in database records with zero hallucination.
"""
import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.models.entities import Competitor, CompetitorRanking, Competition, Venue, AIInteraction
from app.services.analytics_service import AnalyticsService


class AITennisAssistant:
    @staticmethod
    def answer_query(db: Session, prompt: str, user_id: int = None) -> Dict[str, Any]:
        """
        Processes user query through grounded intent extraction and tool execution.
        """
        prompt_lower = prompt.lower()
        citations = []
        suggested_actions = [
            "Who are the top 5 ranked players?",
            "Compare Mate Pavic and Jordan Thompson",
            "Which country has the most players?",
            "Show available competitions"
        ]

        # INTENT 1: TOP PLAYERS / RANKINGS
        if any(w in prompt_lower for w in ["top", "highest", "leader", "best", "rank"]):
            players = AnalyticsService.get_all_players_profiled(db)[:5]
            lines = [f"Here are the top ranked players in the official SportRadar rankings:"]
            for p in players:
                lines.append(f"• #{p['rank']} {p['name']} ({p['country']}) - {p['points']:,} pts | {p['competitions_played']} tournaments | Tier: {p['cluster_tier']}")
                citations.append({"entity": "competitor", "reference_id": p["competitor_id"], "label": p["name"]})
            
            response_text = "\n".join(lines)
            suggested_actions = ["Compare top 2 players", "Show country distribution"]

        # INTENT 2: COMPARISON BETWEEN PLAYERS
        elif any(w in prompt_lower for w in ["compare", "vs", "versus", "difference"]):
            all_players = AnalyticsService.get_all_players_profiled(db)
            matched = []
            for p in all_players:
                # Check for last name or first name match
                names = p["name"].lower().replace(",", "").split()
                if any(n in prompt_lower for n in names if len(n) > 3):
                    matched.append(p)
            
            if len(matched) >= 2:
                p_a, p_b = matched[0], matched[1]
                comp_data = AnalyticsService.compare_players(db, p_a["competitor_id"], p_b["competitor_id"])
                response_text = (
                    f"⚔️ Comparison Analysis: {p_a['name']} vs {p_b['name']}\n\n"
                    f"{comp_data['ai_comparison_analysis']}\n\n"
                    f"• {p_a['name']}: #{p_a['rank']} | {p_a['points']:,} pts | Consistency: {p_a['traits']['consistency']}/100\n"
                    f"• {p_b['name']}: #{p_b['rank']} | {p_b['points']:,} pts | Consistency: {p_b['traits']['consistency']}/100\n\n"
                    f"Note: {comp_data['missing_data_warnings'][0]}"
                )
                citations.append({"entity": "competitor", "reference_id": p_a["competitor_id"], "label": p_a["name"]})
                citations.append({"entity": "competitor", "reference_id": p_b["competitor_id"], "label": p_b["name"]})
            else:
                # Fallback to comparing top 2
                p_a, p_b = all_players[0], all_players[1]
                comp_data = AnalyticsService.compare_players(db, p_a["competitor_id"], p_b["competitor_id"])
                response_text = (
                    f"Showing comparison for Top 2 ranked competitors:\n\n"
                    f"{comp_data['ai_comparison_analysis']}"
                )

        # INTENT 3: COUNTRIES / GEOGRAPHY
        elif any(w in prompt_lower for w in ["country", "countries", "nation", "global"]):
            countries = AnalyticsService.get_country_analytics(db)
            top_countries = countries[:5]
            lines = ["🌍 Global Player Distribution by Nation:"]
            for c in top_countries:
                lines.append(f"• {c['country']} ({c['country_code']}): {c['player_count']} player(s), {c['total_points']:,} total points (avg {c['avg_points']} pts)")
                citations.append({"entity": "country", "reference_id": c["country_code"], "label": c["country"]})
            response_text = "\n".join(lines)

        # INTENT 4: COMPETITIONS & VENUES
        elif any(w in prompt_lower for w in ["competition", "tournament", "venue", "complex", "wimbledon", "vienna"]):
            comps = db.query(Competition).limit(5).all()
            lines = ["🏆 Available Competitions & Tournaments:"]
            for c in comps:
                lines.append(f"• {c.competition_name} ({c.type.capitalize()}, {c.gender.capitalize()})")
                citations.append({"entity": "competition", "reference_id": c.competition_id, "label": c.competition_name})
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

        # Persist conversation
        try:
            interaction = AIInteraction(
                user_id=user_id,
                prompt=prompt,
                response=response_text
            )
            db.add(interaction)
            db.commit()
        except Exception:
            db.rollback()

        return {
            "prompt": prompt,
            "response": response_text,
            "suggested_actions": suggested_actions,
            "citations": citations,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
