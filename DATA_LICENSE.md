# Data license and attribution

## Data

The only data used in this project is the following Zenodo deposit:

> Rodríguez-Romero, B., and Tunas-Maceiras, I. (2025). Forward Head Posture in individuals with and
> without chronic neck pain [Dataset]. Zenodo. https://doi.org/10.5281/zenodo.17550555

* Dataset creators (official DataCite and Zenodo order): Rodríguez-Romero, Beatriz; Tunas-Maceiras, Isabel.
* Contributor: Ramos-Gómez, Fernando, listed as co-investigator in the deposited readme. He is
  credited here as a contributor, not as a dataset creator. (The readme's own citation line names
  three people; this project follows the official two creator citation, see audit flag F6.)
* License: Creative Commons Attribution 4.0 International (CC BY 4.0),
  https://creativecommons.org/licenses/by/4.0/ (Zenodo license id `cc-by-4.0`, access `open`).
* Files, unmodified copies of the Zenodo files:
  * `data/raw/Database_Forward Head Posture and Neck Pain.sav` (10039 bytes, md5 `e835bd09dea8ec8bfa73e91e69bac380`)
  * `data/raw/readme_Dataset Forward Head Posture and Neck Pain.txt` (5985 bytes, md5 `9b0c87e5f31e8d6fbba7bd43b924d072`)
* The tables in `tables/`, figures in `figures/`, `results/summary.json` and `RESULTS.md` are
  derived from this dataset and are shared under the same CC BY 4.0 terms with the attribution above.

### Changes made (CC BY 4.0 section 3(a)(1)(B))

* No change to either deposited file. Both stay byte identical and are hash checked on every load.
* In memory only: Height read as metres (`HeightM`) although the SPSS label says cm (flag F1);
  Standing_Evaluator2 taken as evaluator 2 although its label says evaluator 1 (flag F2); the four
  angle columns read as craniovertebral angle although the SPSS labels say craniocervical (flag F5);
  means of the two evaluators added as `CVA_sitting_mean` and `CVA_standing_mean`.
* Aggregation and statistical modelling. No rows were added, removed or edited.
* Questionnaire and screening question wording from the SPSS labels is not reproduced; only the
  deposited scores are analysed. No questionnaire instrument is republished.

The creators and the licensor do not endorse this project or its interpretation.

## Related article (different license)

> Tunas-Maceiras I, Ramos-Gómez F, Rodríguez-Romero B. Assessment of forward head posture in
> individuals with and without chronic neck pain: A cross-sectional study. Gait & Posture.
> 2026;125:110093. https://doi.org/10.1016/j.gaitpost.2026.110093

The article is licensed CC BY-NC 4.0 (Copyright 2026 The Authors, published by Elsevier B.V.),
which differs from the dataset license. It is cited only. No text, tables, figures, highlights or
reported coefficients from it are reproduced here, and it is not a data source. A submitted
version on SSRN (10.2139/ssrn.5389438) has no clear reuse license and is not used.

## Code

The code in this project is licensed under the MIT License (see `LICENSE`), copyright 2026
Víctor Andrés Gómez López. The MIT license does not apply to the data or derived results.

## No other data

No other dataset is used, merged or referenced as input. Adding another source would require a
new license review first.
