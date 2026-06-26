# CWRU Bearing Signal Analysis — Vibration Diagnostics from First Principles

A complete, physics-grounded implementation of the vibration signal-processing pipeline used for rolling-element bearing fault detection, applied to the Case Western Reserve University (CWRU) Bearing Fault Dataset.

**Author:** Akshat Verma — Rotating Equipment Engineer, HPCL Mumbai Refinery; B.Tech (Mech.), IIT Bombay

---

## What this project demonstrates

The implementation of the full bearing-fault diagnostic pipeline from first principles in Python, validate every step against the underlying physics, and interpret the results with the engineering judgement of someone who diagnoses bearing faults on industrial machinery daily.

This is not a "bearing fault classifier" project. There is no machine learning here. The deliverable is an end-to-end implementation of the methods that have defined industrial vibration analysis for forty years — envelope demodulation, spectral kurtosis, time-frequency analysis, adaptive decomposition — with each method's physical motivation, mathematical implementation, and failure modes explicitly documented.

## Methods implemented

| Stage | Method | Module | What it does |
|---|---|---|---|
| 1 | Time-domain statistics | `severity.py` | RMS, kurtosis, crest factor, peak-to-peak as fault indicators |
| 2 | Bearing kinematics | `fault_frequencies.py` | BPFO, BPFI, BSF, FTF derived from no-slip rolling |
| 3 | Windowed FFT | `spectrum.py` | Amplitude-calibrated single-sided spectrum with Hanning window |
| 4 | Envelope analysis | `envelope.py` | Bandpass + Hilbert + envelope-spectrum demodulation |
| 5 | Fast kurtogram | `kurtogram.py` | Automatic demodulation-band selection via spectral kurtosis |
| 6 | STFT and CWT | `time_frequency.py` | Spectrograms and constant-Q scalograms for non-stationary signals |
| 7 | EMD and VMD | `decomposition.py` | Adaptive signal decomposition; mode-mixing comparison |
| 8 | Severity tracking | `severity.py` | Feature progression across fault sizes 0.007″ → 0.014″ → 0.021″ |
| 9 | Cross-load analysis | (notebook) | Feature behaviour across motor loads 0–3 HP |

All modules are dependency-light (NumPy, SciPy, PyWavelets, PyEMD, vmdpy, matplotlib, pandas) and well-documented. Every function has a docstring describing the *physical* meaning of its inputs and outputs, not just the data types.

## Repository layout

```
cwru-bearing-analysis/
├── README.md                      ← this file
├── requirements.txt
├── config.py                      ← central config: bearing geometry, file mapping, sampling rates
├── download_cwru.py               ← download & checksum-verify CWRU .mat files
├── cwru_loader.py                 ← uniform interface for loading CWRU records
├── spectrum.py                    ← amplitude-calibrated FFT
├── fault_frequencies.py           ← bearing kinematics
├── envelope.py                    ← bandpass + Hilbert + envelope spectrum
├── kurtogram.py                   ← fast dyadic kurtogram
├── time_frequency.py              ← STFT and CWT wrappers
├── decomposition.py               ← EMD and VMD wrappers
├── severity.py                    ← bundled feature extraction
├── notebook.ipynb                 ← the main deliverable: tutorial walkthrough
├── data/cwru/                     ← .mat files land here after download
│   └── checksums.json             ← integrity check for reproducibility
└── docs/
    ├── technical_summary.pdf      ← 3-page portfolio document
    └── figures/                   ← exported plots
```

## How to run it

### 1. Install dependencies

```bash
git clone https://github.com/<your-github>/cwru-bearing-analysis
cd cwru-bearing-analysis
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` (minimal):
```
numpy>=1.24
scipy>=1.10
matplotlib>=3.7
pandas>=2.0
PyWavelets>=1.4
EMD-signal>=1.5
vmdpy>=0.2
jupyter>=1.0
```

### 2. Download the dataset

```bash
python download_cwru.py
```

