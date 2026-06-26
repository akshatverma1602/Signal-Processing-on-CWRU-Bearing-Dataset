"""
Central configuration for the CWRU bearing fault analysis project.
All bearing geometry, file mappings, and analysis parameters live here.
No analysis script should hardcode any of these values.
"""

# -----------------------------------------------------------------------------
# Bearing geometry — SKF 6205-2RS JEM (drive end bearing on the CWRU rig)
# Source: CWRU Bearing Data Center, Apparatus & Procedures page,
# cross-checked against SKF 6205-2RS manufacturer data sheet.
# All dimensions in inches to match the CWRU convention.
# -----------------------------------------------------------------------------
BEARING_DE = {
    "designation":    "SKF 6205-2RS JEM",
    "n_balls":        9,
    "ball_diameter":  0.3126,    # inches
    "pitch_diameter": 1.537,     # inches
    "contact_angle":  0.0,       # radians; deep-groove ball bearing under radial load
}

# Fan end bearing — SKF 6203, included for completeness; not used in primary pipeline
BEARING_FE = {
    "designation":    "SKF 6203-2RS JEM",
    "n_balls":        9,
    "ball_diameter":  0.2656,
    "pitch_diameter": 1.122,
    "contact_angle":  0.0,
}

# -----------------------------------------------------------------------------
# Operating conditions: motor load (HP) -> approximate shaft speed (rpm)
# Per CWRU documentation; small drift (< 1 rpm) is normal between runs.
# -----------------------------------------------------------------------------
LOAD_TO_RPM = {
    0: 1797,
    1: 1772,
    2: 1750,
    3: 1730,
}

# -----------------------------------------------------------------------------
# Sampling
# -----------------------------------------------------------------------------
FS_12K = 12000   # Hz, primary dataset
FS_48K = 48000   # Hz, available for some DE files; we use 12k as the standard

