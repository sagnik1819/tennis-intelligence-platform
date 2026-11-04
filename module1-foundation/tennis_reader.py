"""
Module 1: Programming Foundation - Tennis JSON Data Parser and Explorer
Demonstrates file handling, JSON deserialization, exception handling,
data validation, and formatted CLI presentation.
"""
import json
import os
import sys
from typing import List

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ensure local imports work cleanly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from player_model import Competitor, PlayerRankingProfile


class TennisDataParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.rankings: List[PlayerRankingProfile] = []

    def load_data(self) -> bool:
        """Loads JSON data with defensive exception handling."""
        if not os.path.exists(self.file_path):
            print(f"[ERROR] File not found: {self.file_path}")
            return False

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            raw_rankings = data.get("rankings", [])
            for item in raw_rankings:
                comp_data = item.get("competitor", {})
                competitor = Competitor(
                    id=comp_data.get("id", "N/A"),
                    name=comp_data.get("name", "Unknown"),
                    country=comp_data.get("country", "Unknown"),
                    country_code=comp_data.get("country_code", "UNK"),
                    abbreviation=comp_data.get("abbreviation", "UNK"),
                )

                profile = PlayerRankingProfile(
                    competitor=competitor,
                    rank=item.get("rank", 0),
                    points=item.get("points", 0),
                    movement=item.get("movement", 0),
                    competitions_played=item.get("competitions_played", 0),
                )
                self.rankings.append(profile)

            print(f"[SUCCESS] Successfully parsed {len(self.rankings)} player profiles from JSON.")
            return True

        except json.JSONDecodeError as jde:
            print(f"[ERROR] Malformed JSON: {jde}")
            return False
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred: {e}")
            return False

    def display_leaderboard(self):
        """Displays a clean CLI tennis leaderboard."""
        print("\n" + "=" * 90)
        print("          [TENNIS INTELLIGENCE PLATFORM] - MODULE 1 VERIFICATION")
        print("=" * 90)
        print(f"{'RANK':<6}{'PLAYER NAME':<28}{'COUNTRY':<18}{'POINTS':<10}{'MOVEMENT':<12}{'TOURNAMENTS':<12}")
        print("-" * 90)

        for p in self.rankings:
            country_str = f"{p.competitor.country} ({p.competitor.country_code})"
            print(
                f"{p.rank:<6}"
                f"{p.competitor.name:<28}"
                f"{country_str:<18}"
                f"{p.points:<10}"
                f"{p.movement_indicator:<12}"
                f"{p.competitions_played:<12}"
            )

        print("=" * 90)
        total_points = sum(p.points for p in self.rankings)
        avg_points = total_points / len(self.rankings) if self.rankings else 0
        print(f"Summary: Total Players: {len(self.rankings)} | Avg Points: {avg_points:.1f} | Top Seed: {self.rankings[0].competitor.name if self.rankings else 'N/A'}")
        print("=" * 90 + "\n")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_json = os.path.join(current_dir, "..", "data-engineering", "sample_data", "tennis_sample.json")
    
    parser = TennisDataParser(sample_json)
    if parser.load_data():
        parser.display_leaderboard()
