"""Integrity, audit, documentation and numeric lock tests for Cervical Posture Lab."""
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cervical_posture_lab import analysis as A  # noqa: E402
from cervical_posture_lab import audit as AU  # noqa: E402
from cervical_posture_lab import data as D  # noqa: E402

DOCS = ["README.md", "RESULTS.md", "DATA_LICENSE.md", "PROVENANCE.md", "LICENSE"]
FORBIDDEN_DASHES = ["\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2015", "\u2212", "--"]
FORBIDDEN_NAMES = ["optimo", "malqa", "riyadh"]
# Questionnaire or screening wording that must never appear in outputs (taken from the SPSS labels).
INSTRUMENT_SNIPPETS = ["have you experienced", "even if intermittent", "has lasted for more than 3 months",
                       "in the past year?", "neck pain today?"]


@pytest.fixture(scope="module")
def loaded():
    return D.load_raw()


@pytest.fixture(scope="module")
def raw(loaded):
    return loaded[0]


@pytest.fixture(scope="module")
def meta(loaded):
    return loaded[1]


@pytest.fixture(scope="module")
def df(raw, meta):
    return D.prepare(raw, meta)


@pytest.fixture(scope="module")
def summary():
    return json.loads((ROOT / "results" / "summary.json").read_text(encoding="utf-8"))


def text(name):
    return (ROOT / name).read_text(encoding="utf-8")


def output_texts():
    files = [ROOT / n for n in DOCS] + sorted((ROOT / "tables").glob("*.csv")) + [ROOT / "results" / "summary.json"]
    return {p.name: p.read_text(encoding="utf-8") for p in files}


# Integrity

def test_file_names_hashes_and_sizes():
    assert D.SAV_PATH.name == "Database_Forward Head Posture and Neck Pain.sav"
    assert D.README_PATH.name == "readme_Dataset Forward Head Posture and Neck Pain.txt"
    assert D.SAV_PATH.stat().st_size == 10039
    assert D.README_PATH.stat().st_size == 5985
    assert D.md5sum(D.SAV_PATH) == "e835bd09dea8ec8bfa73e91e69bac380"
    assert D.md5sum(D.README_PATH) == "9b0c87e5f31e8d6fbba7bd43b924d072"
    assert sorted(p.name for p in D.RAW_DIR.iterdir()) == sorted(D.EXPECTED)


def test_verify_aborts_on_changed_file(tmp_path, monkeypatch):
    bad = tmp_path / "raw"
    shutil.copytree(D.RAW_DIR, bad)
    with open(bad / D.SAV_NAME, "ab") as fh:
        fh.write(b"x")
    monkeypatch.setattr(D, "RAW_DIR", bad)
    with pytest.raises(ValueError):
        D.verify_raw()


def test_shape_ids_and_no_identifiers(raw):
    assert raw.shape == (92, 19)
    ids = raw["ID"].astype(int)
    assert ids.nunique() == 92 and ids.min() == 1 and ids.max() == 103
    assert sorted(ids) != list(range(1, 93))
    assert D.identifier_like_columns(raw.columns) == []


def test_groups_and_sex(df, raw):
    assert df["group"].value_counts().to_dict() == {"chronic neck pain": 50, "asymptomatic": 42}
    assert (raw["Sex"] == 1).sum() == 62 and (raw["Sex"] == 0).sum() == 30
    assert (df["sex_label"] == "woman").sum() == 62
    assert 18.37 < raw["age"].min() < 18.39 and 32.91 < raw["age"].max() < 32.93


def test_value_labels_parsed(meta):
    assert meta.variable_value_labels["Sex"] == {0.0: "man", 1.0: "woman"}
    assert meta.variable_value_labels["ChronicNeckPain"] == {0.0: "No", 1.0: "Sí"}


def test_derived_columns_in_memory_only(raw, df):
    assert list(df.columns[:19]) == list(raw.columns)
    assert np.allclose(df["CVA_sitting_mean"], (raw["Sitting_Evaluator1"] + raw["Sitting_Evaluator2"]) / 2)
    assert (df["HeightM"] == raw["Height"]).all()
    assert D.md5sum(D.SAV_PATH) == D.EXPECTED[D.SAV_NAME]["md5"]


# Codebook flags

def test_height_is_metres_bmi_identity(raw):
    assert raw["Height"].min() == pytest.approx(1.50) and raw["Height"].max() == pytest.approx(1.92)
    assert np.allclose(raw["BMI"], raw["Weight"] / raw["Height"] ** 2, atol=1e-9)
    as_cm = raw["Weight"] / (raw["Height"] / 100) ** 2
    assert as_cm.min() > 100_000  # incompatible with the deposited BMI


