"""Loading, integrity checks and labelling for the forward head posture table.

Only data source: Zenodo record 17550555 (version DOI 10.5281/zenodo.17550555,
concept DOI 10.5281/zenodo.17550554), license cc-by-4.0, open access.
The deposited files are never modified. Derived columns exist in memory only.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pyreadstat

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
SAV_NAME = "Database_Forward Head Posture and Neck Pain.sav"
README_NAME = "readme_Dataset Forward Head Posture and Neck Pain.txt"
SAV_PATH = RAW_DIR / SAV_NAME
README_PATH = RAW_DIR / README_NAME

EXPECTED = {
    SAV_NAME: {"md5": "e835bd09dea8ec8bfa73e91e69bac380", "bytes": 10039},
    README_NAME: {"md5": "9b0c87e5f31e8d6fbba7bd43b924d072", "bytes": 5985},
}
EXPECTED_ROWS = 92
EXPECTED_COLS = 19

ZENODO_RECORD = "https://zenodo.org/records/17550555"
ZENODO_DOI = "10.5281/zenodo.17550555"
ZENODO_CONCEPT_DOI = "10.5281/zenodo.17550554"
ZENODO_ISSUED = "2025-11-20"
LICENSE_ID = "cc-by-4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
ZENODO_FILE_URLS = {
    SAV_NAME: "https://zenodo.org/api/records/17550555/files/Database_Forward%20Head%20Posture%20and%20Neck%20Pain.sav/content",
    README_NAME: "https://zenodo.org/api/records/17550555/files/readme_Dataset%20Forward%20Head%20Posture%20and%20Neck%20Pain.txt/content",
}

DATASET_TITLE = "Forward Head Posture in individuals with and without chronic neck pain"
DATASET_VERSION = ('Final data from study "Assessment of forward head posture in individuals with and '
                   'without chronic neck pain: a cross-sectional study"')
SHORT_NAME = "Cervical Posture Lab"
CREATORS = ["Rodríguez-Romero, Beatriz", "Tunas-Maceiras, Isabel"]
CONTRIBUTORS = ["Ramos-Gómez, Fernando"]  # co-investigator in the readme, not a dataset creator
DATASET_CITATION = (
    "Rodríguez-Romero, B., and Tunas-Maceiras, I. (2025). " + DATASET_TITLE +
    " [Dataset]. Zenodo. https://doi.org/10.5281/zenodo.17550555"
)
SHORT_CITATION = "Rodríguez-Romero and Tunas-Maceiras 2025, Zenodo 10.5281/zenodo.17550555"

PAPER_DOI = "10.1016/j.gaitpost.2026.110093"
PAPER_LICENSE = "CC BY-NC 4.0"
PAPER_CITATION = (
    "Tunas-Maceiras I, Ramos-Gómez F, Rodríguez-Romero B. Assessment of forward head posture in "
    "individuals with and without chronic neck pain: A cross-sectional study. Gait & Posture. "
    "2026;125:110093. https://doi.org/10.1016/j.gaitpost.2026.110093"
)

CVA_RAW = ["Sitting_Evaluator1", "Sitting_Evaluator2", "Standing_Evaluator1", "Standing_Evaluator2"]
CVA_MEAN = {"sitting": "CVA_sitting_mean", "standing": "CVA_standing_mean"}
GROUP_LABELS = {0: "asymptomatic", 1: "chronic neck pain"}
GROUP_ORDER = ["asymptomatic", "chronic neck pain"]

IDENTIFIER_PATTERNS = [
    "name", "birth", "dob", "date", "address", "street", "zip", "postcode", "phone",
    "email", "mail", "mrn", "record", "insurance", "photo", "image", "initial",
]


def md5sum(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_raw() -> dict:
    """Raise if either deposited file is missing or differs from the Zenodo record."""
    out = {}
    for name, exp in EXPECTED.items():
        p = RAW_DIR / name
        if not p.exists():
            raise FileNotFoundError(f"{p} not found. Copy the deposited file or run scripts/fetch_data.py.")
        size, digest = p.stat().st_size, md5sum(p)
        if digest != exp["md5"] or size != exp["bytes"]:
            raise ValueError(f"{name} does not match {ZENODO_DOI}: md5={digest}, bytes={size}")
        out[name] = {"md5": digest, "bytes": size}
    return out


def load_raw():
    """The .sav exactly as deposited (values and SPSS metadata). Hashes checked first."""
    verify_raw()
    df, meta = pyreadstat.read_sav(str(SAV_PATH))
    if df.shape != (EXPECTED_ROWS, EXPECTED_COLS):
        raise ValueError(f"unexpected shape {df.shape}")
    return df, meta


def load_readme() -> str:
    verify_raw()
    return README_PATH.read_text(encoding="utf-8")


def identifier_like_columns(columns) -> list[str]:
    return [str(c) for c in columns
            if str(c).lower() != "id" and any(p in str(c).lower() for p in IDENTIFIER_PATTERNS)]


def prepare(raw: pd.DataFrame, meta) -> pd.DataFrame:
    """Add documented derived columns in memory. Deposited columns are left intact.

    * group, female, neck_pain: parsed with the SPSS value labels.
    * HeightM: the deposited Height, read as metres (the SPSS label says cm; see audit flag F1).
    * CVA_sitting_mean, CVA_standing_mean: mean of the two deposited evaluator columns.
    """
    vl = meta.variable_value_labels
    assert vl["Sex"] == {0.0: "man", 1.0: "woman"}, vl["Sex"]
    assert vl["ChronicNeckPain"] == {0.0: "No", 1.0: "Sí"}, vl["ChronicNeckPain"]
    df = raw.copy()
    df["sex_label"] = df["Sex"].map(vl["Sex"])
    df["female"] = (df["Sex"] == 1).astype(int)
    df["neck_pain"] = (df["ChronicNeckPain"] == 1).astype(int)
    df["group"] = pd.Categorical(df["ChronicNeckPain"].map({0.0: GROUP_LABELS[0], 1.0: GROUP_LABELS[1]}),
                                 categories=GROUP_ORDER)
    df["HeightM"] = df["Height"]
    df["CVA_sitting_mean"] = df[["Sitting_Evaluator1", "Sitting_Evaluator2"]].mean(axis=1)
    df["CVA_standing_mean"] = df[["Standing_Evaluator1", "Standing_Evaluator2"]].mean(axis=1)
    return df
