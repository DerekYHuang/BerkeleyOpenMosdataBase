"""
generate_synthetic_bomb_data.py
--------------------------------
Generates synthetic HDF5 data files that exactly match the BOMB dataset schema
described in UCB/EECS-2021-192 (Berkeley Open MOS dataBase).

This script is used when the actual BOMB HDF5 files are not yet available.
The generated data has the same:
  - Array keys:   ibias, y11-y33
  - Dimensions:   [montecarlo, temperature, process, device, Vbs, Vgs, Vds]
  - Sweep ranges: matching the paper's descriptions
  - Value ranges: realistic I-V / Y-parameter magnitudes

Reference:
  Paper:  https://www2.eecs.berkeley.edu/Pubs/TechRpts/2021/EECS-2021-192.html
  PDF:    https://www2.eecs.berkeley.edu/Pubs/TechRpts/2021/Archive/EECS-2021-192.pdf
  See:    Section 2 (data structure) and Section 3 (generation framework)

Usage:
  python scripts/generate_synthetic_bomb_data.py
  # Output → data/raw/Technology_A_data.hdf5  (and Technology_B_data.hdf5)
"""

import os
import h5py
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

# ── Sweep dimensions (from BOMB paper, Section 2) ─────────────────────────────
# Shape: [montecarlo, temperature, process, device, Vbs, Vgs, Vds]
DIMENSIONS = {
    "Technology_A": {
        "montecarlo":  100,   # 100 MC variations (paper exact value)
        "temperature":   3,   # -20C, 27C, 120C
        "process":       3,   # ss (slow-slow), tt (typical), ff (fast-fast)
        "device":        4,   # LVT, NOM, HVT-1, HVT-2
        "Vbs":          11,   # 0 to Vdd in 11 steps
        "Vgs":          11,
        "Vds":          11,
    },
    "Technology_B": {
        "montecarlo":  100,
        "temperature":   3,
        "process":       5,   # Technology B has more process corners
        "device":        6,   # Technology B has more device flavors
        "Vbs":          11,
        "Vgs":          11,
        "Vds":          11,
    },
}

# Parameter names from paper Section 2
PARAMETERS = ["ibias", "y11", "y12", "y13", "y21", "y22", "y23", "y31", "y32", "y33"]

# Realistic value ranges for each parameter (CMOS transistor physics)
# ibias: drain current (A) — typically nA to mA range
# y-parameters: admittance parameters (S) — typically pS to nS range
VALUE_RANGES = {
    "ibias": (1e-9,  1e-3),    # 1nA to 1mA
    "y11":   (1e-15, 1e-9),    # fS to nS (input admittance)
    "y12":   (1e-16, 1e-10),   # reverse transfer admittance (smaller)
    "y13":   (1e-16, 1e-10),
    "y21":   (1e-4,  1e-1),    # forward transconductance (mS to 100mS)
    "y22":   (1e-12, 1e-6),    # output admittance
    "y23":   (1e-13, 1e-7),
    "y31":   (1e-13, 1e-7),
    "y32":   (1e-13, 1e-7),
    "y33":   (1e-12, 1e-6),
}


def generate_parameter_array(shape: tuple, param: str, rng: np.random.Generator) -> np.ndarray:
    """
    Generate a realistic synthetic array for a BOMB parameter.

    Uses log-uniform distribution since electrical parameters span many
    orders of magnitude (consistent with real device characterization data).
    """
    low, high = VALUE_RANGES[param]
    log_low  = np.log10(low)
    log_high = np.log10(high)

    # Base log-uniform values
    arr = 10 ** rng.uniform(log_low, log_high, size=shape)

    # Add physical correlations:
    # - ibias increases with Vgs (gate voltage → more current)
    # - Temperature affects carrier mobility (higher T → lower ibias for NMOS in saturation)
    # These are approximations to make the data physically plausible.
    if param == "ibias":
        mc, temp, proc, dev, vbs, vgs, vds = shape

        # Vgs sweep: current increases roughly quadratically with Vgs step
        vgs_factor = np.linspace(0.1, 1.0, vgs) ** 2
        arr *= vgs_factor[np.newaxis, np.newaxis, np.newaxis, np.newaxis,
                          np.newaxis, :, np.newaxis]

        # Temperature: mobility degradation at high T (index 2 = 120C)
        temp_factors = np.array([1.15, 1.0, 0.75])  # -20C boosts, 120C reduces
        arr *= temp_factors[np.newaxis, :, np.newaxis, np.newaxis,
                             np.newaxis, np.newaxis, np.newaxis]

        # Add Monte Carlo variation (±20% random variation per MC run)
        mc_noise = rng.normal(1.0, 0.2, size=(mc, 1, 1, 1, 1, 1, 1))
        arr *= np.abs(mc_noise)

    return arr.astype(np.float64)


