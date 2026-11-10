"""Run the full Cervical Posture Lab analysis offline from the local deposited files.

Usage (from the project root):
    .venv/bin/python scripts/run_analysis.py

Writes tables/, figures/ (PNG and WebP), results/summary.json and RESULTS.md.
Stops if the md5 or byte size of either deposited file differs from the Zenodo record.
"""
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cervical_posture_lab import analysis as A  # noqa: E402
from cervical_posture_lab import audit as AU  # noqa: E402
from cervical_posture_lab import data as D  # noqa: E402
from cervical_posture_lab import figures as F  # noqa: E402
from cervical_posture_lab.report import write_results_md  # noqa: E402

TABLES, FIGS, RES = ROOT / "tables", ROOT / "figures", ROOT / "results"


def r(x, k=3):
    if isinstance(x, (list, tuple)):
        return [r(v, k) for v in x]
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), k)


def rec(row: pd.Series, keys, k=3) -> dict:
    return {key: r(row[key], k) for key in keys}


def main() -> None:
    for p in (TABLES, FIGS, RES):
        p.mkdir(exist_ok=True)
    for old in list(TABLES.glob("*.csv")) + list(FIGS.glob("*.png")) + list(FIGS.glob("*.webp")):
        old.unlink()  # generated outputs only; data/raw is never touched
    log = []

    hashes = D.verify_raw()
    raw, meta = D.load_raw()
    readme = D.load_readme()
    df = D.prepare(raw, meta)
    log.append(f"verified {json.dumps(hashes)} shape {raw.shape}")

    inv = AU.column_inventory(raw, meta)
    flags = AU.flags(raw, meta, readme)
    cons = AU.consistency_checks(raw)
    miss = AU.missingness(raw)
    bmi = AU.bmi_identity(raw)
    gaps = AU.id_gaps(raw)
    desc = A.describe_by_group(df)
    props = A.proportions_by_group(df)
    prim = A.primary_contrasts(df)
    sens = A.sensitivity_contrasts(df)
    sexbmi = A.sex_bmi_associations(df)
    symp = A.symptom_associations(df)
    sitstand = A.sitting_vs_standing(df)
    agr = A.agreement(df)

    height = pd.DataFrame([
        {"reading": "Height as metres (readme, used here)", "bmi_min": bmi["bmi_deposited_range"][0],
         "bmi_max": bmi["bmi_deposited_range"][1], "max_abs_diff_vs_deposited_bmi": bmi["max_abs_diff_bmi_height_in_m"]},
        {"reading": "Height as cm (SPSS label, not used)", "bmi_min": bmi["bmi_if_height_read_as_cm_range"][0],
         "bmi_max": bmi["bmi_if_height_read_as_cm_range"][1],
         "max_abs_diff_vs_deposited_bmi": float((raw["Weight"] / (raw["Height"] / 100) ** 2 - raw["BMI"]).abs().max())},
    ])
    agr_out = agr.copy()
    for c in ("loa_low_ci95", "loa_high_ci95"):
        agr_out[c] = agr_out[c].map(lambda v: f"{v[0]:.3f} to {v[1]:.3f}")

    outs = [
        ("t01_column_inventory_and_readme_coverage.csv", inv),
        ("t02_codebook_flags.csv", flags),
        ("t03_consistency_checks.csv", cons),
        ("t04_missingness_by_group.csv", miss),
        ("t05_height_unit_check.csv", height),
        ("t06_continuous_by_group.csv", desc),
        ("t07_proportions_by_group.csv", props),
        ("t08_primary_contrasts.csv", prim),
        ("t09_evaluator_sensitivity_contrasts.csv", sens),
        ("t10_sex_and_bmi_associations.csv", sexbmi),
        ("t11_symptom_associations_chronic_neck_pain.csv", symp),
        ("t12_evaluator_agreement.csv", agr_out),
        ("t13_sitting_vs_standing.csv", pd.DataFrame([sitstand])),
    ]
    for name, t in outs:
        t.to_csv(TABLES / name, index=False, float_format="%.6g")

    made = []
    made += F.fig_audit(raw, flags, gaps, FIGS / "fig01_codebook_audit.png")
    made += F.fig_missingness(miss, FIGS / "fig02_missingness.png")
    made += F.fig_cva_by_group(df, FIGS / "fig03_cva_by_group.png")
    made += F.fig_forest(prim, sens, FIGS / "fig04_prespecified_contrasts.png")
    made += F.fig_agreement(df, agr, FIGS / "fig05_evaluator_agreement.png")
    made += F.fig_symptoms(df, FIGS / "fig06_symptom_associations.png")

    ckeys = ["estimate", "se_hc3", "ci95_low", "ci95_high", "p", "p_holm"]
    g = df["group"]
    summary = {
        "project": D.SHORT_NAME,
        "status": "public",
        "dataset": {"title": D.DATASET_TITLE, "version": D.DATASET_VERSION, "record": D.ZENODO_RECORD,
                    "doi": D.ZENODO_DOI, "concept_doi": D.ZENODO_CONCEPT_DOI, "issued": D.ZENODO_ISSUED,
                    "license": D.LICENSE_ID, "creators": D.CREATORS, "contributors": D.CONTRIBUTORS,
                    "citation": D.DATASET_CITATION, "files": hashes},
        "companion_paper": {"citation": D.PAPER_CITATION, "doi": D.PAPER_DOI, "license": D.PAPER_LICENSE,
                            "use": "cited only; no text, tables, figures or reported coefficients reused"},
        "environment": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__},
        "n_participants": int(len(raw)),
        "n_columns": int(raw.shape[1]),
        "groups": {k: int(v) for k, v in g.value_counts().reindex(D.GROUP_ORDER).items()},
        "sex": {"women": int((raw["Sex"] == 1).sum()), "men": int((raw["Sex"] == 0).sum())},
        "age_range": r([raw["age"].min(), raw["age"].max()], 2),
        "id": {"unique": int(raw["ID"].nunique()), "min": int(raw["ID"].min()), "max": int(raw["ID"].max()),
               "absent_numbers": gaps},
        "audit": {
            "flags": {row.flag: {"severity": row.severity, "item": row.item} for row in flags.itertuples()},
            "main_flags": [f for f, s in zip(flags["flag"], flags["severity"]) if s == "main"],
            "height_unit": {k: r(v, 6) for k, v in bmi.items()},
            "readme_under_specified_columns": AU.README_UNDER_SPECIFIED,
            "consistency_checks": {row.check: [int(row.rows_flagged), int(row.rows_checked)] for row in cons.itertuples()},
            "deposited_files_modified": False,
        },
        "missingness": {
            "NDI_total": {"asymptomatic_missing": int(miss.set_index("column").loc["NDI_total", "missing_asymptomatic_of_42"]),
                          "chronic_neck_pain_missing": int(miss.set_index("column").loc["NDI_total", "missing_chronic_neck_pain_of_50"]),
                          "present": int(raw["NDI_total"].notna().sum())},
            "IPAQ_total_missing": int(raw["IPAQ_total"].isna().sum()),
            "IPAQ_categorized_missing": int(raw["IPAQ_categorized"].isna().sum()),
            "IPAQ_missing_by_group": {gg: int(raw.loc[g == gg, "IPAQ_total"].isna().sum()) for gg in D.GROUP_ORDER},
            "VAS_missing": int(raw["VAS_neck_0to100"].isna().sum()),
            "other_columns_complete": int((miss["missing_total_of_92"] == 0).sum()),
        },
        "primary_contrasts": {f"{row['position']}|{row['model']}": rec(row, ckeys, 6) for _, row in prim.iterrows()},
        "sensitivity_contrasts": {f"{row['position']}|{row['cva_source']}|{row['model']}": rec(row, ckeys, 6)
                                  for _, row in sens.iterrows()},
        "sex_bmi_associations": {f"{row['position']}|{row['term']}|{row['model']}": rec(row, ckeys[:-1], 6)
                                 for _, row in sexbmi.iterrows()},
        "symptom_associations": {f"{row['score']}|{row['position']}": {"n": int(row["n"]), **rec(row, [
            "estimate", "ci95_low", "ci95_high", "p", "r", "r_ci95_low", "r_ci95_high", "rho", "rho_ci95_low",
            "rho_ci95_high"], 6)} for _, row in symp.iterrows()},
        "sitting_vs_standing": {k: (r(v, 6) if not isinstance(v, int) else v) for k, v in sitstand.items()},
        "agreement": {row["position"]: {k: r(row[k], 6) for k in [
            "icc_a1", "icc_a1_ci95_low", "icc_a1_ci95_high", "icc_c1", "sem_degrees", "bias_e2_minus_e1",
            "bias_ci95_low", "bias_ci95_high", "sd_diff", "loa_low", "loa_high", "loa_low_ci95", "loa_high_ci95",
            "paired_t_p", "abs_diff_within_1_degree_pct", "abs_diff_within_2_degrees_pct", "max_abs_diff"]}
            for _, row in agr.iterrows()},
        "agreement_model": "ICC(A,1): two way random effects, absolute agreement, single measure "
                           "(McGraw and Wong 1996; Shrout and Fleiss ICC(2,1)), McGraw and Wong F based 95% CI",
        "figure_titles": dict(F.TITLES),
        "figure_footer": F.FOOTER,
        "outputs": {"tables": sorted(p.name for p in TABLES.glob("*.csv")),
                    "figures": sorted(p.name for p in made)},
    }
    (RES / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_results_md(ROOT / "RESULTS.md", summary, flags=flags, cons=cons, miss=miss, desc=desc, props=props,
                     prim=prim, sens=sens, sexbmi=sexbmi, symp=symp, agr=agr)
    log.append(f"tables {len(summary['outputs']['tables'])} figures {len(made)}")
    (RES / "run_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))


if __name__ == "__main__":
    main()
