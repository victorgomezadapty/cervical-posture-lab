# Cervical Posture Lab

A transparent, reproducible re-analysis of one open Zenodo table of craniovertebral angle (CVA),
measured by two evaluators in sitting and standing, and neck pain scores in 92 young adults with
and without chronic neck pain.

**Status: public.** The analysis repository is public at
https://github.com/victorgomezadapty/cervical-posture-lab. Kaggle links will be added when they are live.

## About the name

The deposit's official title is *Forward Head Posture in individuals with and without chronic neck
pain* (Zenodo, DOI 10.5281/zenodo.17550555). "Cervical Posture Lab" is only this project's short
name (package `cervical_posture_lab`).

## What this project adds

This is not another run of the paper's group tests, regressions and ICCs. It adds four things
that are different from the deposit and the companion paper:

1. **Codebook audit.** The deposited SPSS file is checked against the deposited readme. Every
   mismatch is flagged and none is silently fixed: the Height label says cm while values and the
   readme are metres; the Standing_Evaluator2 label says evaluator 1; the readme variable list
   omits ID, ChronicNeckPain and VAS and gives one entry for four CVA columns; IDs have gaps.
2. **Missingness account.** NDI is present only in the chronic neck pain group (48 of 50, none of
   42 asymptomatic); IPAQ is missing in 14 rows (7 per group).
3. **Pre-specified contrasts** from the open table with 95% CIs and HC3 robust standard errors,
   unadjusted and adjusted for age, sex and BMI, Holm corrected across a fixed family of 4, with
   sensitivity to which evaluator is used versus the mean of both.
4. **Agreement of the two deposited evaluator columns**, ICC(A,1) and limits of agreement,
   labelled as agreement of deposited values, not a reconstruction of the paper's reliability protocol.

## What this project is not

* Not a new clinical study, and not clinical advice.
* Not a diagnostic or screening cutoff for forward head posture.
* Not a replication of the companion paper. Its results are not reproduced, compared or "beaten" here.
* Not a reuse of the paper's content. The paper (CC BY-NC 4.0) is cited only.

## From the deposit, inferred, added

| Item | Source |
|-|-|
| 92 rows, 19 columns, values, SPSS labels and value labels, readme text | Deposit |
| Height in metres (label says cm) | **Inferred** from values, readme and exact BMI identity |
| Standing_Evaluator2 is evaluator 2 (label says 1) | **Inferred** from the column name |
| Each CVA value is a mean of three readings | **Inferred** from values being multiples of 1/3 degree |
| Ethics approval, photogrammetry protocol, recruitment flow | As reported in the paper (cited, not reused) |
| Audit, missingness account, adjusted contrasts, evaluator sensitivity, agreement | Added by this project |

## Main results

All numbers are in [RESULTS.md](RESULTS.md) and `results/summary.json`.

* n = 92: 50 chronic neck pain, 42 asymptomatic; 62 women, 30 men; age 18.38 to 32.92 years.
* 4 main codebook flags (F1 to F4) and 4 minor notes (F5 to F8), none silently corrected. Read as
  cm, Height would give a BMI of about 177,557 to 408,163; read as metres it reproduces the
  deposited BMI exactly.
* Pre-specified CVA contrasts, chronic neck pain minus asymptomatic, mean of evaluators, degrees:
  sitting unadjusted -0.03 (95% CI -2.25 to 2.19), adjusted 0.29 (-1.82 to 2.39); standing
  unadjusted -0.73 (-2.72 to 1.25), adjusted -0.41 (-2.17 to 1.36). 0 of 4 pass Holm. Single
  evaluator estimates move by at most 0.14 degrees.
* Women and higher BMI go with smaller angles (sitting, mutually adjusted with age: woman vs man
  -2.43, -4.69 to -0.17; BMI -0.55 per kg/m2, -0.85 to -0.25).
