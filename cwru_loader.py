"""
Load CWRU .mat files into a uniform (signal, fs, rpm, metadata) tuple.

The CWRU files are inconsistent in two ways:
    1. The drive-end signal variable is named X<file_num>_DE_time (e.g.
       X105_DE_time), so the variable name changes per file.
    2. Some files contain an RPM key (X<file_num>RPM); some do not, in which
       case we fall back to the nominal load->rpm mapping.

This loader hides both inconsistencies behind a clean interface.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
from scipy.io import loadmat

from config import CWRU_FILES, LOAD_TO_RPM, DATA_DIR


@dataclass
class BearingSignal:
    """A loaded vibration record with all metadata needed for downstream analysis."""
    signal: np.ndarray       # 1-D acceleration signal, units: g (per CWRU convention)
    fs: int                  # sampling frequency, Hz
    rpm: float               # shaft speed, rpm (measured if available, nominal otherwise)
    label: str               # e.g. 'IR007_0'
    fault: str               # 'none' | 'inner' | 'outer' | 'ball'
    size_in: float           # fault size, inches (0 for healthy)
    load_hp: int             # motor load, HP
    file_num: int            # CWRU file number, for traceability

    @property
    def shaft_freq_hz(self) -> float:
        return self.rpm / 60.0

    @property
    def duration_s(self) -> float:
        return len(self.signal) / self.fs


def _find_de_signal(mat: dict, file_num: int) -> np.ndarray:
    """Locate the drive-end time series. Try the standard naming first; fall
    back to scanning for any *_DE_time key."""
    standard_key = f"X{file_num:03d}_DE_time"
    if standard_key in mat:
        return np.asarray(mat[standard_key]).squeeze()
    # Some files use non-zero-padded numbering
    alt_key = f"X{file_num}_DE_time"
    if alt_key in mat:
        return np.asarray(mat[alt_key]).squeeze()
    de_keys = [k for k in mat if k.endswith("_DE_time")]
    if not de_keys:
        raise KeyError(f"No *_DE_time variable found in file {file_num}. "
                       f"Available keys: {[k for k in mat if not k.startswith('__')]}")
    if len(de_keys) > 1:
        print(f"  Warning: file {file_num} has multiple DE keys {de_keys}; using {de_keys[0]}")
    return np.asarray(mat[de_keys[0]]).squeeze()


def _find_rpm(mat: dict, file_num: int, load_hp: int) -> float:
    """Use the recorded RPM if present; otherwise fall back to the nominal value."""
    for key in (f"X{file_num:03d}RPM", f"X{file_num}RPM"):
        if key in mat:
            return float(np.asarray(mat[key]).squeeze())
    return float(LOAD_TO_RPM[load_hp])


def load(label: str, data_dir: Optional[str] = None) -> BearingSignal:
    """Load a CWRU record by label (e.g. 'IR007_0').

    Parameters
    ----------
    label : str
        Key into CWRU_FILES, e.g. 'Normal_0', 'IR007_0', 'OR021@6_3'.
    data_dir : str, optional
        Override the default data directory (config.DATA_DIR).

    Returns
    -------
    BearingSignal
        Holds the drive-end acceleration signal in g, sampling rate, shaft
        speed, and full provenance metadata.
    """
    if label not in CWRU_FILES:
        raise KeyError(f"Unknown label '{label}'. Available: {sorted(CWRU_FILES)[:5]}...")
    meta = CWRU_FILES[label]
    base = Path(data_dir or DATA_DIR)
    path = base / f"{label}_{meta['file_num']}.mat"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `python download_cwru.py --label {label}` first."
        )

    mat = loadmat(str(path))
    signal = _find_de_signal(mat, meta["file_num"])
    rpm = _find_rpm(mat, meta["file_num"], meta["load_hp"])

    return BearingSignal(
        signal=signal.astype(np.float64),
        fs=meta["fs_hz"],
        rpm=rpm,
        label=label,
        fault=meta["fault"],
        size_in=meta["size_in"],
        load_hp=meta["load_hp"],
        file_num=meta["file_num"],
    )
