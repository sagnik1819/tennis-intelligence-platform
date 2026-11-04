"""
Module 3: Data Transformation and Cleaning Engine
Converts nested SportRadar JSON structures into normalized, relational DataFrames.
Applies deduplication, type casting, text cleaning, and missing-value normalization.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple


class DataTransformer:
    """
    Transforms raw JSON data structures into 6 relational entities matching the PostgreSQL schema:
    1. Categories
    2. Competitions
    3. Complexes
    4. Venues
    5. Competitors
    6. Competitor Rankings
    """

    @staticmethod
    def clean_text(val: Any, default: str = "") -> str:
        """Trims whitespace and handles nulls for text fields."""
        if pd.isna(val) or val is None:
            return default
        return str(val).strip()

    def transform_competitions_data(self, raw_data: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Parses categories and competitions into two normalized DataFrames.
        Resolves parent-child relationships and category foreign keys.
        """
        # 1. Categories
        raw_cats = raw_data.get("categories", [])
        cat_records = []
        for cat in raw_cats:
            cat_records.append({
                "category_id": self.clean_text(cat.get("id")),
                "category_name": self.clean_text(cat.get("name"), "Unknown Category")
            })

        df_categories = pd.DataFrame(cat_records)
        df_categories.drop_duplicates(subset=["category_id"], inplace=True)

        # 2. Competitions
        raw_comps = raw_data.get("competitions", [])
        comp_records = []
        for comp in raw_comps:
            cat_obj = comp.get("category", {})
            cat_id = self.clean_text(cat_obj.get("id")) if cat_obj else None
            
            # If the category wasn't in raw_cats, register it
            if cat_id and cat_id not in df_categories["category_id"].values:
                extra_cat = pd.DataFrame([{
                    "category_id": cat_id,
                    "category_name": self.clean_text(cat_obj.get("name"), "Other")
                }])
                df_categories = pd.concat([df_categories, extra_cat], ignore_index=True)

            parent_id = comp.get("parent_id")
            parent_id = self.clean_text(parent_id) if parent_id else None

            comp_records.append({
                "competition_id": self.clean_text(comp.get("id")),
                "competition_name": self.clean_text(comp.get("name")),
                "parent_id": parent_id,
                "type": self.clean_text(comp.get("type"), "doubles").lower(),
                "gender": self.clean_text(comp.get("gender"), "men").lower(),
                "category_id": cat_id
            })

        df_competitions = pd.DataFrame(comp_records)
        df_competitions.drop_duplicates(subset=["competition_id"], inplace=True)

        return df_categories, df_competitions

    def transform_complexes_data(self, raw_data: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Flattens nested complexes and venues into two normalized DataFrames.
        """
        raw_complexes = raw_data.get("complexes", [])
        complex_records = []
        venue_records = []

        for c in raw_complexes:
            complex_id = self.clean_text(c.get("id"))
            complex_records.append({
                "complex_id": complex_id,
                "complex_name": self.clean_text(c.get("name"), "Sports Complex")
            })

            # Nested venues
            for v in c.get("venues", []):
                country_code = self.clean_text(v.get("country_code"), "UNK")[:3].upper()
                venue_records.append({
                    "venue_id": self.clean_text(v.get("id")),
                    "venue_name": self.clean_text(v.get("name")),
                    "city_name": self.clean_text(v.get("city_name"), "Unknown City"),
                    "country_name": self.clean_text(v.get("country_name"), "Unknown Country"),
                    "country_code": country_code,
                    "timezone": self.clean_text(v.get("timezone"), "UTC"),
                    "complex_id": complex_id
                })

        df_complexes = pd.DataFrame(complex_records)
        df_complexes.drop_duplicates(subset=["complex_id"], inplace=True)

        df_venues = pd.DataFrame(venue_records)
        df_venues.drop_duplicates(subset=["venue_id"], inplace=True)

        return df_complexes, df_venues

    def transform_rankings_data(self, raw_data: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Extracts competitors and their ranking statistics into two relational DataFrames.
        """
        raw_rankings = raw_data.get("rankings", [])
        competitor_records = []
        ranking_records = []

        for idx, r in enumerate(raw_rankings, start=1):
            comp = r.get("competitor", {})
            competitor_id = self.clean_text(comp.get("id"))
            
            competitor_records.append({
                "competitor_id": competitor_id,
                "name": self.clean_text(comp.get("name")),
                "country": self.clean_text(comp.get("country"), "Unknown"),
                "country_code": self.clean_text(comp.get("country_code"), "UNK")[:3].upper(),
                "abbreviation": self.clean_text(comp.get("abbreviation"), "UNK")[:10].upper()
            })

            ranking_records.append({
                "rank_id": idx,
                "rank": int(r.get("rank", 0)),
                "movement": int(r.get("movement", 0)),
                "points": int(r.get("points", 0)),
                "competitions_played": int(r.get("competitions_played", 0)),
                "competitor_id": competitor_id
            })

        df_competitors = pd.DataFrame(competitor_records)
        df_competitors.drop_duplicates(subset=["competitor_id"], inplace=True)

        df_rankings = pd.DataFrame(ranking_records)
        df_rankings.drop_duplicates(subset=["rank_id"], inplace=True)

        return df_competitors, df_rankings
