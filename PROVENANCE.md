# Data provenance

| Field | Value |
|-|-|
| Source | Zenodo record 17550555 (https://zenodo.org/records/17550555) |
| Version DOI | 10.5281/zenodo.17550555 |
| Concept DOI | 10.5281/zenodo.17550554 |
| Title | Forward Head Posture in individuals with and without chronic neck pain |
| Version string | Final data from study "Assessment of forward head posture in individuals with and without chronic neck pain: a cross-sectional study" |
| Short name | "Cervical Posture Lab" is only this project's short name; it is not the deposit title |
| Creators | Rodríguez-Romero, Beatriz; Tunas-Maceiras, Isabel (University of A Coruña) |
| Contributor | Ramos-Gómez, Fernando (co-investigator in the readme, not a dataset creator) |
| Issued | 2025-11-20 |
| License | CC BY 4.0 (Zenodo license id `cc-by-4.0`, access `open`) |
| File 1 | `Database_Forward Head Posture and Neck Pain.sav`, 10039 bytes, md5 `e835bd09dea8ec8bfa73e91e69bac380` |
| File 2 | `readme_Dataset Forward Head Posture and Neck Pain.txt`, 5985 bytes, md5 `9b0c87e5f31e8d6fbba7bd43b924d072` |
| Content | 92 rows by 19 columns; SPSS labels and value labels; no photos or photogrammetry images |
| Identifiers | No names, dates, contact data or images of people. ID is a study code, 92 unique values from 1 to 103 with gaps |
| Ethics | As reported in the companion paper, which is cited and not reused. No ethics reference number is given in the deposit and none is stated here |
| Companion paper | Tunas-Maceiras I, Ramos-Gómez F, Rodríguez-Romero B. Gait & Posture 2026;125:110093. https://doi.org/10.1016/j.gaitpost.2026.110093. License CC BY-NC 4.0 |
| Not used | SSRN submitted version 10.2139/ssrn.5389438 (no clear reuse license) |

## How the local copy was made

The two files had been downloaded from Zenodo into a separate local license check folder. On
10 Nov 2026 they were copied (not moved) into `data/raw/` under their exact deposited names, and
the md5 and size were verified on both copies. Direct re-download from this machine is often
refused by Zenodo with HTTP 403; `scripts/fetch_data.py` tries only if a file is missing and
reports, rather than fails, when blocked. The files in `data/raw/` are never edited.

## Rules for this project

1. This Zenodo deposit is the only data source. Nothing else is merged or used as data. The paper
   is used only for attribution, for pointers to methods described only there, and to avoid false
   replication claims. No text, tables or figures from the paper are reproduced.
2. The md5 and size of both files are checked every time the data are loaded
   (`cervical_posture_lab.data.verify_raw`), in the analysis script and in the tests. The analysis
   stops if they do not match.
3. Outputs are aggregates. No row level data and no questionnaire wording are written to outputs.
4. Attribution as in `DATA_LICENSE.md` must accompany any reuse of the data or derived results.
5. Status: public. The analysis repository is public at https://github.com/victorgomezadapty/cervical-posture-lab. Kaggle links will be added when they are live.