This fetches all 36 `.mat` files (~150 MB total) from canonical CWRU URLs into `data/cwru/`. Each download is verified against SHA-256 checksums committed in `data/cwru/checksums.json`, so subsequent runs detect any silent dataset drift on CWRU's side.

If you have already downloaded the files manually, run once with `--write-checksums` to populate the checksum file. (Find all downloaded files in the folder `data` to run directly.

### 3. Run the notebook

```bash
jupyter lab notebook.ipynb
```

The notebook runs top to bottom on a freshly downloaded dataset and reproduces every figure and table in the technical summary PDF.

## What the outputs mean — summary results table

This is the headline result table: did each method detect each fault, and how confidently? "Detection" = clear peak at the theoretical fault frequency in the relevant spectrum, with at least 6 dB SNR against the local noise floor. All measurements at 1 HP load (1772 rpm), fault size 0.007″.

| Method | Healthy (false-alarm check) | Outer race | Inner race | Ball |
|---|---|---|---|---|
| **Time-domain stats only** (kurt/crest) | no false alarm | flagged | flagged | flagged (weakly) |
| **Raw FFT** (Stage 3) | no false alarm | sometimes detected (~10 dB) | rarely detected (~3 dB) | not detected |
| **Envelope spectrum, manual band** (Stage 4) | no false alarm | strong (~30 dB) | strong (~22 dB) | moderate (~12 dB) |
| **Envelope spectrum, kurtogram band** (Stage 5) | no false alarm | strong (~30 dB) | strong (~24 dB) | moderate (~14 dB) |
| **EMD best IMF + envelope** (Stage 7) | no false alarm | strong (~25 dB) | moderate (~20 dB) | moderate (~12 dB), non-deterministic |
| **VMD best mode + envelope** (Stage 7) | no false alarm | strong (~28 dB) | strong (~22 dB) | moderate (~14 dB) |

(SNR values are typical; exact numbers vary per file. The notebook reports actual measurements on each run.)

The diagnostic pattern is robust:
- **Time-domain statistics flag faults but cannot localise them** — kurtosis tells you something is wrong, not what.
- **Raw FFT detects only severe outer race faults reliably** — the energy lives at the resonance, not the fault frequency. This is the central failure that motivates envelope analysis.
- **Envelope analysis (Stage 4) is the workhorse** — it adds 15–20 dB SNR over raw FFT for race faults, taking them from invisible to obvious. This is the method that field instruments at HPCL run by default.
- **The kurtogram (Stage 5) automates band selection** without significant SNR penalty vs. a well-chosen manual band, eliminating the human-in-the-loop step.
- **VMD (Stage 7) matches the envelope spectrum's performance and adds deterministic mode separation** — useful when multiple modulating sources coexist (real industrial signals).
- **EMD (Stage 7) is competitive but non-deterministic** and is being superseded by VMD in the bearing-diagnostics literature.

## References

The methods implemented draw on the following primary sources:
- Randall, R.B. & Antoni, J. (2011). "Rolling element bearing diagnostics — A tutorial." *Mechanical Systems and Signal Processing* 25(2): 485–520.
- McFadden, P.D. & Smith, J.D. (1984). "Model for the vibration produced by a single point defect in a rolling element bearing." *Journal of Sound and Vibration* 96(1).
- Antoni, J. (2007). "Fast computation of the kurtogram for the detection of transient faults." *Mechanical Systems and Signal Processing* 21(1): 108–124.
- Dragomiretskiy, K. & Zosso, D. (2014). "Variational mode decomposition." *IEEE Transactions on Signal Processing* 62(3): 531–544.
- Huang, N.E. et al. (1998). "The empirical mode decomposition and the Hilbert spectrum for nonlinear and non-stationary time series analysis." *Proc. Royal Society A* 454: 903–995.
- ISO 10816 / ISO 20816 — Mechanical vibration evaluation by measurement on non-rotating parts.

The CWRU dataset and its bearing geometry specifications:
- Case Western Reserve University Bearing Data Center: https://engineering.case.edu/bearingdatacenter
