"""
Module 3: End-to-End ETL Pipeline
Orchestrates:
1. Extraction (SportRadar API / Offline Mock Fallback)
2. Transformation & Relational Normalization (Pandas)
3. Quality Auditing & Anomaly Detection (Pydantic / QualityMonitor)
4. Staging Output Generation (CSV/Parquet ready for PostgreSQL ingestion)
"""
import os
import sys
import logging
from typing import Dict, Any, Tuple
import pandas as pd

# Path setups for sibling imports
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURR_DIR, "..", ".."))
sys.path.append(os.path.join(CURR_DIR, "..", "extraction"))
sys.path.append(os.path.join(CURR_DIR, "..", "transformation"))
sys.path.append(os.path.join(CURR_DIR, "..", "validation"))

from sportradar_client import SportRadarClient
from transformer import DataTransformer
from quality_monitor import DataQualityMonitor

logger = logging.getLogger("ETLPipeline")


class ETLPipeline:
    def __init__(self, output_dir: str = None):
        self.client = SportRadarClient()
        self.transformer = DataTransformer()
        self.monitor = DataQualityMonitor()
        self.output_dir = output_dir or os.path.join(CURR_DIR, "processed")
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self) -> Dict[str, pd.DataFrame]:
        logger.info("================ STARTING ETL PIPELINE ================")

        # 1. EXTRACT
        logger.info("[ETL 1/4] Extracting data from SportRadar endpoints...")
        raw_competitions = self.client.get_competitions()
        raw_complexes = self.client.get_complexes()
        raw_rankings = self.client.get_doubles_rankings()

        # 2. TRANSFORM
        logger.info("[ETL 2/4] Transforming and normalizing relational data...")
        df_categories, df_competitions = self.transformer.transform_competitions_data(raw_competitions)
        df_complexes, df_venues = self.transformer.transform_complexes_data(raw_complexes)
        df_competitors, df_rankings = self.transformer.transform_rankings_data(raw_rankings)

        tables: Dict[str, Tuple[pd.DataFrame, str]] = {
            "categories": (df_categories, "category_id"),
            "competitions": (df_competitions, "competition_id"),
            "complexes": (df_complexes, "complex_id"),
            "venues": (df_venues, "venue_id"),
            "competitors": (df_competitors, "competitor_id"),
            "competitor_rankings": (df_rankings, "rank_id")
        }

        # 3. VALIDATE & AUDIT
        logger.info("[ETL 3/4] Running automated data quality checks...")
        audit_report = self.monitor.generate_full_report(tables)
        logger.info(f"Audit Complete. Overall Status: {audit_report['overall_status']}")

        # 4. LOAD / STAGE TO PROCESSED CSVs
        logger.info(f"[ETL 4/4] Staging processed tables into: {self.output_dir}")
        for name, (df, _) in tables.items():
            csv_path = os.path.join(self.output_dir, f"{name}.csv")
            df.to_csv(csv_path, index=False, encoding="utf-8")
            logger.info(f" -> Exported {name}.csv ({len(df)} rows)")

        logger.info("================ ETL PIPELINE COMPLETED SUCCESSFULLY ================")
        return {k: v[0] for k, v in tables.items()}


if __name__ == "__main__":
    pipeline = ETLPipeline()
    results = pipeline.run()
    for name, df in results.items():
        print(f"\n--- {name.upper()} SAMPLE ({len(df)} rows) ---")
        print(df.head(3))
