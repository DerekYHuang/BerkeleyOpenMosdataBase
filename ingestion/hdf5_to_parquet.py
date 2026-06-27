"""
hdf5_to_parquet.py
------------------
Flattens BOMB HDF5 multi-dimensional arrays into a tabular Parquet file
suitable for loading into S3 / Redshift / DuckDB.

The BOMB dataset dimensions per array:
  [montecarlo, temperature, process, device, Vbs, Vgs, Vds]
"""

import os
import numpy as np
import pandas as pd
import logging

from download_bomb import SimData, validate_hdf5_file

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.getenv("BOMB_DATA_DIR", "./data/raw")
HDF5_FILE = os.getenv("BOMB_HDF5_FILE", "Technology_A_data.hdf5")
OUTPUT_DIR = "./data/parquet"

# Temperature labels (from BOMB paper: -20C, 27C, 120C)
TEMP_LABELS = [-20, 27, 120]


def flatten_bomb_to_dataframe(sim: SimData) -> pd.DataFrame:
    """
    Flatten all BOMB parameter arrays into a single tidy DataFrame.
    Each row represents one transistor characterization measurement.
    """
    logger.info("Flattening BOMB arrays into tabular format...")

    ibias = sim.data.get("ibias")
    if ibias is None:
        raise ValueError("ibias key not found in BOMB dataset.")

    shape = ibias.shape
    logger.info(f"ibias shape: {shape} → [mc, temp, process, device, Vbs, Vgs, Vds]")

    mc_size, temp_size, process_size, device_size, vbs_size, vgs_size, vds_size = shape

    rows = []
    for mc in range(mc_size):
        for t_idx in range(temp_size):
            for proc in range(process_size):
                for dev in range(device_size):
                    for vbs in range(vbs_size):
                        for vgs in range(vgs_size):
                            for vds in range(vds_size):
                                row = {
                                    "montecarlo_idx": mc,
                                    "temperature_c": TEMP_LABELS[t_idx] if t_idx < len(TEMP_LABELS) else t_idx,
                                    "process_idx": proc,
                                    "device_idx": dev,
                                    "vbs_step": vbs,
                                    "vgs_step": vgs,
                                    "vds_step": vds,
                                }
                                # Add all parameter values
                                for param, arr in sim.data.items():
                                    try:
                                        row[param] = float(arr[mc, t_idx, proc, dev, vbs, vgs, vds])
                                    except Exception:
                                        row[param] = None
                                rows.append(row)

    df = pd.DataFrame(rows)
    logger.info(f"✅ Flattened to DataFrame: {len(df):,} rows × {len(df.columns)} columns")
    return df


def add_thermal_stability_flag(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a thermal_stress_flag column: 1 if temperature >= 120C, else 0.
    This creates the thermal stability analytical dimension for dbt.
    """
    df["thermal_stress_flag"] = (df["temperature_c"] >= 120).astype(int)
    return df


def save_to_parquet(df: pd.DataFrame, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, index=False, engine="pyarrow")
    logger.info(f"✅ Saved Parquet file: {output_path}")
    logger.info(f"   Size: {os.path.getsize(output_path) / 1e6:.1f} MB")


if __name__ == "__main__":
    filepath = os.path.join(DATA_DIR, HDF5_FILE)

    if not validate_hdf5_file(filepath):
        exit(1)

    sim = SimData.load(filepath)
    df = flatten_bomb_to_dataframe(sim)
    df = add_thermal_stability_flag(df)

    output_path = os.path.join(OUTPUT_DIR, "bomb_transistor_flat.parquet")
    save_to_parquet(df, output_path)

    print(df.head())
    print(df.dtypes)
