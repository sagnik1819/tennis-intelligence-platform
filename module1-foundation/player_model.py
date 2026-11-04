"""
Module 1: Programming Foundation - Object-Oriented Player Representation
Demonstrates OOP, Encapsulation, Type Annotations, and Methods.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Competitor:
    id: str
    name: str
    country: str
    country_code: str
    abbreviation: str

    def display_name(self) -> str:
        """Returns formatted competitor name with country flag/code."""
        return f"{self.name} [{self.country_code}]"


class PlayerRankingProfile:
    def __init__(self, competitor: Competitor, rank: int, points: int, movement: int, competitions_played: int):
        self.competitor = competitor
        self.rank = rank
        self.points = points
        self.movement = movement
        self.competitions_played = competitions_played

    @property
    def movement_indicator(self) -> str:
        """Returns visual ASCII-safe indicator of rank movement."""
        if self.movement > 0:
            return f"+{self.movement} (UP)"
        elif self.movement < 0:
            return f"{self.movement} (DN)"
        return " 0 (EQ)"

    def summary(self) -> str:
        """Generates a formatted summary line for this player."""
        return (
            f"Rank #{self.rank:<2} | {self.competitor.name:<26} | "
            f"Country: {self.competitor.country:<12} ({self.competitor.country_code}) | "
            f"Points: {self.points:<5} | Movement: {self.movement_indicator:<8} | "
            f"Tournaments: {self.competitions_played}"
        )
