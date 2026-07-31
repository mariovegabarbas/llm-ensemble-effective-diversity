"""Dissent by interpretive-openness stratum. Post-hoc, not preregistered.

The vignette bank is stratified on two crossed dimensions, the clinical picture
and the interpretive openness of the case. The openness dimension affords a check
on what the index registers: a measure of dissent among readings would be
expected to return more dissent on the cases built to admit several.

Descriptive only. No hypothesis test is performed and no inferential claim is
made: fifteen vignettes split 6 / 2 / 7 do not support inference.

Two bootstrap levels are reported for every contrast. Resampling runs ignores the
nesting of thirty runs inside each vignette and is the optimistic one; resampling
vignettes, the unit the stratification applies to, is reported alongside.

    python3 src/openness_analysis.py
"""
import json
import statistics
from collections import defaultdict

import numpy as np
import pandas as pd

import paths

SEED = 20260723
N_BOOTSTRAP = 2000
REFERENCE_STRATUM = "genuinely_distinct"
#: Declared in Methods; the script stops if the data disagree.
DECLARED_SPLIT = {"shared_frame_ineffective": 6, "shared_frame_effective": 2,
                  "genuinely_distinct": 7}


def _describe(values) -> dict:
    values = list(values)
    return {"n": len(values), "mean": statistics.mean(values),
            "sd": statistics.stdev(values), "min": min(values), "max": max(values)}


def _bootstrap_difference(a, b, rng, by_vignette=False) -> dict:
    """Percentile CI of mean(a) - mean(b), resampling runs or whole vignettes."""
    if by_vignette:
        groups_a = [np.array(v) for v in a.values()]
        groups_b = [np.array(v) for v in b.values()]
        differences = np.empty(N_BOOTSTRAP)
        for i in range(N_BOOTSTRAP):
            sample_a = np.concatenate([groups_a[j] for j in
                                       rng.randint(0, len(groups_a), len(groups_a))])
            sample_b = np.concatenate([groups_b[j] for j in
                                       rng.randint(0, len(groups_b), len(groups_b))])
            differences[i] = sample_a.mean() - sample_b.mean()
        observed = np.concatenate(groups_a).mean() - np.concatenate(groups_b).mean()
    else:
        a, b = np.asarray(a), np.asarray(b)
        differences = np.empty(N_BOOTSTRAP)
        for i in range(N_BOOTSTRAP):
            differences[i] = (rng.choice(a, a.size, replace=True).mean()
                              - rng.choice(b, b.size, replace=True).mean())
        observed = a.mean() - b.mean()
    return {"difference": float(observed),
            "ci95": [float(np.percentile(differences, 2.5)),
                     float(np.percentile(differences, 97.5))]}


def _grouped(frame: pd.DataFrame, column: str) -> dict:
    grouped = defaultdict(list)
    for row in frame.itertuples():
        grouped[row.vignette_id].append(getattr(row, column))
    return dict(grouped)


def main() -> None:
    strata = pd.read_csv(paths.VIGNETTE_STRATA)
    observed_split = strata["openness_stratum"].value_counts().to_dict()
    if observed_split != DECLARED_SPLIT:
        raise SystemExit(f"openness split is {observed_split}, Methods declares {DECLARED_SPLIT}")
    print(f"openness split matches Methods: {observed_split}")

    data = pd.read_csv(paths.ENSEMBLE_INDICES).merge(strata, on="vignette_id")
    results = {"posthoc": True, "preregistered": False, "seed": SEED,
               "n_bootstrap": N_BOOTSTRAP, "split": observed_split,
               "by_stratum": {}, "by_clinical_picture": {}, "contrasts": {},
               "contrasts_by_vignette": {}, "within_picture": {}}

    for stratum, group in data.groupby("openness_stratum"):
        results["by_stratum"][stratum] = {
            "n_vignettes": group["vignette_id"].nunique(), "n_runs": len(group),
            "n_eff": _describe(group["n_eff"]), "s_norm": _describe(group["s_norm"])}
        print(f"{stratum:26s} vignettes={group['vignette_id'].nunique()} "
              f"runs={len(group):3d} n_eff={group['n_eff'].mean():.4f} "
              f"s_norm={group['s_norm'].mean():.4f}")

    for picture, group in data.groupby("clinical_picture"):
        results["by_clinical_picture"][picture] = {
            "n_vignettes": group["vignette_id"].nunique(), "n_runs": len(group),
            "n_eff": _describe(group["n_eff"]), "s_norm": _describe(group["s_norm"])}

    rng = np.random.RandomState(SEED)
    reference = data[data["openness_stratum"] == REFERENCE_STRATUM]
    for other in ("shared_frame_ineffective", "shared_frame_effective"):
        comparison = data[data["openness_stratum"] == other]
        for column in ("n_eff", "s_norm"):
            key = f"{REFERENCE_STRATUM}_minus_{other}|{column}"
            results["contrasts"][key] = _bootstrap_difference(
                reference[column], comparison[column], rng)
    for other in ("shared_frame_ineffective", "shared_frame_effective"):
        comparison = data[data["openness_stratum"] == other]
        for column in ("n_eff", "s_norm"):
            key = f"{REFERENCE_STRATUM}_minus_{other}|{column}"
            results["contrasts_by_vignette"][key] = _bootstrap_difference(
                _grouped(reference, column), _grouped(comparison, column), rng,
                by_vignette=True)

    print("\ncontrasts (reference stratum minus the other):")
    for key, value in results["contrasts"].items():
        vignette_ci = results["contrasts_by_vignette"][key]["ci95"]
        print(f"  {key:56s} {value['difference']:+.4f} "
              f"runs CI [{value['ci95'][0]:+.4f}, {value['ci95'][1]:+.4f}] "
              f"vignettes CI [{vignette_ci[0]:+.4f}, {vignette_ci[1]:+.4f}]")

    # The marginal contrast, recomputed inside each clinical picture and averaged
    # with equal weight. A tabulation, not a model.
    for column in ("n_eff", "s_norm"):
        differences = {}
        for picture in sorted(data["clinical_picture"].unique()):
            subset = data[data["clinical_picture"] == picture]
            a = subset[subset["openness_stratum"] == REFERENCE_STRATUM][column]
            b = subset[subset["openness_stratum"] == "shared_frame_ineffective"][column]
            if len(a) and len(b):
                differences[picture] = float(a.mean() - b.mean())
        results["within_picture"][column] = {
            "per_picture": differences,
            "equal_weight_mean": statistics.mean(differences.values())}
        print(f"within-picture {column}: " +
              "  ".join(f"{k}={v:+.4f}" for k, v in differences.items()) +
              f"   equal-weight mean {results['within_picture'][column]['equal_weight_mean']:+.4f}")

    print("\nCaveat: the shared_frame_effective stratum has two vignettes. Every quantity "
          "involving it rests on those two cases and supports no comparison.")

    output = paths.ensure_results() / "openness_analysis.json"
    output.write_text(json.dumps(results, indent=1))
    print(f"written: {output.relative_to(paths.ROOT)}")


if __name__ == "__main__":
    main()
