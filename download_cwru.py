"""
Download CWRU bearing .mat files from canonical URLs, verify by SHA-256
checksum, and organise into a clean folder structure.

Usage:
    python download_cwru.py                # download/verify everything
    python download_cwru.py --label IR007_0  # single file
    python download_cwru.py --verify-only    # check existing files, no download
    python download_cwru.py --write-checksums  # FIRST RUN ONLY: compute and store
                                               # checksums after manual download

Strategy:
    1. On first use, download files into data/cwru/ and run with
       --write-checksums to populate checksums.json from whatever was downloaded.
    2. On all subsequent runs, the script verifies each existing file against
       checksums.json. Mismatch -> warn and re-download. Missing -> download.
    3. This protects against silent dataset drift if CWRU re-uploads modified
       files, and gives a clean error message rather than corrupt analysis.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from config import CWRU_FILES, CWRU_BASE_URL, DATA_DIR

CHECKSUM_FILE = Path(DATA_DIR) / "checksums.json"


def sha256_of_file(path: Path, chunk_size: int = 1 << 20) -> str:
    """Compute SHA-256 hex digest of a file by streaming 1 MB chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def download_one(label: str, file_num: int, dest: Path) -> None:
    """Download a single .mat file with a basic User-Agent (CWRU's CDN sometimes
    rejects the default urllib agent)."""
    url = CWRU_BASE_URL.format(file_num=file_num)
    print(f"  Downloading {label:15s} <- {url}")
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (cwru-bearing-analysis)"})
    try:
        with urlopen(req, timeout=60) as resp:
            data = resp.read()
    except (URLError, HTTPError) as e:
        print(f"    FAILED: {e}", file=sys.stderr)
        raise
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"    -> {dest} ({len(data)/1e6:.2f} MB)")


def load_checksums() -> dict:
    if CHECKSUM_FILE.exists():
        return json.loads(CHECKSUM_FILE.read_text())
    return {}


def save_checksums(checksums: dict) -> None:
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHECKSUM_FILE.write_text(json.dumps(checksums, indent=2, sort_keys=True))
    print(f"Wrote {len(checksums)} checksums to {CHECKSUM_FILE}")


def file_path(label: str, file_num: int) -> Path:
    """Local path: data/cwru/<label>_<file_num>.mat — label-tagged so the
    filename itself documents what the file is."""
    return Path(DATA_DIR) / f"{label}_{file_num}.mat"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--label", help="Download only this label (default: all)")
    parser.add_argument("--verify-only", action="store_true",
                        help="Verify existing files against checksums; do not download")
    parser.add_argument("--write-checksums", action="store_true",
                        help="Compute checksums of currently downloaded files and write checksums.json")
    args = parser.parse_args()

    targets = ({args.label: CWRU_FILES[args.label]} if args.label else CWRU_FILES)
    checksums = load_checksums()

    if args.write_checksums:
        new_checksums = {}
        for label, meta in targets.items():
            path = file_path(label, meta["file_num"])
            if path.exists():
                new_checksums[label] = sha256_of_file(path)
                print(f"  {label:15s} {new_checksums[label][:16]}...")
            else:
                print(f"  {label:15s} MISSING — skipped")
        checksums.update(new_checksums)
        save_checksums(checksums)
        return

    n_ok, n_downloaded, n_mismatch, n_failed = 0, 0, 0, 0
    for label, meta in targets.items():
        path = file_path(label, meta["file_num"])
        expected = checksums.get(label)

        if path.exists():
            actual = sha256_of_file(path)
            if expected is None:
                print(f"  {label:15s} present, no checksum on record (run --write-checksums)")
                n_ok += 1
                continue
            if actual == expected:
                print(f"  {label:15s} OK (checksum match)")
                n_ok += 1
                continue
            print(f"  {label:15s} CHECKSUM MISMATCH — expected {expected[:12]}, got {actual[:12]}")
            n_mismatch += 1
            if args.verify_only:
                continue
            print(f"    Re-downloading...")

        if args.verify_only:
            print(f"  {label:15s} MISSING")
            continue

        try:
            download_one(label, meta["file_num"], path)
            n_downloaded += 1
        except Exception:
            n_failed += 1

    print(f"\nSummary: ok={n_ok}, downloaded={n_downloaded}, "
          f"mismatch={n_mismatch}, failed={n_failed}")
    if n_failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
