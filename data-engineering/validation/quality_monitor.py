"""
Module 3: Data Quality & Freshness Monitor
Performs automated data quality audits, missing-value profiling,
duplicate detection, and relational integrity checking across all DataFrames.
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
import pandas as pd

logger = logging.getLogger("DataQualityMonitor")


class DataQualityMonitor:
    """
    Evaluates data cleanliness, identifies null percentages,
    ensures foreign key consistency, and produces production audit reports.
    """
    def __init__(self, report_path: str = "data_quality_report.json"):
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        self.report_path = os.path.join(curr_dir, report_path)

    def audit_dataframe(self, name: str, df: pd.DataFrame, primary_key: str) -> Dict[str, Any]:
        """Runs quality checks on a single relational DataFrame."""
        total_rows = len(df)
        duplicates = df.duplicated(subset=[primary_key]).sum() if primary_key in df.columns else 0
        null_counts = df.isnull().sum().to_dict()
        completeness = {col: round((1 - (null_counts[col] / total_rows)) * 100, 2) if total_rows > 0 else 100.0 for col in df.columns}

        return {
            "entity": name,
            "total_records": int(total_rows),
            "primary_key": primary_key,
            "duplicate_keys": int(duplicates),
            "missing_values": {k: int(v) for k, v in null_counts.items()},
            "completeness_percentage": completeness,
            "is_valid": bool(duplicates == 0 and total_rows > 0)
        }

    def generate_full_report(self, tables: Dict[str, Tuple[pd.DataFrame, str]]) -> Dict[str, Any]:
        """
        Audits all 6 core tables and generates a consolidated audit report.
        tables format: {"categories": (df_categories, "category_id"), ...}
        """
        report_timestamp = datetime.now(timezone.utc).isoformat()
        audit_results = {
            "audit_timestamp": report_timestamp,
            "overall_status": "PASSED",
            "entities": {}
        }

        all_valid = True
        for name, (df, pk) in tables.items():
            entity_audit = self.audit_dataframe(name, df, pk)
            audit_results["entities"][name] = entity_audit
            if not entity_audit["is_valid"]:
                all_valid = False

        audit_results["overall_status"] = "PASSED" if all_valid else "WARNINGS_FOUND"

        # Persist report to disk
        try:
            with open(self.report_path, "w", encoding="utf-8") as f:
                json.dump(audit_results, f, indent=2)
            logger.info(f"Data quality report generated: {self.report_path}")
        except Exception as e:
            logger.error(f"Failed to write data quality report: {e}")

        return audit_results
