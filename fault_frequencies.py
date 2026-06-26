"""
Bearing fault frequency calculations from bearing geometry and shaft speed.

All formulas assume:
  - Inner race rotates with the shaft, outer race fixed (CWRU configuration).
  - Pure rolling at both contact points (no slip).
  - Single-row ball or roller bearing.

References:
  Randall & Antoni (2011), McFadden & Smith (1984).
"""

from dataclasses import dataclass
from typing import Dict
import numpy as np


@dataclass
class FaultFrequencies:
    """Bearing fault frequencies, all in Hz."""
    fr:    float  # shaft rotation frequency
    ftf:   float  # fundamental train (cage) frequency
    bpfo:  float  # ball pass frequency, outer race
    bpfi:  float  # ball pass frequency, inner race
    bsf:   float  # ball spin frequency (rotation about ball axis)

    @property
    def bsf_impact_rate(self) -> float:
        """Impact rate for a ball fault: 2 x BSF."""
        return 2.0 * self.bsf

    def as_dict(self) -> dict:
        return {
            "fr (shaft)":          self.fr,
            "FTF (cage)":          self.ftf,
            "BPFO (outer race)":   self.bpfo,
            "BPFI (inner race)":   self.bpfi,
            "BSF (ball spin)":     self.bsf,
            "2*BSF (ball impact)": self.bsf_impact_rate,
        }


def compute_fault_frequencies(bearing: Dict, rpm: float) -> FaultFrequencies:
    """Compute the four characteristic fault frequencies for a bearing.

    Parameters
    ----------
    bearing : dict
        Must contain 'n_balls', 'ball_diameter', 'pitch_diameter',
        'contact_angle' (radians).
    rpm : float
        Shaft rotational speed in revolutions per minute.

    Returns
    -------
    FaultFrequencies
    """
    n   = bearing["n_balls"]
    d   = bearing["ball_diameter"]
    D   = bearing["pitch_diameter"]
    phi = bearing["contact_angle"]
    if D <= 0 or d <= 0 or n <= 0:
        raise ValueError(f"Invalid geometry: n={n}, d={d}, D={D}")
    if d >= D:
        raise ValueError(f"Ball diameter ({d}) >= pitch diameter ({D})")

    fr = rpm / 60.0
    g  = (d / D) * np.cos(phi)

    ftf  = 0.5 * fr * (1.0 - g)
    bpfo = n * ftf
    bpfi = n * fr - bpfo
    bsf  = (D / (2.0 * d)) * fr * (1.0 - g ** 2)

    return FaultFrequencies(fr=fr, ftf=ftf, bpfo=bpfo, bpfi=bpfi, bsf=bsf)


def validate(bearing: Dict, freqs: FaultFrequencies, rpm: float, tol: float = 1e-9) -> None:
    """Assert the BPFI + BPFO = n*fr identity and sanity-check geometry."""
    n = bearing["n_balls"]
    d = bearing["ball_diameter"]
    D = bearing["pitch_diameter"]
    expected_sum = n * (rpm / 60.0)
    actual_sum = freqs.bpfi + freqs.bpfo
    assert abs(actual_sum - expected_sum) < tol, \
        f"BPFI + BPFO = {actual_sum}, expected {expected_sum}"
    assert freqs.ftf < freqs.fr / 2.0, \
        f"FTF ({freqs.ftf}) >= fr/2 ({freqs.fr/2})"
    assert 0.05 < d / D < 0.5, \
        f"d/D = {d/D:.3f} outside typical range (0.1-0.3)"