def generate_hdf5(tech_name: str, dims: dict, output_dir: str, rng: np.random.Generator):
    """Generate a single BOMB-format HDF5 file for one technology node."""
    shape = (
        dims["montecarlo"],
        dims["temperature"],
        dims["process"],
        dims["device"],
        dims["Vbs"],
        dims["Vgs"],
        dims["Vds"],
    )

    total_points = np.prod(shape)
    logger.info(f"\n{'='*55}")
    logger.info(f"Generating {tech_name}")
    logger.info(f"  Shape: {shape}")
    logger.info(f"  Total data points per parameter: {total_points:,}")
    logger.info(f"  Parameters: {len(PARAMETERS)}")
    logger.info(f"  Total array elements: {total_points * len(PARAMETERS):,}")

    filename = os.path.join(output_dir, f"{tech_name}_data.hdf5")

    with h5py.File(filename, "w") as f:
        # Store sweep metadata as attributes (mirrors BOMB paper structure)
        f.attrs["technology"] = tech_name
        f.attrs["source"]     = "synthetic — generated from BOMB paper schema (EECS-2021-192)"
        f.attrs["paper_url"]  = "https://www2.eecs.berkeley.edu/Pubs/TechRpts/2021/EECS-2021-192.html"
        f.attrs["dimensions"] = str(shape)
        f.attrs["dim_labels"] = "[montecarlo, temperature, process, device, Vbs, Vgs, Vds]"

        # Temperature values (from paper)
        f.attrs["temperature_values_C"] = [-20, 27, 120]

        for param in PARAMETERS:
            logger.info(f"  Generating {param}...")
            arr = generate_parameter_array(shape, param, rng)
            ds = f.create_dataset(
                param,
                data=arr,
                compression="gzip",      # HDF5 compression (reduces file size ~60%)
                compression_opts=4,
            )
            ds.attrs["units"] = "A" if param == "ibias" else "S"
            ds.attrs["shape_description"] = "[mc, temp, process, device, Vbs, Vgs, Vds]"

    file_size_mb = os.path.getsize(filename) / 1e6
    logger.info(f"✅ Saved: {filename}  ({file_size_mb:.1f} MB)")
    return filename


def verify_hdf5(filepath: str):
    """Quick verification — load and print structure."""
    logger.info(f"\nVerifying {filepath}...")
    with h5py.File(filepath, "r") as f:
        logger.info(f"  HDF5 keys: {list(f.keys())}")
        for key in f.keys():
            arr = f[key]
            logger.info(f"    {key}: shape={arr.shape}, dtype={arr.dtype}")

        logger.info(f"  Attributes: {dict(f.attrs)}")
    logger.info("✅ Verification passed\n")


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Reproducible seed for consistent results
    rng = np.random.default_rng(seed=42)

    generated = []
    for tech_name, dims in DIMENSIONS.items():
        filepath = generate_hdf5(tech_name, dims, OUTPUT_DIR, rng)
        verify_hdf5(filepath)
        generated.append(filepath)

    logger.info("=" * 55)
    logger.info("All synthetic BOMB data files generated:")
    for f in generated:
        size_mb = os.path.getsize(f) / 1e6
        logger.info(f"  {f}  ({size_mb:.1f} MB)")
    logger.info("\nNext step:")
    logger.info("  python ingestion/download_bomb.py")
    logger.info("  python ingestion/hdf5_to_parquet.py")
