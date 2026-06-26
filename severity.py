"""
Feature extraction for severity tracking: time-domain statistics + envelope-
spectrum-based fault frequency features in one call.

Designed for Stage 8 progression analysis and Project 3 Kalman filter.
"""

from dataclasses import dataclass, asdict
from typing import Dict
import numpy as np
from scipy.stats import kurtosis as scipy_kurtosis

from spectrum import band_amplitude, noise_floor
from envelope import envelope_spectrum
from envelope import bandpass_filter, envelope as hilbert_envelope
from fault_frequencies import compute_fault_frequencies


@dataclass
class SeverityFeatures:
    """Bundled features for one bearing record at one operating condition."""
    # Time-domain
    rms_g:          float
    peak_to_peak_g: float
    crest_factor:   float
    kurtosis:       float
    # Envelope-spectrum, fault-frequency-specific
    bpfo_peak_g:    float
    bpfo_snr_db:    float
    bpfo_drift_pct: float
    n_harmonics:    int

    def as_dict(self) -> Dict:
        return asdict(self)


def extract_features(
    signal: np.ndarray,
    fs: float,
    rpm: float,
    bearing: dict,
    fault_type: str,
    f_low: float = 2000.0,
    f_high: float = 4000.0,
    tol_pct: float = 2.0,
    n_harmonic_check: int = 5,
) -> SeverityFeatures:
    """Extract the full severity feature set for one record.

    Parameters
    ----------
    signal : np.ndarray — raw acceleration signal.
    fs : float — sampling frequency, Hz.
    rpm : float — shaft speed, rpm.
    bearing : dict — bearing geometry (BEARING_DE from config).
    fault_type : str — 'inner', 'outer', 'ball', or 'none'.
    f_low, f_high : float — demodulation band, Hz.
    tol_pct : float — peak-frequency tolerance for slip.
    n_harmonic_check : int — harmonics to check.

    Returns
    -------
    SeverityFeatures
    """
    x = np.asarray(signal, dtype=np.float64)

    # Time-domain
    rms = float(np.sqrt(np.mean(x ** 2)))
    pk2pk = float(np.ptp(x))
    crest = float(np.max(np.abs(x)) / rms) if rms > 0 else 0.0
    kurt = float(scipy_kurtosis(x, fisher=False))

    # Target fault frequency
    freqs = compute_fault_frequencies(bearing, rpm)
    target = {
        "inner": freqs.bpfi,
        "outer": freqs.bpfo,
        "ball":  freqs.bsf_impact_rate,
        "none":  freqs.bpfo,
    }[fault_type]

    # Envelope spectrum — use Welch averaging for robust SNR estimation.
    # The full-length FFT (N=120k -> df=0.1 Hz) gives artificially low noise
    # floors; Welch with nperseg=4096 gives df~3 Hz with ~58 averages, producing
    # physically meaningful SNR values.
    from spectrum import welch_amplitude_spectrum
    x_bp = bandpass_filter(x, fs, f_low, f_high)
    env = hilbert_envelope(x_bp)
    env_demeaned = env - env.mean()
    f_env, A_env = welch_amplitude_spectrum(env_demeaned, fs, nperseg=4096)
    peak, peak_f = band_amplitude(f_env, A_env, target, tol_pct=tol_pct)
    floor = noise_floor(f_env, A_env, target, exclude_pct=5.0, window_pct=25.0)
    snr_db = 20 * np.log10(peak / floor) if (floor > 0 and peak > 0) else 0.0
    drift = 100.0 * (peak_f - target) / target if target > 0 else 0.0

    # Harmonic count
    n_harm = 0
    for h in range(1, n_harmonic_check + 1):
        f_h = h * target
        if f_h > f_env.max():
            break
        peak_h, _ = band_amplitude(f_env, A_env, f_h, tol_pct=tol_pct)
        floor_h = noise_floor(f_env, A_env, f_h, exclude_pct=5.0, window_pct=25.0)
        if floor_h > 0 and peak_h > 2.0 * floor_h:
            n_harm += 1

    return SeverityFeatures(
        rms_g=rms,
        peak_to_peak_g=pk2pk,
        crest_factor=crest,
        kurtosis=kurt,
        bpfo_peak_g=peak,
        bpfo_snr_db=snr_db,
        bpfo_drift_pct=drift,
        n_harmonics=n_harm,
    )