def test_flag_height_label(meta):
    assert meta.column_names_to_labels["Height"] == "Height (cm)"
    assert "Height (m)" in D.load_readme()


def test_flag_standing_evaluator2_label(meta):
    assert "evaluator 1" in meta.column_names_to_labels["Standing_Evaluator2"]
    assert "evaluator 2" in meta.column_names_to_labels["Sitting_Evaluator2"]


def test_flag_readme_incomplete():
    rd = D.load_readme()
    var_list = rd.split("VARIABLE LIST:")[1].split("ABBREVIATIONS")[0]
    for missing in ["ID", "VAS", "Chronic", "Evaluator", "Sitting", "Standing"]:
        assert missing.lower() not in var_list.lower(), missing
    assert "CVA (grades)" in var_list
    assert "Number of variables: 19" in rd


def test_flag_id_gaps(raw):
    assert AU.id_gaps(raw) == [16, 58, 60, 61, 63, 66, 67, 68, 69, 84, 102]


def test_four_main_flags_documented(raw, meta, summary):
    f = AU.flags(raw, meta, D.load_readme())
    assert list(f.loc[f.severity == "main", "flag"]) == ["F1", "F2", "F3", "F4"]
    assert summary["audit"]["main_flags"] == ["F1", "F2", "F3", "F4"]
    assert summary["audit"]["deposited_files_modified"] is False
    res = text("RESULTS.md")
    for item in ["Height unit", "Standing_Evaluator2 label", "Readme variable list incomplete", "ID gaps"]:
        assert item in res


# Missingness

def test_ndi_missingness(raw):
    g0, g1 = raw["ChronicNeckPain"] == 0, raw["ChronicNeckPain"] == 1
    assert raw.loc[g0, "NDI_total"].isna().sum() == 42
    assert raw.loc[g1, "NDI_total"].isna().sum() == 2
    assert raw["NDI_total"].notna().sum() == 48


def test_ipaq_and_vas_missingness(raw):
    assert raw["IPAQ_total"].isna().sum() == 14
    assert raw["IPAQ_categorized"].isna().sum() == 14
    assert (raw["IPAQ_total"].isna() == raw["IPAQ_categorized"].isna()).all()
    assert raw["VAS_neck_0to100"].isna().sum() == 0
    g0 = raw["ChronicNeckPain"] == 0
    assert raw.loc[g0, "IPAQ_total"].isna().sum() == 7


# Documentation, names, status, credit

def test_title_and_short_name():
    rd = text("README.md")
    assert rd.startswith("# Cervical Posture Lab")
    assert "Forward Head Posture in individuals with and without chronic neck" in rd
    assert '"Cervical Posture Lab" is only this project\'s short' in rd
    assert D.DATASET_TITLE == "Forward Head Posture in individuals with and without chronic neck pain"
    assert "is only the project short name" in text("RESULTS.md")


def test_status_public():
    rd = text("README.md")
    kaggle_dataset = "https://www.kaggle.com/datasets/vctorandrsgmezlpez/forward-head-posture-with-and-without-neck-pain"
    kaggle_notebook = "https://www.kaggle.com/code/vctorandrsgmezlpez/cervical-posture-lab-cva-neck-pain-re-analysis"
    assert "**Status: public.**" in rd
    assert "https://github.com/victorgomezadapty/cervical-posture-lab" in rd
    assert kaggle_dataset in rd
    assert kaggle_notebook in rd
    assert "will be added when they are live" not in rd.lower()
    assert {u.rstrip(".,);") for u in re.findall(r"https://www\.kaggle\.com/\S+", rd)} == {kaggle_dataset, kaggle_notebook}
    prov = text("PROVENANCE.md")
    assert "https://github.com/victorgomezadapty/cervical-posture-lab" in prov
    assert kaggle_dataset in prov
    assert kaggle_notebook in prov
    assert "will be added when they are live" not in prov.lower()
    assert {u.rstrip(".,);") for u in re.findall(r"https://www\.kaggle\.com/\S+", prov)} == {kaggle_dataset, kaggle_notebook}
    res = text("RESULTS.md")
    assert "**Status: public.**" in res
    assert "https://github.com/victorgomezadapty/cervical-posture-lab" in res
    assert "kaggle.com" not in res.lower()


def test_paper_cited_only():
    for name in ["README.md", "RESULTS.md", "DATA_LICENSE.md"]:
        t = text(name)
        assert "10.1016/j.gaitpost.2026.110093" in t, name
        assert "CC BY-NC 4.0" in t, name
        assert "cited only" in t.lower() or "cite only" in t.lower(), name
    assert "ssrn" not in text("README.md").lower()
    assert "is not used" in text("DATA_LICENSE.md")


