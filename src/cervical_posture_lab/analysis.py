"""Pre-specified analyses. Fixed before any contrast was computed; locked by tests.

Primary family (Holm across these 4): chronic neck pain minus asymptomatic, OLS with HC3
standard errors, for the mean of the two evaluators in sitting and in standing, each
unadjusted and adjusted for age, sex and BMI.
Sensitivity (outside the primary family, own Holm): the same 8 models per single evaluator.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint

from . import data as D

ADJ = " + age + female + BMI"
PRIMARY = [
    ("sitting", "mean of evaluators", "CVA_sitting_mean", "unadjusted"),
    ("sitting", "mean of evaluators", "CVA_sitting_mean", "adjusted age, sex, BMI"),
    ("standing", "mean of evaluators", "CVA_standing_mean", "unadjusted"),
    ("standing", "mean of evaluators", "CVA_standing_mean", "adjusted age, sex, BMI"),
]
SENSITIVITY = [
    (pos, f"evaluator {k}", f"{pos.capitalize()}_Evaluator{k}", model)
    for pos in ("sitting", "standing") for k in (1, 2)
    for model in ("unadjusted", "adjusted age, sex, BMI")
]


def mean_ci(x) -> dict:
    x = pd.Series(x).dropna().astype(float)
    n = len(x)
    m, sd = x.mean(), x.std(ddof=1)
    h = stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n)
    return {"n": n, "mean": m, "sd": sd, "ci95_low": m - h, "ci95_high": m + h,
            "median": x.median(), "q1": x.quantile(0.25), "q3": x.quantile(0.75)}


def welch_diff(a, b) -> dict:
    a, b = pd.Series(a).dropna(), pd.Series(b).dropna()
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    se = np.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    d = a.mean() - b.mean()
    h = stats.t.ppf(0.975, df) * se
    return {"diff": d, "ci95_low": d - h, "ci95_high": d + h}


CONTINUOUS = ["age", "Weight", "HeightM", "BMI", "VAS_neck_0to100", "NDI_total", "IPAQ_total",
              "CVA_sitting_mean", "CVA_standing_mean"] + D.CVA_RAW
BINARY = {"female": "women", "NMQ_neck_lastyear": "NMQ neck pain last year: yes",
          "NMQ_neck_lastmonth": "NMQ neck pain last month: yes", "NMQ_neck_last7days": "NMQ neck pain last 7 days: yes",
          "NMQ_neck_today": "NMQ neck pain today: yes"}


def describe_by_group(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for v in CONTINUOUS:
        for g in D.GROUP_ORDER:
            s = mean_ci(df.loc[df["group"] == g, v])
            rows.append({"variable": v, "group": g, **s})
        a = df.loc[df["group"] == D.GROUP_ORDER[1], v]
        b = df.loc[df["group"] == D.GROUP_ORDER[0], v]
        if a.notna().sum() > 1 and b.notna().sum() > 1:
            w = welch_diff(a, b)
            rows.append({"variable": v, "group": "difference, pain minus asymptomatic (Welch)",
                         "n": int(a.notna().sum() + b.notna().sum()), "mean": w["diff"],
                         "ci95_low": w["ci95_low"], "ci95_high": w["ci95_high"]})
    return pd.DataFrame(rows)


def proportions_by_group(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    items = [(c, lab, df[c] == 1) for c, lab in BINARY.items()]
    for k, lab in [(1, "IPAQ low"), (2, "IPAQ moderate"), (3, "IPAQ high")]:
        items.append(("IPAQ_categorized", lab, df["IPAQ_categorized"] == k))
    for c, lab, hit in items:
        for g in D.GROUP_ORDER:
            m = (df["group"] == g) & df[c].notna()
            k, n = int(hit[m].sum()), int(m.sum())
            lo, hi = proportion_confint(k, n, method="wilson")
            rows.append({"variable": c, "category": lab, "group": g, "k": k, "n": n,
                         "pct": 100 * k / n, "ci95_low_pct": 100 * lo, "ci95_high_pct": 100 * hi})
    return pd.DataFrame(rows)


def ols(df: pd.DataFrame, formula: str):
    return smf.ols(formula, data=df).fit(cov_type="HC3")


def _term(fit, term: str) -> dict:
    lo, hi = fit.conf_int().loc[term]
    return {"estimate": float(fit.params[term]), "se_hc3": float(fit.bse[term]),
            "ci95_low": float(lo), "ci95_high": float(hi), "p": float(fit.pvalues[term]), "n": int(fit.nobs)}


def contrasts(df: pd.DataFrame, spec) -> pd.DataFrame:
    rows = []
    for pos, src, col, model in spec:
        f = f"{col} ~ neck_pain" + (ADJ if model != "unadjusted" else "")
        rows.append({"position": pos, "cva_source": src, "column": col, "model": model,
                     **_term(ols(df, f), "neck_pain")})
    out = pd.DataFrame(rows)
    out["p_holm"] = multipletests(out["p"], method="holm")[1]
    return out


def primary_contrasts(df):
    t = contrasts(df, PRIMARY)
    t["family"] = "primary (Holm across 4)"
    return t


def sensitivity_contrasts(df):
    t = contrasts(df, SENSITIVITY)
    t["family"] = "sensitivity, outside primary family (own Holm across 8)"
    return t


def sex_bmi_associations(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pos, col in D.CVA_MEAN.items():
        for model, f, terms in [
            ("unadjusted", f"{col} ~ female", ["female"]),
            ("unadjusted", f"{col} ~ BMI", ["BMI"]),
            ("mutually adjusted with age", f"{col} ~ female + BMI + age", ["female", "BMI"]),
        ]:
            fit = ols(df, f)
            for t in terms:
                rows.append({"position": pos, "term": "woman vs man" if t == "female" else "BMI per 1 kg/m2",
                             "model": model, **_term(fit, t)})
    return pd.DataFrame(rows)


def pearson_ci(x, y) -> dict:
    r, p = stats.pearsonr(x, y)
    n = len(x)
    z, se = np.arctanh(r), 1 / np.sqrt(n - 3)
    return {"r": float(r), "r_ci95_low": float(np.tanh(z - 1.96 * se)),
            "r_ci95_high": float(np.tanh(z + 1.96 * se)), "r_p": float(p)}


def spearman_ci(x, y) -> dict:
    rho, p = stats.spearmanr(x, y)
    n = len(x)
    se = np.sqrt((1 + rho ** 2 / 2) / (n - 3))  # Bonett and Wright (2000)
    z = np.arctanh(rho)
    return {"rho": float(rho), "rho_ci95_low": float(np.tanh(z - 1.96 * se)),
            "rho_ci95_high": float(np.tanh(z + 1.96 * se)), "rho_p": float(p)}


def symptom_associations(df: pd.DataFrame) -> pd.DataFrame:
    """Within chronic neck pain only, complete case. Slope in degrees per 10 score points."""
    cp = df[df["neck_pain"] == 1].copy()
    rows = []
    for score in ["VAS_neck_0to100", "NDI_total"]:
        for pos, col in D.CVA_MEAN.items():
            d = cp[[col, score]].dropna().copy()
            d["score10"] = d[score] / 10
            fit = ols(d, f"{col} ~ score10")
            rows.append({"score": score, "position": pos, "slope_unit": "degrees per 10 points",
                         **_term(fit, "score10"), **pearson_ci(d[score], d[col]), **spearman_ci(d[score], d[col])})
    return pd.DataFrame(rows)


def sitting_vs_standing(df: pd.DataFrame) -> dict:
    x, y = df["CVA_sitting_mean"], df["CVA_standing_mean"]
    d = y - x
    m = mean_ci(d)
    return {"n": int(len(x)), **pearson_ci(x, y), **spearman_ci(x, y),
            "mean_diff_standing_minus_sitting": float(m["mean"]),
            "diff_ci95_low": float(m["ci95_low"]), "diff_ci95_high": float(m["ci95_high"])}


def icc_a1(a, b) -> dict:
    """ICC(A,1) of McGraw and Wong (1996), equal to Shrout and Fleiss ICC(2,1): two way random
    effects, absolute agreement, single measure. 95% CI from the McGraw and Wong F method.
    Also returns ICC(C,1), two way, consistency, single measure, for context."""
    Y = np.column_stack([a, b]).astype(float)
    n, k = Y.shape
    gm = Y.mean()
    ssr = k * ((Y.mean(axis=1) - gm) ** 2).sum()
    ssc = n * ((Y.mean(axis=0) - gm) ** 2).sum()
    sst = ((Y - gm) ** 2).sum()
    sse = sst - ssr - ssc
    msr, msc, mse = ssr / (n - 1), ssc / (k - 1), sse / ((n - 1) * (k - 1))
    icc = (msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n)
    icc_c = (msr - mse) / (msr + (k - 1) * mse)
    aa = k * icc / (n * (1 - icc))
    bb = 1 + k * icc * (n - 1) / (n * (1 - icc))
    v = (aa * msc + bb * mse) ** 2 / ((aa * msc) ** 2 / (k - 1) + (bb * mse) ** 2 / ((n - 1) * (k - 1)))
    fl = stats.f.ppf(0.975, n - 1, v)
    fu = stats.f.ppf(0.975, v, n - 1)
    lo = n * (msr - fl * mse) / (fl * (k * msc + (k * n - k - n) * mse) + n * msr)
    hi = n * (fu * msr - mse) / (k * msc + (k * n - k - n) * mse + n * fu * msr)
    return {"icc_a1": float(icc), "icc_a1_ci95_low": float(lo), "icc_a1_ci95_high": float(hi),
            "icc_c1": float(icc_c), "sem_degrees": float(np.sqrt(mse))}


def bland_altman(a, b) -> dict:
    """Evaluator 2 minus evaluator 1. 95% limits of agreement with approximate CIs (Bland and Altman 1999)."""
    d = np.asarray(b, float) - np.asarray(a, float)
    n = len(d)
    m, sd = d.mean(), d.std(ddof=1)
    t = stats.t.ppf(0.975, n - 1)
    se_bias = sd / np.sqrt(n)
    se_loa = sd * np.sqrt(1 / n + 1.96 ** 2 / (2 * (n - 1)))
    lo, hi = m - 1.96 * sd, m + 1.96 * sd
    tt = stats.ttest_rel(b, a)
    return {"bias_e2_minus_e1": float(m), "bias_ci95_low": float(m - t * se_bias), "bias_ci95_high": float(m + t * se_bias),
            "sd_diff": float(sd), "loa_low": float(lo), "loa_high": float(hi),
            "loa_low_ci95": [float(lo - t * se_loa), float(lo + t * se_loa)],
            "loa_high_ci95": [float(hi - t * se_loa), float(hi + t * se_loa)],
            "paired_t_p": float(tt.pvalue),
            "abs_diff_within_1_degree_pct": float(100 * (np.abs(d) <= 1 + 1e-9).mean()),
            "abs_diff_within_2_degrees_pct": float(100 * (np.abs(d) <= 2 + 1e-9).mean()),
            "max_abs_diff": float(np.abs(d).max())}


def agreement(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pos in ("sitting", "standing"):
        a, b = df[f"{pos.capitalize()}_Evaluator1"], df[f"{pos.capitalize()}_Evaluator2"]
        rows.append({"position": pos, "n": int(len(a)), **icc_a1(a, b), **bland_altman(a, b)})
    return pd.DataFrame(rows)
