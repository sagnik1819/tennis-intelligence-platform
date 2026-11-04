"""
Module 4 Verification Script: Execute and Test All 20 Curriculum Analytical SQL Queries
Runs every single query from the syllabus against the seeded database and verifies output.
"""
import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Path setup
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURR_DIR, ".."))
sys.path.append(os.path.join(PROJECT_ROOT, "backend", "app", "database"))
sys.path.append(CURR_DIR)

from sqlalchemy import text
from connection import engine
from seed_database import seed_database


QUERIES = [
    # Part 1: Competitions & Categories
    ("Q1: List all competitions along with their category name",
     "SELECT c.competition_name, c.type, c.gender, cat.category_name FROM competitions c JOIN categories cat ON c.category_id = cat.category_id ORDER BY cat.category_name"),

    ("Q2: Count the number of competitions in each category",
     "SELECT cat.category_name, COUNT(c.competition_id) AS competition_count FROM categories cat LEFT JOIN competitions c ON cat.category_id = c.category_id GROUP BY cat.category_name ORDER BY competition_count DESC"),

    ("Q3: Find all competitions of type 'doubles'",
     "SELECT competition_name, gender, type FROM competitions WHERE LOWER(type) = 'doubles'"),

    ("Q4: Get competitions that belong to a specific category (e.g., ITF Men)",
     "SELECT c.competition_name, c.type, cat.category_name FROM competitions c JOIN categories cat ON c.category_id = cat.category_id WHERE cat.category_name = 'ITF Men'"),

    ("Q5: Identify parent competitions and their sub-competitions",
     "SELECT p.competition_name AS parent_competition, s.competition_name AS sub_competition FROM competitions s JOIN competitions p ON s.parent_id = p.competition_id"),

    ("Q6: Analyze the distribution of competition types by category",
     "SELECT cat.category_name, c.type, COUNT(*) AS total_events FROM competitions c JOIN categories cat ON c.category_id = cat.category_id GROUP BY cat.category_name, c.type"),

    ("Q7: List all competitions with no parent (top-level competitions)",
     "SELECT competition_name, type, gender FROM competitions WHERE parent_id IS NULL"),

    # Part 2: Complexes & Venues
    ("Q8: List all venues along with their associated complex name",
     "SELECT v.venue_name, v.city_name, v.country_name, cx.complex_name FROM venues v JOIN complexes cx ON v.complex_id = cx.complex_id"),

    ("Q9: Count the number of venues in each complex",
     "SELECT cx.complex_name, COUNT(v.venue_id) AS total_venues FROM complexes cx LEFT JOIN venues v ON cx.complex_id = v.complex_id GROUP BY cx.complex_name ORDER BY total_venues DESC"),

    ("Q10: Get details of venues in a specific country (e.g., Chile)",
     "SELECT venue_name, city_name, country_name, timezone FROM venues WHERE country_name = 'Chile'"),

    ("Q11: Identify all venues and their timezones",
     "SELECT venue_name, city_name, country_name, timezone FROM venues ORDER BY timezone"),

    ("Q12: Find complexes that have more than one venue",
     "SELECT cx.complex_name, COUNT(v.venue_id) AS venue_count FROM complexes cx JOIN venues v ON cx.complex_id = v.complex_id GROUP BY cx.complex_id, cx.complex_name HAVING COUNT(v.venue_id) > 1"),

    ("Q13: List venues grouped by country",
     "SELECT country_name, COUNT(venue_id) AS total_venues FROM venues GROUP BY country_name ORDER BY total_venues DESC"),

    ("Q14: Find all venues for a specific complex (e.g., Nacional)",
     "SELECT v.venue_name, v.city_name, cx.complex_name FROM venues v JOIN complexes cx ON v.complex_id = cx.complex_id WHERE cx.complex_name LIKE '%Nacional%'"),

    # Part 3: Competitors & Rankings
    ("Q15: Get all competitors with their rank and points",
     "SELECT c.name, c.country, r.rank, r.points, r.competitions_played FROM competitor_rankings r JOIN competitors c ON r.competitor_id = c.competitor_id ORDER BY r.rank ASC"),

    ("Q16: Find competitors ranked in the top 5",
     "SELECT r.rank, c.name, c.country, r.points FROM competitor_rankings r JOIN competitors c ON r.competitor_id = c.competitor_id WHERE r.rank <= 5 ORDER BY r.rank ASC"),

    ("Q17: List competitors with no rank movement (stable rank)",
     "SELECT r.rank, c.name, c.country, r.movement FROM competitor_rankings r JOIN competitors c ON r.competitor_id = c.competitor_id WHERE r.movement = 0 ORDER BY r.rank ASC"),

    ("Q18: Get the total points of competitors from a specific country (e.g., Croatia)",
     "SELECT c.country, SUM(r.points) AS total_country_points, COUNT(c.competitor_id) AS total_players FROM competitor_rankings r JOIN competitors c ON r.competitor_id = c.competitor_id WHERE c.country = 'Croatia' GROUP BY c.country"),

    ("Q19: Count the number of competitors per country",
     "SELECT country, country_code, COUNT(competitor_id) AS player_count FROM competitors GROUP BY country, country_code ORDER BY player_count DESC"),

    ("Q20: Find competitors with the highest points in the current week",
     "SELECT c.name, c.country, r.rank, r.points FROM competitor_rankings r JOIN competitors c ON r.competitor_id = c.competitor_id WHERE r.points = (SELECT MAX(points) FROM competitor_rankings)")
]


def run_all_queries():
    print("=" * 85)
    print("      🎾 TENNIS INTELLIGENCE PLATFORM - MODULE 4: 20 SQL QUERIES EXECUTION 🎾")
    print("=" * 85)

    # Ensure database is freshly seeded
    seed_database()

    with engine.connect() as conn:
        for idx, (title, sql_str) in enumerate(QUERIES, start=1):
            result = conn.execute(text(sql_str)).fetchall()
            print(f"\n[{idx:02d}/20] {title}")
            print(f"SQL: {sql_str}")
            print(f"Result Rows: {len(result)}")
            for row in result[:3]:  # Print first 3 rows as preview
                print(f"   -> {tuple(row)}")
            if len(result) > 3:
                print(f"   -> ... (+{len(result) - 3} more rows)")
            assert len(result) > 0, f"Query {idx} returned empty result!"

    print("\n" + "=" * 85)
    print("     🎉 ALL 20 CURRICULUM ANALYTICAL SQL QUERIES EXECUTED & VERIFIED! 🎉")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    run_all_queries()
