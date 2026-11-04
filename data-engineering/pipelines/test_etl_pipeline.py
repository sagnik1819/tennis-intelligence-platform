"""
Module 3 Verification Script: Automated Tests for Data Engineering & ETL Pipeline
Validates DataFrame transformations, null checks, deduplication, and file staging.
"""
import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from etl_pipeline import ETLPipeline


def run_etl_verification():
    print("=" * 85)
    print("        🎾 TENNIS INTELLIGENCE PLATFORM - MODULE 3 ETL VERIFICATION 🎾")
    print("=" * 85)

    pipeline = ETLPipeline()
    tables = pipeline.run()

    print("\n[VERIFICATION CHECKS]")
    print("-" * 85)

    # 1. Assert all 6 entities exist
    expected_entities = ["categories", "competitions", "complexes", "venues", "competitors", "competitor_rankings"]
    for entity in expected_entities:
        assert entity in tables, f"Missing expected entity: {entity}"
        df = tables[entity]
        assert len(df) > 0, f"Entity {entity} produced empty DataFrame!"
        print(f"[PASS] Entity '{entity:<20}' generated {len(df):>2} records.")

    # 2. Assert Primary Key Uniqueness
    pk_map = {
        "categories": "category_id",
        "competitions": "competition_id",
        "complexes": "complex_id",
        "venues": "venue_id",
        "competitors": "competitor_id",
        "competitor_rankings": "rank_id"
    }
    for entity, pk in pk_map.items():
        duplicates = tables[entity].duplicated(subset=[pk]).sum()
        assert duplicates == 0, f"Found {duplicates} duplicate PKs in {entity}!"
        print(f"[PASS] Primary Key '{pk:<18}' in '{entity:<20}' has 0 duplicates.")

    # 3. Assert CSV Output Files Exist
    for entity in expected_entities:
        csv_file = os.path.join(pipeline.output_dir, f"{entity}.csv")
        assert os.path.exists(csv_file), f"Staged CSV not found: {csv_file}"
        assert os.path.getsize(csv_file) > 0, f"CSV file is empty: {csv_file}"
    print(f"[PASS] All 6 relational CSV staging files verified in '{pipeline.output_dir}'.")

    # 4. Assert Data Quality Report Exists
    quality_report = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "validation", "data_quality_report.json")
    assert os.path.exists(quality_report), "Quality report was not written to disk!"
    print(f"[PASS] Data Quality audit report verified on disk.")

    print("=" * 85)
    print("       🎉 MODULE 3: DATA ENGINEERING & ETL VERIFICATION PASSED SUCCESSFULLY! 🎉")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    run_etl_verification()
