# llm-ensemble-effective-diversity

Analysis code and data for a study of how much distinct perspective an ensemble
of language models actually produces on an interpretive clinical task, and of
what structures that quantity.

Sixteen language models from ten families each wrote a psychotherapeutic case
formulation for fifteen stratified clinical vignettes, under counterbalanced
presentation of a ten-framework menu, giving 450 ensemble runs and 7,082
formulations for analysis. The panel behaved on average as the equivalent of
**1.69** distinct formulations, against a single-model baseline of **1.43**
obtained by resampling one model's own runs.

> **The manuscript is in preparation.** Links to the published article and its
> DOI are not yet available, and their absence is expected rather than a broken
> reference. This repository is released so the analysis can be read and rerun
> alongside the preprint.

## The measure is the Vendi Score, and this is not a reimplementation of it

The effective number of voices reported here **is** the Vendi Score, the
exponential of the von Neumann entropy of a normalised similarity matrix
(Friedman and Dieng, 2022). This repository does not reimplement it: `src/dissent.py`
calls the authors' reference implementation, the
[`vendi-score`](https://github.com/vertaix/Vendi-Score) package, and depends on it.

What is original here is the per-voice decomposition, the dissent contribution
`d_i` of each ensemble member, defined as one minus its mean similarity to the
other members of its run. Its maximum identifies the most divergent voice. Note
that `d_i` does **not** decompose the spectral index: it is a different
functional of the same Gram matrix. Its mean recovers the mean pairwise dissent
of the ensemble, which is `n/(n-1)` times the internal diversity the reference
implementation computes over all `n²` entries.

> Friedman, D., and Dieng, A. B. (2022). The Vendi Score: A Diversity Evaluation
> Metric for Machine Learning. *arXiv*:2210.02410.

## Preregistration

The hypothesis, the measure, the panel composition and the analysis plan were
registered publicly before any data were generated:

**<https://osf.io/c5qk7>**

> The registration is under embargo until **September 2027** and will not resolve
> publicly before that date.

`docs/deviations_from_preregistration.md` records the departures adopted before
any data were generated, and the reconciliation of the manuscript title with the
registered one. `docs/validity_criteria.md` records the mechanical criteria that
decide whether a formulation is degenerate; they were frozen in writing before
being applied, blind to the dissent measure and to model identity.

## Layout

```
src/                  analysis code
  dissent.py            the measurement apparatus (Vendi Score + per-voice decomposition)
  framework_parser.py   recovers the therapeutic framework each formulation declares
  confirmatory.py       H1: the between-model variance component
  exploratory.py        RQ2 family, RQ3 scale, RQ4 most divergent voice, RQ5 variance partition
  framework_analysis.py declared-framework analysis (post-hoc)
  openness_analysis.py  dissent by interpretive-openness stratum (post-hoc)
  export_data.py        builds data/ from the internal run directory (provenance, not reproduction)
  paths.py              every path, derived from the repository root
data/                 published data, schema in data/SCHEMA.md
  indices/              per-run indices, per-model dissent, exclusions, strata, panel
  formulations/         the 7,200 formulations obtained, as JSONL
docs/                 validity criteria, deviations, field mapping
figures/              figure generator and its output
```

## Reproducing the results

Python 3.10 or later.

```sh
pip install -r requirements.txt

python3 src/confirmatory.py          # H1; the full permutation test takes a while
python3 src/exploratory.py           # RQ2-RQ5
python3 src/framework_analysis.py    # post-hoc, declared framework
python3 src/openness_analysis.py     # post-hoc, openness stratum
python3 figures/make_figures.py      # after exploratory.py
```

Results are written to `results/`. Every script reads only from `data/` and
resolves its paths relative to the repository root, so a fresh clone runs without
editing anything. Set `CDI_DATA_ROOT` to read the data from elsewhere.

`src/confirmatory.py` runs the registered 99,999 permutations by default; pass
`--permutations` a smaller number for a quick check. `src/exploratory.py` accepts
`--skip-rq5` to skip the variance partition, whose bootstrap refits the mixed
model 200 times.

Seeds are fixed: 20260722 for the confirmatory permutation test, 20260723 for the
exploratory bootstraps.

### Recomputing the indices from scratch

The published indices were computed from `text-embedding-3-large` embeddings of
the formulations. Those embeddings are not published; `data/formulations/` holds
the texts they were computed from, so they can be regenerated. `src/dissent.py`
takes any embedding matrix and returns the same quantities.

## Licences

| What | Licence |
|---|---|
| Everything under `src/` and `figures/` | Apache License 2.0 — see [`LICENSE`](LICENSE) |
| Everything under `data/` and `docs/` | Creative Commons Attribution 4.0 — see [`LICENSE-DATA`](LICENSE-DATA) |

The `vendi-score` dependency is MIT-licensed and is not vendored here.

## The vignette bank is not included

The fifteen clinical vignettes are not part of this repository. They are held in
a restricted deposit, a condition set by their clinical authorship, and are
available on reasoned request:

**<https://doi.org/10.5281/zenodo.21708455>**

What is published instead is `data/indices/vignette_strata.csv`, the two design
labels of each vignette, so that the stratified analyses can be reproduced
without the clinical material. The formulations the models wrote **are**
published in full.

## Citing this work

See [`CITATION.cff`](CITATION.cff). Until the article appears, cite the
repository and the preregistration.
