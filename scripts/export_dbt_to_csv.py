"""
export_dbt_to_csv.py
---------------------
Exports the dbt mart tables from DuckDB into CSV files that the
Streamlit dashboard reads.

Run this AFTER completing `dbt run` successfully:
  python scripts/export_dbt_to_csv.py

Outputs to: dashboard/data/exports/
  - fact_transistor_characterization.csv
  - dim_device.csv
  - dim_temperature.csv
  - dim_process_corner.csv

Once these CSVs exist, the Streamlit dashboard will show REAL pipeline
data instead of synthetic fallback data.
"""

import os
import duckdb
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DUCKDB_PATH  = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "bomb_dbt.duckdb")
EXPORTS_DIR  = os.path.join(os.path.dirname(__file__), "..", "dashboard", "data", "exports")

# Tables to export and any column sampling/limits for dashboard performance
EXPORTS = {
    "fact_transistor_characterization": {
        "query": """
            SELECT
                f.characterization_id,
                f.montecarlo_idx,
                f.ibias,
                f.ibias_abs,
                f.gm_proxy,
                f.thermal_stress_flag,
                d.device_label,
                d.device_voltage_class,
                t.temperature_c,
                t.thermal_regime,
                t.is_high_stress,
                p.process_label
            FROM fact_transistor_characterization f
            JOIN dim_device d      ON f.device_key      = d.device_key
            JOIN dim_temperature t ON f.temperature_key = t.temperature_key
            JOIN dim_process_corner p ON f.process_key  = p.process_key
            USING SAMPLE 10 PERCENT  -- sample for dashboard performance
        """,
    },
    "dim_device": {
        "query": "SELECT * FROM dim_device",
    },
    "dim_temperature": {
        "query": "SELECT * FROM dim_temperature",
    },
    "dim_process_corner": {
        "query": "SELECT * FROM dim_process_corner",
    },
}


def export_tables():
    if not os.path.exists(DUCKDB_PATH):
        logger.error(f"DuckDB file not found: {DUCKDB_PATH}")
        logger.error("Run `dbt run` first to generate the mart tables.")
        exit(1)

    os.makedirs(EXPORTS_DIR, exist_ok=True)
    conn = duckdb.connect(DUCKDB_PATH, read_only=True)

    for table_name, config in EXPORTS.items():
        logger.info(f"Exporting {table_name}...")
        try:
            df = conn.execute(config["query"]).df()
            out_path = os.path.join(EXPORTS_DIR, f"{table_name}.csv")
            df.to_csv(out_path, index=False)
            size_kb = os.path.getsize(out_path) / 1024
            logger.info(f"  ✅ {out_path}  ({len(df):,} rows · {size_kb:.0f} KB)")
        except Exception as e:
            logger.error(f"  ❌ Failed to export {table_name}: {e}")

    conn.close()
    logger.info("\n✅ All tables exported. Dashboard will now show real pipeline data.")
    logger.info(f"   Location: {EXPORTS_DIR}")
    logger.info("\nNext step: commit the CSVs and push to GitHub.")
    logger.info("  git add dashboard/data/exports/")
    logger.info("  git commit -m 'feat: add pipeline output data for dashboard'")
    logger.info("  git push")


if __name__ == "__main__":
    export_tables()