* Within chronic neck pain, CVA shows no clear association with VAS (n 50) or NDI (n 48); all CIs include 0.
* Evaluator agreement of deposited values: ICC(A,1) 0.958 (0.933 to 0.974) sitting and 0.966
  (0.949 to 0.977) standing; limits of agreement -2.39 to 3.36 and -2.36 to 2.52 degrees.

## Project layout

| Path | Content |
|-|-|
| `data/raw/Database_Forward Head Posture and Neck Pain.sav` | Unmodified Zenodo file (CC BY 4.0), md5 and size checked on every load |
| `data/raw/readme_Dataset Forward Head Posture and Neck Pain.txt` | Unmodified Zenodo readme, md5 and size checked on every load |
| `src/cervical_posture_lab/` | `data` (load, checksums, labels), `audit`, `analysis`, `figures`, `report` |
| `scripts/run_analysis.py` | Regenerates `tables/`, `figures/`, `results/summary.json`, `RESULTS.md` |
| `scripts/fetch_data.py` | Tries Zenodo only if a file is missing; tolerates HTTP 403 |
| `tests/` | Integrity, audit, documentation and numeric lock tests |
| `tables/` | 13 CSV tables, aggregates only |
| `figures/` | 6 figures as PNG with WebP twins |
| `DATA_LICENSE.md`, `PROVENANCE.md`, `LICENSE` | Source, licenses, hashes, attribution and changes |

## How to run

Python 3.13.5 was used. From the project root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/run_analysis.py
.venv/bin/python -m pytest -q
```

Everything runs offline on the local copies in a few seconds. Zenodo often answers HTTP 403 to
automated traffic from the build machine, so the files were copied from a local license check
folder and are verified by md5 and size instead of being downloaded again.

## Methods in brief

* md5 and byte size of both files verified before every load; the analysis stops on mismatch.
* Unmodified .sav read with pyreadstat; Sex and ChronicNeckPain parsed with their value labels;
  derived columns (HeightM, CVA_sitting_mean, CVA_standing_mean) exist in memory only.
* Means with t based 95% CIs, Welch differences, Wilson CIs for proportions.
* Contrasts: OLS with HC3 robust standard errors; Holm across the 4 primary models; single
  evaluator models are a separate sensitivity family with their own Holm.
* Associations: OLS HC3 slopes, Pearson r (Fisher CI), Spearman rho (Bonett and Wright CI).
* Agreement: ICC(A,1), two way random effects, absolute agreement, single measure (McGraw and
  Wong; Shrout and Fleiss ICC(2,1)), F based 95% CI; Bland Altman bias and 95% limits of agreement.

## Limitations

A small single site sample of young adults, a group variable from one yes or no column, codebook
mismatches resolved by stated assumptions, NDI only in the pain group, undocumented missing IPAQ,
and no photographs to check landmarking. Null contrasts are not evidence of equivalence. Details
in [RESULTS.md](RESULTS.md#10-limitations).

## Data, citation and license

Data: Rodríguez-Romero, B., and Tunas-Maceiras, I. (2025). Forward Head Posture in individuals
with and without chronic neck pain [Dataset]. Zenodo. https://doi.org/10.5281/zenodo.17550555.
License CC BY 4.0. Dataset creators: Rodríguez-Romero, Beatriz and Tunas-Maceiras, Isabel.
Contributor (co-investigator in the readme, not a dataset creator): Ramos-Gómez, Fernando.

Companion paper (cite only, CC BY-NC 4.0): Tunas-Maceiras I, Ramos-Gómez F, Rodríguez-Romero B.
Assessment of forward head posture in individuals with and without chronic neck pain: A
cross-sectional study. Gait & Posture. 2026;125:110093. https://doi.org/10.1016/j.gaitpost.2026.110093.

This is the only data source. Code: MIT (`LICENSE`). Data and derived outputs: CC BY 4.0
(`DATA_LICENSE.md`). The creators do not endorse this re-analysis.
