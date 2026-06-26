"""
Spectrograms (STFT) and scalograms (CWT) for vibration signals.

Both return a uniform (time_axis, freq_axis, magnitude_2d) interface.
"""

from typing import Tuple
import numpy as np
from scipy.signal import stft as scipy_stft
import pywt


def stft_spectrogram(
    x: np.ndarray,
    fs: float,
    nperseg: int = 256,
    noverlap_frac: float = 0.75,
    window: str = "hann",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute the STFT magnitude spectrogram.

    Parameters
    ----------
    x : np.ndarray
        Real signal, 1-D.
    fs : float
        Sampling frequency, Hz.
    nperseg : int
        Window length in samples.
    noverlap_frac : float
        Fractional overlap between adjacent windows.
    window : str
        scipy window name.

    Returns
    -------
    t : np.ndarray  — time axis (seconds)
    f : np.ndarray  — frequency axis (Hz)
    Z : np.ndarray  — magnitude spectrogram, shape (len(f), len(t))
    """
    noverlap = int(nperseg * noverlap_frac)
    f, t, Zxx = scipy_stft(
        x, fs=fs, window=window, nperseg=nperseg, noverlap=noverlap,
        return_onesided=True, scaling="spectrum",
    )
    return t, f, np.abs(Zxx)


def cwt_scalogram(
    x: np.ndarray,
    fs: float,
    f_min: float = 50.0,
    f_max: float = 5000.0,
    n_scales: int = 100,
    wavelet: str = "cmor1.5-1.0",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute a CWT scalogram with logarithmic frequency spacing.

    Parameters
    ----------
    x : np.ndarray
        Real signal, 1-D.
    fs : float
        Sampling frequency, Hz.
    f_min, f_max : float
        Frequency range to analyse (Hz). Logarithmically spaced.
    n_scales : int
        Number of logarithmically-spaced frequency points.
    wavelet : str
        PyWavelets wavelet name. 'cmor1.5-1.0' is complex Morlet.

    Returns
    -------
    t : np.ndarray  — time axis (seconds)
    f : np.ndarray  — frequency axis (Hz, decreasing)
    Z : np.ndarray  — |CWT coefficients|, shape (n_scales, len(x))
    """
    centre_freq = pywt.central_frequency(wavelet)
    freqs = np.geomspace(f_max, f_min, n_scales)
    scales = centre_freq * fs / freqs

    coefs, _ = pywt.cwt(x, scales, wavelet, sampling_period=1.0 / fs)

    t = np.arange(len(x)) / fs
    return t, freqs, np.abs(coefs)
