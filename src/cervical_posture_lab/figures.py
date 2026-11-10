"""Figures, all computed in this project. Each PNG gets a WebP twin. No paper figures are copied."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402

from . import data as D  # noqa: E402

plt.rcParams.update({
    "axes.unicode_minus": False,
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})
COLORS = {"asymptomatic": "#4C72B0", "chronic neck pain": "#C44E52"}
FOOTER = f"Data: {D.SHORT_CITATION}, CC BY 4.0. Public re-analysis."
TITLES: dict[str, str] = {}  # file name to title text, checked by tests


def _save(fig, path: Path, title: str) -> list[Path]:
    TITLES[path.name] = title
    fig.canvas.draw()
    bottom = fig.get_tightbbox(fig.canvas.get_renderer()).y0 / fig.get_figheight()
    fig.text(0.01, bottom - 0.015, FOOTER, fontsize=7, color="#555555", ha="left", va="top")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    webp = path.with_suffix(".webp")
    Image.open(path).save(webp, "WEBP", quality=90, method=6)
    return [path, webp]


def fig_audit(raw: pd.DataFrame, flags: pd.DataFrame, gaps: list[int], path: Path):
    title = "Codebook audit: mismatches flagged, none silently corrected"
    fig = plt.figure(figsize=(13, 4.8))
    gs = fig.add_gridspec(2, 3, height_ratios=[3, 1], width_ratios=[1, 1, 1.5])
    ax = fig.add_subplot(gs[0, 0])
    pred = raw["Weight"] / raw["Height"] ** 2
    ax.scatter(pred, raw["BMI"], s=10, color="#333333")
    lim = [16, 42]
    ax.plot(lim, lim, color="#999999", lw=0.8)
    ax.set_xlabel("weight / height^2, height read as metres")
    ax.set_ylabel("deposited BMI")
    ax.set_title("F1: label says cm, values are metres", fontsize=9)
    ax.text(0.03, 0.97, "exact match with metres\nread as cm, BMI would be\nabout 180,000 to 410,000",
            transform=ax.transAxes, va="top", fontsize=8)
    ax = fig.add_subplot(gs[0, 1])
    ax.hist(raw["NDI_total"].dropna(), bins=np.arange(0, 44, 2), color="#C44E52", alpha=0.85)
    ax.set_xlabel("NDI_total as deposited")
    ax.set_ylabel("participants")
    g1, g0 = raw["ChronicNeckPain"] == 1, raw["ChronicNeckPain"] == 0
    ax.set_title(f"NDI present in {int(raw.loc[g1, 'NDI_total'].notna().sum())} of {int(g1.sum())} pain rows, "
                 f"\n{int(raw.loc[g0, 'NDI_total'].notna().sum())} of {int(g0.sum())} asymptomatic rows", fontsize=9)
    ax = fig.add_subplot(gs[0, 2])
    ax.axis("off")
    lines = [f"{r.flag} ({r.severity}): {r.item}" for r in flags.itertuples()]
    ax.text(0, 1, "Flags (deposited files unchanged)\n\n" + "\n".join(lines), va="top", fontsize=8.5,
            family="DejaVu Sans")
    ax.text(0, 0.18, "F2: label of Standing_Evaluator2 says evaluator 1\n"
            "F3: readme omits ID, ChronicNeckPain and VAS,\n      and gives one CVA entry for four columns",
            va="top", fontsize=8, color="#555555")
    ax = fig.add_subplot(gs[1, :])
    present = set(raw["ID"].astype(int))
    xs = np.arange(1, int(raw["ID"].max()) + 1)
    ax.bar(xs, [1] * len(xs), width=0.9, color=["#888888" if x in present else "#E8A33D" for x in xs])
    ax.set_yticks([])
    ax.set_xlim(0, xs.max() + 1)
    ax.set_xlabel(f"study ID 1 to {xs.max()}: grey present (92), orange absent ({len(gaps)})")
    ax.set_title("F4: ID is a study code with gaps", fontsize=9)
    fig.suptitle(title, fontsize=11, y=1.02)
    fig.subplots_adjust(hspace=0.8, wspace=0.45)
    return _save(fig, path, title)


def fig_missingness(miss: pd.DataFrame, path: Path):
    title = "Missing values by group: NDI present only in the pain group, IPAQ missing in 14 rows"
    m = miss[miss["missing_total_of_92"] > 0]
    fig, ax = plt.subplots(figsize=(7, 3))
    y = np.arange(len(m))
    ax.barh(y - 0.18, m["missing_asymptomatic_of_42"], 0.36, color=COLORS["asymptomatic"], label="asymptomatic (n 42)")
    ax.barh(y + 0.18, m["missing_chronic_neck_pain_of_50"], 0.36, color=COLORS["chronic neck pain"],
            label="chronic neck pain (n 50)")
    for yi, (a, b) in enumerate(zip(m["missing_asymptomatic_of_42"], m["missing_chronic_neck_pain_of_50"])):
        ax.text(a + 0.5, yi - 0.18, str(a), va="center", fontsize=8)
        ax.text(b + 0.5, yi + 0.18, str(b), va="center", fontsize=8)
    ax.set_yticks(y, m["column"])
    ax.invert_yaxis()
    ax.set_xlabel(f"missing values (the other {int((miss['missing_total_of_92'] == 0).sum())} columns are complete)")
    ax.set_title(title, fontsize=9.5)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    return _save(fig, path, title)


def fig_cva_by_group(df: pd.DataFrame, path: Path):
    title = "CVA by group, mean of the two deposited evaluators (this re-analysis)"
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.8), sharey=True)
    for ax, (pos, col) in zip(axes, D.CVA_MEAN.items()):
        data = [df.loc[df["group"] == g, col] for g in D.GROUP_ORDER]
        ax.boxplot(data, widths=0.5, showfliers=False)
        for i, (g, y) in enumerate(zip(D.GROUP_ORDER, data), start=1):
            ax.scatter(np.full(len(y), i) + np.random.default_rng(i).uniform(-0.17, 0.17, len(y)), y,
                       s=9, alpha=0.6, color=COLORS[g])
            ax.text(i, 66, f"mean {y.mean():.1f}", ha="center", fontsize=8)
        ax.set_xticks([1, 2], [f"{g}\nn {len(y)}" for g, y in zip(D.GROUP_ORDER, data)], fontsize=8)
        ax.set_title(pos, fontsize=10)
        ax.set_ylim(34, 68)
    axes[0].set_ylabel("craniovertebral angle, degrees\n(higher is more upright)")
    fig.suptitle(title, fontsize=10, y=1.02)
    return _save(fig, path, title)


def fig_forest(prim: pd.DataFrame, sens: pd.DataFrame, path: Path):
    title = "Chronic neck pain minus asymptomatic, CVA in degrees (OLS, HC3, 95% CI)"
    rows = []
    for pos in ("sitting", "standing"):
        for model in ("unadjusted", "adjusted age, sex, BMI"):
            r = prim[(prim.position == pos) & (prim.model == model)].iloc[0]
            rows.append((f"{pos}, mean of evaluators, {model}", r, True))
            for k in (1, 2):
                r = sens[(sens.position == pos) & (sens.model == model) & (sens.cva_source == f"evaluator {k}")].iloc[0]
                rows.append((f"    evaluator {k} only", r, False))
    fig, ax = plt.subplots(figsize=(8, 5.2))
    for i, (lab, r, primary) in enumerate(rows):
        c = "#333333" if primary else "#999999"
        ax.errorbar(r["estimate"], i, xerr=[[r["estimate"] - r["ci95_low"]], [r["ci95_high"] - r["estimate"]]],
                    fmt="o" if primary else "s", ms=5 if primary else 3.5, color=c, mfc=c if primary else "white")
    ax.axvline(0, color="#333333", lw=0.8)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("difference in CVA, degrees (negative: more forward head in the pain group)")
    ax.set_title(title + "\nblack: primary family, Holm across 4; grey: single evaluator sensitivity", fontsize=9.5)
    return _save(fig, path, title)


def fig_agreement(df: pd.DataFrame, agr: pd.DataFrame, path: Path):
    title = "Agreement of the two deposited evaluator columns (not a reconstruction of the paper's protocol)"
    fig, axes = plt.subplots(2, 2, figsize=(9.5, 7))
    for j, pos in enumerate(("sitting", "standing")):
        a = df[f"{pos.capitalize()}_Evaluator1"]
        b = df[f"{pos.capitalize()}_Evaluator2"]
        r = agr[agr.position == pos].iloc[0]
        ax = axes[0, j]
        ax.scatter(a, b, s=10, color="#333333", alpha=0.7)
        ax.plot([35, 65], [35, 65], color="#999999", lw=0.8)
        ax.set_xlabel("evaluator 1, degrees")
        ax.set_ylabel("evaluator 2, degrees")
        ax.set_title(f"{pos}: ICC(A,1) {r['icc_a1']:.3f} ({r['icc_a1_ci95_low']:.3f} to {r['icc_a1_ci95_high']:.3f})",
                     fontsize=9)
        ax = axes[1, j]
        mean, diff = (a + b) / 2, b - a
        ax.scatter(mean, diff, s=10, color="#333333", alpha=0.7)
        for v, ls in [(r["bias_e2_minus_e1"], "-"), (r["loa_low"], "--"), (r["loa_high"], "--")]:
            ax.axhline(v, color="#C44E52", lw=0.9, ls=ls)
        ax.axhline(0, color="#999999", lw=0.6)
        ax.set_xlabel("mean of evaluators, degrees")
        ax.set_ylabel("evaluator 2 minus evaluator 1")
        ax.set_title(f"bias {r['bias_e2_minus_e1']:.2f}, limits {r['loa_low']:.2f} to {r['loa_high']:.2f} degrees",
                     fontsize=9)
    fig.suptitle(title, fontsize=10, y=1.0)
    fig.tight_layout()
    return _save(fig, path, title)


def fig_symptoms(df: pd.DataFrame, path: Path):
    title = "Within chronic neck pain: CVA (mean of evaluators) against VAS and NDI, complete case"
    cp = df[df["neck_pain"] == 1]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.8), sharey=True)
    for ax, score, lab in [(axes[0], "VAS_neck_0to100", "VAS, deposited score"),
                           (axes[1], "NDI_total", "NDI, deposited score")]:
        for pos, col, c in [("sitting", "CVA_sitting_mean", "#4C72B0"), ("standing", "CVA_standing_mean", "#DD8452")]:
            d = cp[[score, col]].dropna()
            ax.scatter(d[score], d[col], s=10, alpha=0.7, color=c, label=f"{pos} (n {len(d)})")
            b = np.polyfit(d[score], d[col], 1)
            xs = np.linspace(d[score].min(), d[score].max(), 10)
            ax.plot(xs, np.polyval(b, xs), color=c, lw=1)
        ax.set_xlabel(lab)
        ax.legend(frameon=False, fontsize=8)
    axes[0].set_ylabel("CVA, degrees")
    fig.suptitle(title, fontsize=10, y=1.02)
    return _save(fig, path, title)
