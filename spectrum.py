"""
Amplitude-calibrated single-sided FFT for vibration signals.

Conventions:
  - Hanning window with coherent-gain correction, so a pure sinusoid of
    amplitude A in the time domain appears with amplitude A in the magnitude
    spectrum (not A/2, not A * window-factor).
  - Single-sided spectrum: frequencies 0 to fs/2, with non-DC, non-Nyquist
    bins doubled to account for the negative-frequency mirror.
  - Returns frequency axis in Hz and magnitude in the same units as input.
"""

import numpy as np
from typing import Tuple


def amplitude_spectrum(
    x: np.ndarray,
    fs: float,
    window: str = "hann",
    detrend: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute the single-sided amplitude spectrum of a real-valued signal.

    Parameters
    ----------
    x : np.ndarray
        Real-valued time-domain signal, 1-D.
    fs : float
        Sampling frequency, Hz.
    window : str
        Window function. 'hann' (default) or 'rect' (no window).
    detrend : bool
        Subtract the mean before windowing. Default True.

    Returns
    -------
    f : np.ndarray
        Frequency axis, Hz, length N//2 + 1.
    A : np.ndarray
        Amplitude spectrum, same units as x.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 1:
        raise ValueError(f"Expected 1-D signal, got shape {x.shape}")
    N = len(x)
    if detrend:
        x = x - x.mean()

    if window == "hann":
        w = np.hanning(N)
    elif window == "rect":
        w = np.ones(N)
    else:
        raise ValueError(f"Unknown window '{window}'")

    coherent_gain = w.sum() / N

    X = np.fft.rfft(x * w)
    A = np.abs(X) / N / coherent_gain

    A[1:-1] *= 2.0
    if N % 2 == 1:
        A[-1] *= 2.0

    f = np.fft.rfftfreq(N, d=1.0 / fs)
    return f, A


def welch_amplitude_spectrum(
    x: np.ndarray,
    fs: float,
    nperseg: int = 4096,
    noverlap_frac: float = 0.5,
) -> Tuple[np.ndarray, np.ndarray]:
    """Welch-averaged amplitude spectrum for robust SNR estimation.

    The raw FFT of a 120,000-sample record gives 0.1 Hz resolution — fine bins
    but wildly variable noise estimate.  Welch averaging with nperseg=4096 gives
    ~3 Hz resolution and ~58 averages, producing a smooth noise floor that yields
    physically meaningful SNR values.

    Use amplitude_spectrum() for high-resolution spectral plots.
    Use welch_amplitude_spectrum() whenever you compute SNR or noise floor.

    Parameters
    ----------
    x : np.ndarray  — real signal.
    fs : float      — sampling frequency, Hz.
    nperseg : int   — segment length (default 4096 -> df ≈ 3 Hz at 12 kHz).
    noverlap_frac : float — overlap fraction (default 0.5 = 50%).

    Returns
    -------
    f, A : frequency axis (Hz) and amplitude spectrum (same units as x).
    """
    from scipy.signal import welch as scipy_welch
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 1:
        raise ValueError(f"Expected 1-D signal, got shape {x.shape}")
    noverlap = int(nperseg * noverlap_frac)
    f, Pxx = scipy_welch(x - x.mean(), fs=fs, window="hann",
                         nperseg=nperseg, noverlap=noverlap,
                         scaling="spectrum", return_onesided=True)
    # Welch returns power spectrum (V²); convert to amplitude (V)
    A = np.sqrt(Pxx)
    return f, A


def band_amplitude(f: np.ndarray, A: np.ndarray, f_center: float,
                   tol_pct: float = 2.0) -> Tuple[float, float]:
    """Return (peak_amplitude, peak_frequency) within +/- tol_pct% of f_center."""
    f_lo = f_center * (1 - tol_pct / 100)
    f_hi = f_center * (1 + tol_pct / 100)
    mask = (f >= f_lo) & (f <= f_hi)
    if not mask.any():
        return 0.0, f_center
    A_band = A[mask]
    f_band = f[mask]
    idx = np.argmax(A_band)
    return float(A_band[idx]), float(f_band[idx])


def noise_floor(f: np.ndarray, A: np.ndarray, f_center: float,
                exclude_pct: float = 5.0, window_pct: float = 25.0) -> float:
    """Estimate the local noise floor near f_center, excluding the peak band."""
    f_lo, f_hi = f_center * (1 - window_pct/100), f_center * (1 + window_pct/100)
    f_xlo, f_xhi = f_center * (1 - exclude_pct/100), f_center * (1 + exclude_pct/100)
    mask = ((f >= f_lo) & (f <= f_hi)) & ~((f >= f_xlo) & (f <= f_xhi))
    if not mask.any():
        return float(np.median(A))
    return float(np.median(A[mask]))
