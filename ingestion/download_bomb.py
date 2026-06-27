"""
download_bomb.py
----------------
Loads the BOMB (Berkeley Open MOS dataBase) HDF5 dataset using the
SimData API described in UCB/EECS-2021-192.

Dataset source:
  Paper:  https://www2.eecs.berkeley.edu/Pubs/TechRpts/2021/EECS-2021-192.html
  PDF:    https://www2.eecs.berkeley.edu/Pubs/TechRpts/2021/Archive/EECS-2021-192.pdf

Place your downloaded .hdf5 files in: data/raw/
"""

import os
import h5py
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.getenv("BOMB_DATA_DIR", "./data/raw")
HDF5_FILE = os.getenv("BOMB_HDF5_FILE", "Technology_A_data.hdf5")


class SimData:
    """
    Python API class for the BOMB dataset.
    Mirrors the SimData class described in Section 2.1 of EECS-2021-192.

    Attributes:
        data (dict): Multi-dimensional numpy arrays keyed by parameter name.
                     Keys: 'ibias', 'y11', 'y12', 'y21', 'y22', 'y31', 'y32', 'y33'
                     Shape per array: [montecarlo, temperature, process, device, Vbs, Vgs, Vds]
        sweep_params (list): Dimension labels for each axis.
        reshaped_data (np.ndarray or None): Populated on demand.
    """

    PARAMETERS = ["ibias", "y11", "y12", "y13", "y21", "y22", "y23", "y31", "y32", "y33"]
    SWEEP_PARAMS = ["montecarlo", "process", "temp", "vbs", "vgs", "vds"]

    def __init__(self):
        self.data = {}
        self.sweep_params = self.SWEEP_PARAMS
        self.reshaped_data = None
        self.filepath = None

    @classmethod
    def load(cls, filepath: str) -> "SimData":
        """Load a BOMB HDF5 file and return a SimData object."""
        logger.info(f"Loading BOMB dataset from: {filepath}")
        sim = cls()
        sim.filepath = filepath

        with h5py.File(filepath, "r") as f:
            logger.info(f"HDF5 keys found: {list(f.keys())}")
            for key in f.keys():
                sim.data[key] = np.array(f[key])
                logger.info(f"  Loaded '{key}' — shape: {sim.data[key].shape}")

        logger.info(f"✅ Dataset loaded. {len(sim.data)} parameter arrays.")
        return sim

    def get_ibias(self) -> np.ndarray:
        """Return the ibias array. Shape: [mc, temp, process, device, Vbs, Vgs, Vds]"""
        return self.data.get("ibias")

    def summary(self):
        """Print a summary of the loaded dataset."""
        print(f"\n{'='*50}")
        print(f"BOMB Dataset Summary")
        print(f"Source: {self.filepath}")
        print(f"{'='*50}")
        for param, arr in self.data.items():
            print(f"  {param:>6}: shape={arr.shape}, dtype={arr.dtype}")
        total_points = sum(arr.size for arr in self.data.values())
        print(f"\n  Total data points: {total_points:,}")
        print(f"{'='*50}\n")


def validate_hdf5_file(filepath: str) -> bool:
    """Check that the file exists and is a valid HDF5 file."""
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        logger.error("Please download the BOMB dataset HDF5 files and place them in data/raw/")
        logger.error("Reference: https://www2.eecs.berkeley.edu/Pubs/TechRpts/2021/EECS-2021-192.html")
        return False
    try:
        with h5py.File(filepath, "r"):
            pass
        return True
    except Exception as e:
        logger.error(f"Invalid HDF5 file: {e}")
        return False


if __name__ == "__main__":
    filepath = os.path.join(DATA_DIR, HDF5_FILE)

    if not validate_hdf5_file(filepath):
        exit(1)

    bomb = SimData.load(filepath)
    bomb.summary()

    # Quick sanity check on ibias shape
    ibias = bomb.get_ibias()
    if ibias is not None:
        logger.info(f"ibias shape: {ibias.shape}")
        logger.info(f"ibias sample value (first element): {ibias.flat[0]:.6e}")
