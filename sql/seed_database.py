"""
Module 4: Automated Database Seeder
Initializes the database schema and bulk loads cleaned CSV staging datasets
from Module 3 into the database. Also seeds demo users and sync history.
"""
import os
import sys
import hashlib
import pandas as pd
from sqlalchemy.orm import Session

# Setup project import paths
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURR_DIR, ".."))
sys.path.append(os.path.join(PROJECT_ROOT, "backend", "app", "database"))
sys.path.append(os.path.join(PROJECT_ROOT, "backend", "app", "models"))

from connection import engine, SessionLocal, Base
from entities import Category, Competition, Complex, Venue, Competitor, CompetitorRanking, User, SyncLog


def hash_password(password: str) -> str:
    """Simple SHA256 password hash for standard seed verification."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def seed_database():
    print("=" * 85)
    print("      🎾 TENNIS INTELLIGENCE PLATFORM - MODULE 4 DATABASE INITIALIZATION 🎾")
    print("=" * 85)

    # 1. Create tables
    print("\n[1/3] Generating database schema & creating tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("[SUCCESS] All tables created successfully.")

    db: Session = SessionLocal()
    processed_dir = os.path.join(PROJECT_ROOT, "data-engineering", "pipelines", "processed")

    try:
        # 2. Ingest Categories
        print("\n[2/3] Ingesting relational datasets from staged CSVs...")
        df_cats = pd.read_csv(os.path.join(processed_dir, "categories.csv"))
        for _, row in df_cats.iterrows():
            db.merge(Category(category_id=row["category_id"], category_name=row["category_name"]))
        db.commit()
        print(f" -> Ingested {len(df_cats)} categories.")

        # Ingest Competitions
        df_comps = pd.read_csv(os.path.join(processed_dir, "competitions.csv"))
        for _, row in df_comps.iterrows():
            parent = row["parent_id"] if pd.notna(row["parent_id"]) else None
            db.merge(Competition(
                competition_id=row["competition_id"],
                competition_name=row["competition_name"],
                parent_id=parent,
                type=row["type"],
                gender=row["gender"],
                category_id=row["category_id"]
            ))
        db.commit()
        print(f" -> Ingested {len(df_comps)} competitions.")

        # Ingest Complexes
        df_complexes = pd.read_csv(os.path.join(processed_dir, "complexes.csv"))
        for _, row in df_complexes.iterrows():
            db.merge(Complex(complex_id=row["complex_id"], complex_name=row["complex_name"]))
        db.commit()
        print(f" -> Ingested {len(df_complexes)} complexes.")

        # Ingest Venues
        df_venues = pd.read_csv(os.path.join(processed_dir, "venues.csv"))
        for _, row in df_venues.iterrows():
            db.merge(Venue(
                venue_id=row["venue_id"],
                venue_name=row["venue_name"],
                city_name=row["city_name"],
                country_name=row["country_name"],
                country_code=row["country_code"],
                timezone=row["timezone"],
                complex_id=row["complex_id"]
            ))
        db.commit()
        print(f" -> Ingested {len(df_venues)} venues.")

        # Ingest Competitors
        df_comps_list = pd.read_csv(os.path.join(processed_dir, "competitors.csv"))
        for _, row in df_comps_list.iterrows():
            db.merge(Competitor(
                competitor_id=row["competitor_id"],
                name=row["name"],
                country=row["country"],
                country_code=row["country_code"],
                abbreviation=row["abbreviation"]
            ))
        db.commit()
        print(f" -> Ingested {len(df_comps_list)} competitors.")

        # Ingest Competitor Rankings
        df_rankings = pd.read_csv(os.path.join(processed_dir, "competitor_rankings.csv"))
        for _, row in df_rankings.iterrows():
            db.merge(CompetitorRanking(
                rank_id=int(row["rank_id"]),
                rank=int(row["rank"]),
                movement=int(row["movement"]),
                points=int(row["points"]),
                competitions_played=int(row["competitions_played"]),
                competitor_id=row["competitor_id"]
            ))
        db.commit()
        print(f" -> Ingested {len(df_rankings)} ranking records.")

        # 3. Seed Users & Initial Sync Log
        print("\n[3/3] Seeding demo user credentials and initial sync audit log...")
        admin_user = User(
            email="admin@tennisintel.com",
            hashed_password=hash_password("Admin@123"),
            full_name="Lead System Architect",
            role="admin"
        )
        demo_user = User(
            email="analyst@tennisintel.com",
            hashed_password=hash_password("Analyst@123"),
            full_name="Sports Performance Analyst",
            role="user"
        )
        db.add(admin_user)
        db.add(demo_user)

        initial_sync = SyncLog(
            status="SUCCESS",
            data_mode="FIXTURE_STAGED",
            records_processed=len(df_cats) + len(df_comps) + len(df_complexes) + len(df_venues) + len(df_comps_list) + len(df_rankings),
            duration_seconds=0.45
        )
        db.add(initial_sync)
        db.commit()
        print("[SUCCESS] Users (admin@tennisintel.com, analyst@tennisintel.com) and initial sync log seeded.")

        print("=" * 85)
        print("          DATABASE SEEDING COMPLETED WITH ZERO ERRORS!")
        print("=" * 85)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Database seeding failed: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
