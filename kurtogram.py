"""
Fast kurtogram for automatic demodulation-band selection.

Reference:
  Antoni, J. (2007) "Fast computation of the kurtogram for the detection of
  transient faults." MSSP 21(1): 108-124.
"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
from scipy.signal import butter, sosfiltfilt, hilbert
from scipy.stats import kurtosis as scipy_kurtosis


@dataclass
class KurtogramResult:
    """Output of the kurtogram computation."""
    levels:        List[int]
    bandwidths:    List[float]
    kurtosis_grid: List[np.ndarray]
    centres_grid:  List[np.ndarray]
    fs:            float

    def optimal_band(self) -> Tuple[float, float, float]:
        """Return (f_low, f_high, kurtosis_value) of the maximum-kurtosis band."""
        best_k = -np.inf
        best_band = (0.0, 0.0, -np.inf)
        for level, bw, kurts, centres in zip(
            self.levels, self.bandwidths, self.kurtosis_grid, self.centres_grid
        ):
            i_max = int(np.argmax(kurts))
            k_max = float(kurts[i_max])
            if k_max > best_k:
                best_k = k_max
                fc = float(centres[i_max])
                best_band = (fc - bw / 2, fc + bw / 2, k_max)
        return best_band


def _envelope_kurtosis(x: np.ndarray) -> float:
    """Kurtosis of the Hilbert envelope. Pearson convention (Gaussian = 3)."""
    env = np.abs(hilbert(x))
    return float(scipy_kurtosis(env - env.mean(), fisher=False))


def _bandpass(x: np.ndarray, fs: float, f_low: float, f_high: float,
              order: int = 4) -> np.ndarray:
    """Zero-phase Butterworth bandpass."""
    nyq = fs / 2.0
    f_low = max(f_low, 1e-3 * nyq)
    f_high = min(f_high, 0.999 * nyq)
    if f_low >= f_high:
        return np.zeros_like(x)
    sos = butter(order, [f_low / nyq, f_high / nyq],
                 btype="bandpass", output="sos")
    return sosfiltfilt(sos, x)


def compute_kurtogram(
    x: np.ndarray,
    fs: float,
    max_level: int = 6,
    min_level: int = 1,
    f_max: float = None,
    f_min: float = None,
) -> KurtogramResult:
    """Compute the dyadic kurtogram of a signal.

    Parameters
    ----------
    x : np.ndarray
        Input signal, 1-D.
    fs : float
        Sampling frequency, Hz.
    max_level : int
        Deepest level. Bandwidth at level k is fs/(2^(k+1)).
    min_level : int
        Shallowest level.
    f_max : float, optional
        Maximum centre frequency to search (Hz). Default 0.8 * fs/2.
        Prevents selection of near-Nyquist bands dominated by anti-aliasing
        filter artifacts and quantisation noise.
    f_min : float, optional
        Minimum centre frequency to search (Hz). Default 500 Hz.
        The demodulation band must be ABOVE the fault frequency region
        (BPFO/BPFI/BSF live at 50-300 Hz). Demodulating at the fault
        frequency itself is physically meaningless — you need to demodulate
        the structural RESONANCE band (typically 1-5 kHz) to extract the
        fault-frequency modulation. This parameter prevents the kurtogram
        from selecting low-frequency bands where the fault signal is
        directly impulsive (high kurtosis) but not useful for demodulation.

    Returns
    -------
    KurtogramResult
    """
    x = np.asarray(x, dtype=np.float64)
    nyq = fs / 2.0
    if f_max is None:
        f_max = 0.8 * nyq
    if f_min is None:
        f_min = 500.0  # above the fault frequency region  # default: ignore top 20% near Nyquist
    levels = list(range(min_level, max_level + 1))
    bandwidths = []
    kurtosis_grid = []
    centres_grid = []

    for k in levels:
        n_bands = 2 ** k
        bw = nyq / n_bands
        bandwidths.append(bw)
        centres = (np.arange(n_bands) + 0.5) * bw
        centres_grid.append(centres)

        kurts = np.empty(n_bands)
        for i, fc in enumerate(centres):
            if fc < f_min or fc > f_max:
                kurts[i] = 3.0  # Gaussian baseline — skip this band
            else:
                x_bp = _bandpass(x, fs, fc - bw / 2, fc + bw / 2)
                kurts[i] = _envelope_kurtosis(x_bp)
        kurtosis_grid.append(kurts)

    return KurtogramResult(
        levels=levels,
        bandwidths=bandwidths,
        kurtosis_grid=kurtosis_grid,
        centres_grid=centres_grid,
        fs=fs,
    )


def kurtogram_to_image(result: KurtogramResult,
                       n_freq_bins: int = 256) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Render the kurtogram as a 2-D image suitable for imshow.

    Returns
    -------
    image : np.ndarray, shape (n_levels, n_freq_bins).
    f_axis : np.ndarray, length n_freq_bins.
    bw_axis : np.ndarray, length n_levels.
    """
    nyq = result.fs / 2.0
    f_axis = np.linspace(0, nyq, n_freq_bins)
    image = np.zeros((len(result.levels), n_freq_bins))
    for row, (bw, kurts, centres) in enumerate(zip(
        result.bandwidths, result.kurtosis_grid, result.centres_grid
    )):
        for fc, k in zip(centres, kurts):
            f_lo, f_hi = fc - bw / 2, fc + bw / 2
            mask = (f_axis >= f_lo) & (f_axis < f_hi)
            image[row, mask] = k
    bw_axis = np.array(result.bandwidths)
    return image, f_axis, bw_axis
