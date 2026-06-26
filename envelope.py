"""
Envelope analysis for bearing fault detection.

Pipeline:
    raw signal --> bandpass around resonance --> Hilbert envelope -->
    DC removal --> FFT --> envelope spectrum
"""

from typing import Tuple
import numpy as np
from scipy.signal import butter, sosfiltfilt, hilbert

from spectrum import amplitude_spectrum


def bandpass_filter(
    x: np.ndarray,
    fs: float,
    f_low: float,
    f_high: float,
    order: int = 4,
) -> np.ndarray:
    """Zero-phase Butterworth bandpass filter.

    Parameters
    ----------
    x : np.ndarray
        Input signal, 1-D.
    fs : float
        Sampling frequency, Hz.
    f_low, f_high : float
        Passband edges, Hz. Must satisfy 0 < f_low < f_high < fs/2.
    order : int
        Filter order per direction. Default 4 -> effective 8th order after
        forward-backward filtering.

    Returns
    -------
    np.ndarray
        Filtered signal, same length as input. Zero phase distortion.
    """
    nyquist = fs / 2.0
    # Clamp edges that land exactly on DC or Nyquist (common with dyadic
    # kurtogram bands where the top sub-band ends at exactly fs/2)
    f_low = max(f_low, 1.0)            # at least 1 Hz above DC
    f_high = min(f_high, nyquist * 0.999)  # just below Nyquist
    if not (0 < f_low < f_high < nyquist):
        raise ValueError(
            f"Invalid band: need 0 < {f_low} < {f_high} < {nyquist}"
        )
    sos = butter(order, [f_low / nyquist, f_high / nyquist],
                 btype="bandpass", output="sos")
    return sosfiltfilt(sos, x)


def envelope(x: np.ndarray) -> np.ndarray:
    """Extract the amplitude envelope via Hilbert transform.

    Parameters
    ----------
    x : np.ndarray
        Input signal, ideally bandpassed around the structural resonance.

    Returns
    -------
    np.ndarray
        Envelope |z(t)|. Real, non-negative.
    """
    return np.abs(hilbert(x))


def envelope_spectrum(
    x: np.ndarray,
    fs: float,
    f_low: float,
    f_high: float,
    filter_order: int = 4,
) -> Tuple[np.ndarray, np.ndarray]:
    """Full envelope-spectrum pipeline: bandpass -> envelope -> demean -> FFT.

    Parameters
    ----------
    x : np.ndarray
        Raw vibration signal.
    fs : float
        Sampling frequency, Hz.
    f_low, f_high : float
        Bandpass edges defining the demodulation band, Hz.
    filter_order : int
        Butterworth order per direction.

    Returns
    -------
    f_env : np.ndarray
        Frequency axis of the envelope spectrum, Hz.
    A_env : np.ndarray
        Amplitude spectrum of the envelope.
    """
    x_bp = bandpass_filter(x, fs, f_low, f_high, order=filter_order)
    env = envelope(x_bp)
    env_demeaned = env - env.mean()
    return amplitude_spectrum(env_demeaned, fs)
