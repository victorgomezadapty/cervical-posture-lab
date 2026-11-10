"""Try to re-download the two deposited files from Zenodo, only if a local copy is missing.

Usage: .venv/bin/python scripts/fetch_data.py
Never overwrites an existing file. Verifies md5 and size after download.
Zenodo sometimes answers HTTP 403 to automated traffic from this machine. If that happens the
script reports it and exits without error; the project then relies on the copied files, whose
md5 and size are checked on every load.
"""
from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cervical_posture_lab import data as D  # noqa: E402


def main() -> None:
    D.RAW_DIR.mkdir(parents=True, exist_ok=True)
    for name, url in D.ZENODO_FILE_URLS.items():
        p = D.RAW_DIR / name
        if p.exists():
            continue
        tmp = p.with_name(p.name + ".part")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "cervical-posture-lab/0.1"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                tmp.write_bytes(resp.read())
            tmp.rename(p)
            print(f"Downloaded: {name}")
        except (urllib.error.URLError, TimeoutError) as e:
            if tmp.exists():
                tmp.unlink()
            print(f"Could not download {name} ({e}). Copy the deposited file into {D.RAW_DIR} by hand.")
            return
    D.verify_raw()
    print("Both deposited files present and verified (md5 and size).")


if __name__ == "__main__":
    main()