# -----------------------------------------------------------------------------
# File catalogue — 12k Drive End Bearing Fault Data + 48k Normal Baseline
# Maps a human-readable label to (CWRU file number, load_HP).
# Source URLs are reconstructed as:
#   https://engineering.case.edu/sites/default/files/{file_number}.mat
# Verified against CWRU Bearing Data Center pages.
# -----------------------------------------------------------------------------
CWRU_FILES = {
    # Healthy baseline (sampled at 48 kHz on CWRU rig)
    "Normal_0":      {"file_num": 97,  "load_hp": 0, "fault": "none",  "size_in": 0.000, "fs_hz": 48000},
    "Normal_1":      {"file_num": 98,  "load_hp": 1, "fault": "none",  "size_in": 0.000, "fs_hz": 48000},
    "Normal_2":      {"file_num": 99,  "load_hp": 2, "fault": "none",  "size_in": 0.000, "fs_hz": 48000},
    "Normal_3":      {"file_num": 100, "load_hp": 3, "fault": "none",  "size_in": 0.000, "fs_hz": 48000},

    # Inner race faults, 12k DE
    "IR007_0":       {"file_num": 105, "load_hp": 0, "fault": "inner", "size_in": 0.007, "fs_hz": 12000},
    "IR007_1":       {"file_num": 106, "load_hp": 1, "fault": "inner", "size_in": 0.007, "fs_hz": 12000},
    "IR007_2":       {"file_num": 107, "load_hp": 2, "fault": "inner", "size_in": 0.007, "fs_hz": 12000},
    "IR007_3":       {"file_num": 108, "load_hp": 3, "fault": "inner", "size_in": 0.007, "fs_hz": 12000},
    "IR014_0":       {"file_num": 169, "load_hp": 0, "fault": "inner", "size_in": 0.014, "fs_hz": 12000},
    "IR014_1":       {"file_num": 170, "load_hp": 1, "fault": "inner", "size_in": 0.014, "fs_hz": 12000},
    "IR014_2":       {"file_num": 171, "load_hp": 2, "fault": "inner", "size_in": 0.014, "fs_hz": 12000},
    "IR014_3":       {"file_num": 172, "load_hp": 3, "fault": "inner", "size_in": 0.014, "fs_hz": 12000},
    "IR021_0":       {"file_num": 209, "load_hp": 0, "fault": "inner", "size_in": 0.021, "fs_hz": 12000},
    "IR021_1":       {"file_num": 210, "load_hp": 1, "fault": "inner", "size_in": 0.021, "fs_hz": 12000},
    "IR021_2":       {"file_num": 211, "load_hp": 2, "fault": "inner", "size_in": 0.021, "fs_hz": 12000},
    "IR021_3":       {"file_num": 212, "load_hp": 3, "fault": "inner", "size_in": 0.021, "fs_hz": 12000},

    # Ball faults, 12k DE
    "B007_0":        {"file_num": 118, "load_hp": 0, "fault": "ball",  "size_in": 0.007, "fs_hz": 12000},
    "B007_1":        {"file_num": 119, "load_hp": 1, "fault": "ball",  "size_in": 0.007, "fs_hz": 12000},
    "B007_2":        {"file_num": 120, "load_hp": 2, "fault": "ball",  "size_in": 0.007, "fs_hz": 12000},
    "B007_3":        {"file_num": 121, "load_hp": 3, "fault": "ball",  "size_in": 0.007, "fs_hz": 12000},
    "B014_0":        {"file_num": 185, "load_hp": 0, "fault": "ball",  "size_in": 0.014, "fs_hz": 12000},
    "B014_1":        {"file_num": 186, "load_hp": 1, "fault": "ball",  "size_in": 0.014, "fs_hz": 12000},
    "B014_2":        {"file_num": 187, "load_hp": 2, "fault": "ball",  "size_in": 0.014, "fs_hz": 12000},
    "B014_3":        {"file_num": 188, "load_hp": 3, "fault": "ball",  "size_in": 0.014, "fs_hz": 12000},
    "B021_0":        {"file_num": 222, "load_hp": 0, "fault": "ball",  "size_in": 0.021, "fs_hz": 12000},
    "B021_1":        {"file_num": 223, "load_hp": 1, "fault": "ball",  "size_in": 0.021, "fs_hz": 12000},
    "B021_2":        {"file_num": 224, "load_hp": 2, "fault": "ball",  "size_in": 0.021, "fs_hz": 12000},
    "B021_3":        {"file_num": 225, "load_hp": 3, "fault": "ball",  "size_in": 0.021, "fs_hz": 12000},

    # Outer race faults @ 6:00 (centred in load zone), 12k DE
    # NOTE: OR014 files (197-200) are a known anomaly in the CWRU dataset.
    # File 198 in particular may contain data that does not show the expected
    # 0.014" fault signature (RMS and kurtosis near healthy baseline). This has
    # been documented in Smith & Randall (2015) "Rolling Element Bearing
    # Diagnostics Using the Case Western Reserve University Data: A Benchmark
    # Study". If your severity analysis shows non-monotonic outer-race
    # progression, this file is the likely cause. Inspect the raw signal before
    # drawing conclusions about the 0.014" fault size.
    "OR007@6_0":     {"file_num": 130, "load_hp": 0, "fault": "outer", "size_in": 0.007, "fs_hz": 12000},
    "OR007@6_1":     {"file_num": 131, "load_hp": 1, "fault": "outer", "size_in": 0.007, "fs_hz": 12000},
    "OR007@6_2":     {"file_num": 132, "load_hp": 2, "fault": "outer", "size_in": 0.007, "fs_hz": 12000},
    "OR007@6_3":     {"file_num": 133, "load_hp": 3, "fault": "outer", "size_in": 0.007, "fs_hz": 12000},
    "OR014@6_0":     {"file_num": 197, "load_hp": 0, "fault": "outer", "size_in": 0.014, "fs_hz": 12000},
    "OR014@6_1":     {"file_num": 198, "load_hp": 1, "fault": "outer", "size_in": 0.014, "fs_hz": 12000},
    "OR014@6_2":     {"file_num": 199, "load_hp": 2, "fault": "outer", "size_in": 0.014, "fs_hz": 12000},
    "OR014@6_3":     {"file_num": 200, "load_hp": 3, "fault": "outer", "size_in": 0.014, "fs_hz": 12000},
    "OR021@6_0":     {"file_num": 234, "load_hp": 0, "fault": "outer", "size_in": 0.021, "fs_hz": 12000},
    "OR021@6_1":     {"file_num": 235, "load_hp": 1, "fault": "outer", "size_in": 0.021, "fs_hz": 12000},
    "OR021@6_2":     {"file_num": 236, "load_hp": 2, "fault": "outer", "size_in": 0.021, "fs_hz": 12000},
    "OR021@6_3":     {"file_num": 237, "load_hp": 3, "fault": "outer", "size_in": 0.021, "fs_hz": 12000},
}

# Base URL pattern for direct download
CWRU_BASE_URL = "https://engineering.case.edu/sites/default/files/{file_num}.mat"

# Local data directory (relative to project root)
DATA_DIR = "data/cwru"