def test_creators_vs_contributor(summary):
    assert summary["dataset"]["creators"] == ["Rodríguez-Romero, Beatriz", "Tunas-Maceiras, Isabel"]
    assert summary["dataset"]["contributors"] == ["Ramos-Gómez, Fernando"]
    cit = "Rodríguez-Romero, B., and Tunas-Maceiras, I. (2025). Forward Head Posture"
    assert cit in text("RESULTS.md") and cit in D.DATASET_CITATION
    assert "Ramos" not in D.DATASET_CITATION
    for name in ["README.md", "DATA_LICENSE.md", "PROVENANCE.md"]:
        assert re.search(r"not (as )?a dataset creator", text(name)), name


def test_licenses():
    assert "Copyright (c) 2026 Víctor Andrés Gómez López" in text("LICENSE")
    assert "MIT License" in text("LICENSE")
    dl = text("DATA_LICENSE.md")
    assert "CC BY 4.0" in dl and "https://creativecommons.org/licenses/by/4.0/" in dl


def test_what_this_adds_is_explicit():
    for name in ["README.md", "RESULTS.md"]:
        t = text(name)
        assert "## What this project adds" in t, name
        assert "not another run of the paper's group tests, regressions and ICCs" in t.replace("\n", " "), name
        assert "not a reconstruction of the paper's reliability protocol" in t.replace("\n", " "), name


def test_no_typographic_dashes(summary):
    for name, t in output_texts().items():
        if name == "LICENSE":
            continue
        for d in FORBIDDEN_DASHES:
            assert d not in t, (name, repr(d))
    for title in summary["figure_titles"].values():
        assert not any(d in title for d in FORBIDDEN_DASHES), title
    assert not any(d in summary["figure_footer"] for d in FORBIDDEN_DASHES)
    csv_headers = [p.read_text(encoding="utf-8").splitlines()[0] for p in (ROOT / "tables").glob("*.csv")]
    for h in csv_headers:
        assert "-" not in h, h


def test_no_forbidden_names_or_keys():
    blobs = list(output_texts().values()) + [p.read_text(encoding="utf-8") for p in
                                             list((ROOT / "src").rglob("*.py")) + list((ROOT / "scripts").glob("*.py"))]
    for t in blobs:
        low = t.lower()
        for n in FORBIDDEN_NAMES:
            assert n not in low, n
        assert not re.search(r"(sk|ghp|xox[bp])[-_][A-Za-z0-9]{16,}", t)


def test_no_questionnaire_text():
    for name, t in output_texts().items():
        low = t.lower()
        for s in INSTRUMENT_SNIPPETS:
            assert s not in low, (name, s)


