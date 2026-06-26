"""
EMD and VMD adaptive signal decomposition for bearing fault analysis.

EMD via PyEMD: empirical, non-deterministic, mode-mixing-prone.
VMD via vmdpy: variational, deterministic, bandwidth-controlled.

Install:
    pip install EMD-signal vmdpy
"""

from typing import Tuple
import numpy as np


def decompose_emd(x: np.ndarray, max_imfs: int = 8) -> np.ndarray:
    """Empirical Mode Decomposition (basic, non-ensemble).

    Parameters
    ----------
    x : np.ndarray — real signal, 1-D.
    max_imfs : int — maximum number of IMFs to extract.

    Returns
    -------
    np.ndarray — shape (n_imfs, len(x)). Last row is the residual.
    """
    from PyEMD import EMD
    emd = EMD(max_imf=max_imfs)
    imfs = emd(x.astype(np.float64))
    return np.asarray(imfs)


def decompose_vmd(
    x: np.ndarray,
    K: int = 5,
    alpha: float = 2000.0,
    tau: float = 0.0,
    DC: bool = False,
    init: int = 1,
    tol: float = 1e-7,
) -> Tuple[np.ndarray, np.ndarray]:
    """Variational Mode Decomposition.

    Parameters
    ----------
    x : np.ndarray — real signal, 1-D.
    K : int — number of modes.
    alpha : float — bandwidth penalty. Higher = narrower modes.
    tau : float — noise-tolerance (Lagrangian step). 0 = exact reconstruction.
    DC : bool — whether to enforce a DC mode.
    init : int — centre-freq initialisation (0=zero, 1=uniform, 2=random).
    tol : float — convergence tolerance.

    Returns
    -------
    modes : np.ndarray — shape (K, N).
    centre_freqs : np.ndarray — length K, normalised (multiply by fs for Hz).
    """
    from vmdpy import VMD
    x = x.astype(np.float64)
    if len(x) % 2 == 1:
        x = x[:-1]
    u, _, omega = VMD(x, alpha, tau, K, DC, init, tol)
    centre_freqs = omega[-1, :]
    return np.asarray(u), np.asarray(centre_freqs)


def envelope_spectrum_of_modes(
    modes: np.ndarray,
    fs: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute the envelope spectrum of each mode/IMF.

    Parameters
    ----------
    modes : np.ndarray — shape (n_modes, n_samples).
    fs : float — sampling frequency, Hz.

    Returns
    -------
    f : np.ndarray — frequency axis (Hz).
    A : np.ndarray — shape (n_modes, len(f)).
    """
    from scipy.signal import hilbert
    from spectrum import amplitude_spectrum
    n_modes, n_samples = modes.shape
    A_list = []
    for k in range(n_modes):
        env = np.abs(hilbert(modes[k]))
        env -= env.mean()
        f, A_k = amplitude_spectrum(env, fs)
        A_list.append(A_k)
    return f, np.array(A_list)
