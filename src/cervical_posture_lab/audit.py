"""Codebook audit of the deposited SPSS file against the deposited readme.

Every mismatch is flagged and documented. Nothing is silently fixed: the .sav and the
readme stay byte identical to the deposit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data as D

# Columns whose SPSS labels are questionnaire or screening question wording. Their label text
# is not reproduced in any output of this project.
QUESTION_LABEL_COLUMNS = ["ChronicNeckPain", "NMQ_neck_lastyear", "NMQ_neck_lastmonth",
                          "NMQ_neck_today", "NMQ_neck_last7days"]

# How each deposited column is covered by the readme variable list (judged by reading the
# readme; tested against its text in tests/).
README_COVERAGE = {
    "ID": "not listed",
    "age": "listed: Age (years)",
    "Sex": "listed: sex (male/female), codes not given",
    "Weight": "listed: Weight (kg)",
    "Height": "listed: Height (m)",
    "BMI": "listed: BMI (kg/m2)",
    "ChronicNeckPain": "not listed (group variable only described in prose)",
    "NMQ_neck_lastyear": "listed as one NMQ item set",
    "NMQ_neck_lastmonth": "listed as one NMQ item set",
    "NMQ_neck_today": "listed as one NMQ item set",
    "NMQ_neck_last7days": "listed as one NMQ item set",
    "VAS_neck_0to100": "not listed",
    "NDI_total": "listed: NDI, scale given as 0 to 100",
    "IPAQ_total": "listed: IPAQ total (MET minute/week)",
    "IPAQ_categorized": "listed: IPAQ categorized",
    "Sitting_Evaluator1": "only as one entry 'CVA (grades)', evaluator and position not described",
    "Standing_Evaluator1": "only as one entry 'CVA (grades)', evaluator and position not described",
    "Sitting_Evaluator2": "only as one entry 'CVA (grades)', evaluator and position not described",
    "Standing_Evaluator2": "only as one entry 'CVA (grades)', evaluator and position not described",
}
README_UNDER_SPECIFIED = ["ID", "ChronicNeckPain", "VAS_neck_0to100"] + D.CVA_RAW


def column_inventory(raw: pd.DataFrame, meta) -> pd.DataFrame:
    rows = []
    for c in raw.columns:
        label = meta.column_names_to_labels.get(c) or ""
        shown = "[question wording, not reproduced]" if c in QUESTION_LABEL_COLUMNS else label
        vl = meta.variable_value_labels.get(c)
        x = raw[c]
        rows.append({
            "column": c,
            "spss_label": shown,
            "spss_value_labels": "; ".join(f"{int(k)} = {v}" for k, v in vl.items()) if vl else "",
            "spss_format": meta.original_variable_types.get(c, ""),
            "readme_coverage": README_COVERAGE[c],
            "n_present": int(x.notna().sum()),
            "n_missing": int(x.isna().sum()),
            "min": float(x.min()),
            "max": float(x.max()),
        })
    return pd.DataFrame(rows)


def id_gaps(raw: pd.DataFrame) -> list[int]:
    ids = set(raw["ID"].astype(int))
    return [i for i in range(1, max(ids) + 1) if i not in ids]


def bmi_identity(raw: pd.DataFrame) -> dict:
    as_m = raw["Weight"] / raw["Height"] ** 2
    as_label = raw["Weight"] / (raw["Height"] / 100) ** 2  # height taken as cm, as the SPSS label says
    return {
        "max_abs_diff_bmi_height_in_m": float((raw["BMI"] - as_m).abs().max()),
        "height_range_as_deposited": [float(raw["Height"].min()), float(raw["Height"].max())],
        "bmi_deposited_range": [float(raw["BMI"].min()), float(raw["BMI"].max())],
        "bmi_if_height_read_as_cm_range": [float(as_label.min()), float(as_label.max())],
        "bmi_if_height_read_as_cm_median": float(as_label.median()),
    }


def flags(raw: pd.DataFrame, meta, readme: str) -> pd.DataFrame:
    lab = meta.column_names_to_labels
    gaps = id_gaps(raw)
    b = bmi_identity(raw)
    rows = [
        {"flag": "F1", "severity": "main", "item": "Height unit",
         "deposit_says": f"SPSS label '{lab['Height']}'; readme 'Height (m)'",
         "observed": f"values {b['height_range_as_deposited'][0]:.2f} to {b['height_range_as_deposited'][1]:.2f}; "
                     f"BMI equals weight/height^2 with height in metres (max abs diff {b['max_abs_diff_bmi_height_in_m']:.1e})",
         "handling": "analysed as metres (HeightM in memory); .sav label left as deposited"},
        {"flag": "F2", "severity": "main", "item": "Standing_Evaluator2 label",
         "deposit_says": f"SPSS label '{lab['Standing_Evaluator2']}'",
         "observed": "column name says evaluator 2; label repeats evaluator 1",
         "handling": "column name followed; label left as deposited"},
        {"flag": "F3", "severity": "main", "item": "Readme variable list incomplete",
         "deposit_says": "readme lists 19 variables but names fewer items",
         "observed": "ID, ChronicNeckPain and VAS_neck_0to100 not listed; four CVA columns "
                     "(evaluator by position) covered only by one entry 'CVA (grades)'",
         "handling": "columns interpreted from names, SPSS labels and value labels; documented in t01"},
        {"flag": "F4", "severity": "main", "item": "ID gaps",
         "deposit_says": "no description of ID",
         "observed": f"{raw['ID'].nunique()} unique IDs from {int(raw['ID'].min())} to {int(raw['ID'].max())}; "
                     f"{len(gaps)} numbers absent ({', '.join(map(str, gaps))})",
         "handling": "ID treated as a study code only; reasons for gaps unknown, not inferred"},
        {"flag": "F5", "severity": "minor", "item": "Angle name",
         "deposit_says": "SPSS labels say 'Craniocervical angle'; readme says craniovertebral angle (CVA)",
         "observed": "same four columns",
         "handling": "read as CVA, as in the readme and record title"},
        {"flag": "F6", "severity": "minor", "item": "Readme citation line",
         "deposit_says": "readme citation names three people, including the co-investigator",
         "observed": "Zenodo and DataCite list two creators",
         "handling": "official two creator citation used; co-investigator credited as contributor"},
        {"flag": "F7", "severity": "minor", "item": "NDI scale",
         "deposit_says": "readme: NDI, 0 to 100",
         "observed": f"NDI values {raw['NDI_total'].min():.0f} to {raw['NDI_total'].max():.0f}, all even",
         "handling": "analysed as deposited on the stated 0 to 100 scale; even values are consistent with "
                     "a doubled score (inferred, not stated)"},
        {"flag": "F8", "severity": "minor", "item": "CVA resolution",
         "deposit_says": "no description of how each value was obtained",
         "observed": "every CVA value is a multiple of 1/3 degree",
         "handling": "consistent with each value being a mean of three readings (inferred, not stated); "
                     "agreement results refer to the deposited values"},
    ]
    return pd.DataFrame(rows)


def consistency_checks(raw: pd.DataFrame) -> pd.DataFrame:
    """Cross checks between columns. Reported as observations, not as errors."""
    d = raw.dropna(subset=["IPAQ_total"])
    cat = np.where(d["IPAQ_total"] < 600, 1, np.where(d["IPAQ_total"] <= 3000, 2, 3))
    g0, g1 = raw["ChronicNeckPain"] == 0, raw["ChronicNeckPain"] == 1
    rows = [
        ("IPAQ_categorized agrees with IPAQ_total thresholds", int((cat != d["IPAQ_categorized"]).sum()), len(d)),
        ("chronic neck pain rows with no neck pain in the last year (NMQ)", int((g1 & (raw["NMQ_neck_lastyear"] == 0)).sum()), int(g1.sum())),
        ("asymptomatic rows with neck pain in the last year (NMQ)", int((g0 & (raw["NMQ_neck_lastyear"] == 1)).sum()), int(g0.sum())),
        ("asymptomatic rows with VAS above 0", int((g0 & (raw["VAS_neck_0to100"] > 0)).sum()), int(g0.sum())),
        ("chronic neck pain rows with VAS equal to 0", int((g1 & (raw["VAS_neck_0to100"] == 0)).sum()), int(g1.sum())),
        ("duplicate IDs", int(raw["ID"].duplicated().sum()), len(raw)),
    ]
    return pd.DataFrame(rows, columns=["check", "rows_flagged", "rows_checked"])


def missingness(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for c in raw.columns:
        m0 = int(raw.loc[raw["ChronicNeckPain"] == 0, c].isna().sum())
        m1 = int(raw.loc[raw["ChronicNeckPain"] == 1, c].isna().sum())
        rows.append({"column": c, "missing_asymptomatic_of_42": m0, "missing_chronic_neck_pain_of_50": m1,
                     "missing_total_of_92": m0 + m1})
    return pd.DataFrame(rows)