def test_no_photos_or_extra_data():
    files = [p for p in ROOT.rglob("*") if ".venv" not in p.parts and p.is_file()]
    assert not [p for p in files if p.suffix.lower() in {".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".heic"}]
    imgs = [p for p in files if p.suffix in {".png", ".webp"}]
    assert all(p.parent.name == "figures" for p in imgs)


def test_figures_png_and_webp_twins(summary):
    pngs = sorted((ROOT / "figures").glob("*.png"))
    assert len(pngs) == 6
    for p in pngs:
        assert p.with_suffix(".webp").exists()
    assert set(summary["figure_titles"]) == {p.name for p in pngs}
    foot = summary["figure_footer"]
    assert foot.endswith("Public re-analysis.")
    assert "CC BY 4.0" in foot and "10.5281/zenodo.17550555" in foot and "Rodríguez-Romero" in foot


# Numeric locks (recomputed from the deposited file)

def test_primary_contrasts_locked(df, summary):
    p = A.primary_contrasts(df).set_index(["position", "model"])
    exp = {
        ("sitting", "unadjusted"): (-0.0263, -2.2476, 2.1949),
        ("sitting", "adjusted age, sex, BMI"): (0.2874, -1.8151, 2.3900),
        ("standing", "unadjusted"): (-0.7343, -2.7192, 1.2506),
        ("standing", "adjusted age, sex, BMI"): (-0.4063, -2.1743, 1.3617),
    }
    for k, (est, lo, hi) in exp.items():
        r = p.loc[k]
        assert r["estimate"] == pytest.approx(est, abs=1e-3)
        assert r["ci95_low"] == pytest.approx(lo, abs=1e-3)
        assert r["ci95_high"] == pytest.approx(hi, abs=1e-3)
        assert summary["primary_contrasts"][f"{k[0]}|{k[1]}"]["estimate"] == pytest.approx(est, abs=1e-3)
    assert (p["p_holm"] >= 0.05).all()
    assert len(p) == 4


def test_sensitivity_outside_family(df):
    s = A.sensitivity_contrasts(df)
    assert len(s) == 8 and s["family"].str.contains("outside primary family").all()
    assert (s["p"] > 0.05).all()


def test_sex_bmi_locked(df):
    t = A.sex_bmi_associations(df).set_index(["position", "term", "model"])
    assert t.loc[("sitting", "woman vs man", "mutually adjusted with age"), "estimate"] == pytest.approx(-2.4346, abs=1e-3)
    assert t.loc[("sitting", "BMI per 1 kg/m2", "mutually adjusted with age"), "estimate"] == pytest.approx(-0.5495, abs=1e-3)
    assert t.loc[("standing", "BMI per 1 kg/m2", "unadjusted"), "estimate"] == pytest.approx(-0.5619, abs=1e-3)


def test_symptoms_locked(df):
    t = A.symptom_associations(df).set_index(["score", "position"])
    assert t.loc[("NDI_total", "sitting"), "n"] == 48
    assert t.loc[("VAS_neck_0to100", "sitting"), "n"] == 50
    assert t.loc[("NDI_total", "sitting"), "r"] == pytest.approx(-0.1178, abs=1e-3)
    assert ((t["ci95_low"] < 0) & (t["ci95_high"] > 0)).all()


def test_sitting_standing_locked(df):
    s = A.sitting_vs_standing(df)
    assert s["r"] == pytest.approx(0.8270, abs=1e-3)
    assert s["mean_diff_standing_minus_sitting"] == pytest.approx(0.9565, abs=1e-3)


def test_agreement_locked(df, summary):
    a = A.agreement(df).set_index("position")
    assert a.loc["sitting", "icc_a1"] == pytest.approx(0.9585, abs=5e-4)
    assert a.loc["sitting", "icc_a1_ci95_low"] == pytest.approx(0.9329, abs=5e-4)
    assert a.loc["sitting", "icc_a1_ci95_high"] == pytest.approx(0.9737, abs=5e-4)
    assert a.loc["standing", "icc_a1"] == pytest.approx(0.9659, abs=5e-4)
    assert a.loc["sitting", "loa_low"] == pytest.approx(-2.3900, abs=1e-3)
    assert a.loc["sitting", "loa_high"] == pytest.approx(3.3610, abs=1e-3)
    assert a.loc["standing", "loa_low"] == pytest.approx(-2.3598, abs=1e-3)
    assert a.loc["standing", "loa_high"] == pytest.approx(2.5192, abs=1e-3)
    assert a.loc["sitting", "bias_e2_minus_e1"] == pytest.approx(0.4855, abs=1e-3)
    assert "absolute agreement, single measure" in summary["agreement_model"]


def test_icc_formula_on_known_case():
    # perfect agreement gives ICC 1; a constant offset lowers absolute agreement but not consistency
    x = np.array([40.0, 45, 50, 55, 60, 52, 47])
    noise = np.array([0.1, -0.1, 0.05, -0.05, 0.1, -0.1, 0.0])
    assert A.icc_a1(x, x + noise)["icc_a1"] > 0.999
    off = A.icc_a1(x, x + noise + 3)
    assert off["icc_c1"] > 0.999 and off["icc_a1"] < 0.95
    assert off["icc_a1_ci95_low"] < off["icc_a1"] < off["icc_a1_ci95_high"]


def test_readme_numbers_match_summary(summary):
    rd = re.sub(r"\s+", " ", text("README.md"))
    pc = summary["primary_contrasts"]
    for k in pc:
        v = pc[k]
        assert f"{v['estimate']:.2f}" in rd and f"{v['ci95_low']:.2f} to {v['ci95_high']:.2f}" in rd, k
    ag = summary["agreement"]
    for pos in ("sitting", "standing"):
        assert f"{ag[pos]['icc_a1']:.3f} ({ag[pos]['icc_a1_ci95_low']:.3f} to {ag[pos]['icc_a1_ci95_high']:.3f})" in rd
        assert f"{ag[pos]['loa_low']:.2f} to {ag[pos]['loa_high']:.2f}" in rd


def test_results_regenerated_consistently(summary):
    assert summary["n_participants"] == 92 and summary["n_columns"] == 19
    assert summary["status"] == "public"
    assert summary["missingness"]["NDI_total"] == {"asymptomatic_missing": 42, "chronic_neck_pain_missing": 2, "present": 48}
    assert summary["missingness"]["IPAQ_total_missing"] == 14
    assert len(summary["outputs"]["tables"]) == 13
