"""Exploratory analyses, registered in advance as exploratory and reported descriptively.

Four analyses, none of which carries a registered directional prediction:

* RQ2, grouping by model family or line;
* RQ3, the effect of scale within a family, over the four declared pairs;
* RQ4, the identity and stability of the most divergent voice;
* RQ5, the partition of variance between the model and case factors.

Uncertainty is assessed by cluster bootstrap over runs. The number of resamples
differs by analysis: 200 for RQ5, whose bootstrap refits the mixed model on each
resample, and 2000 for the other three, which resample summary statistics.

    python3 src/exploratory.py [--skip-rq5]
"""
import argparse
import itertools
import json
import statistics

import numpy as np
import pandas as pd

import paths
from confirmatory import variance_components

SEED = 20260723
N_BOOTSTRAP = 2000
N_BOOTSTRAP_MIXED = 200


def _percentile_ci(samples, level: float = 95.0) -> list:
    lower = (100.0 - level) / 2.0
    return [float(np.percentile(samples, lower)), float(np.percentile(samples, 100.0 - lower))]


def _run_keys(data: pd.DataFrame) -> np.ndarray:
    return data[["vignette_id", "run_id"]].drop_duplicates().to_numpy()


def rq2_family_grouping(data: pd.DataFrame, panel: pd.DataFrame, rng) -> dict:
    """Within-line versus between-line dispersion of mean dissent.

    Within-line dispersion is the mean absolute difference between the two
    members of each two-member line. Between-line dispersion is the mean absolute
    difference between the mean dissent of every pair of models drawn from
    different lines. The ratio below one is what a grouping effect looks like.
    """
    line_of = dict(zip(panel["model"], panel["line"]))

    # runs x models matrix of d_i, so a bootstrap resample of runs is a row
    # selection and the per-model means are one nanmean over the selected rows.
    wide = data.pivot_table(index=["vignette_id", "run_id"], columns="model", values="d_i")
    models = list(wide.columns)
    values = wide.to_numpy()

    two_member_lines = [line for line in {line_of[m] for m in models}
                        if sum(1 for m in models if line_of[m] == line) == 2]
    within_pairs = [[models.index(m) for m in models if line_of[m] == line]
                    for line in two_member_lines]
    between_pairs = [(i, j) for i, j in itertools.combinations(range(len(models)), 2)
                     if line_of[models[i]] != line_of[models[j]]]

    def statistics_for(rows: np.ndarray) -> tuple:
        means = np.nanmean(rows, axis=0)
        within = float(np.mean([abs(means[a] - means[b]) for a, b in within_pairs]))
        between = float(np.mean([abs(means[i] - means[j]) for i, j in between_pairs]))
        return within, between, means

    within, between, means = statistics_for(values)
    line_ranges = {line: float(abs(means[a] - means[b]))
                   for line, (a, b) in zip(two_member_lines, within_pairs)}

    ratios = []
    for _ in range(N_BOOTSTRAP):
        rows = values[rng.randint(0, len(values), len(values))]
        w, b, _ = statistics_for(rows)
        ratios.append(w / b)
    return {"within_line": within, "between_line": between, "ratio": within / between,
            "ratio_ci95": _percentile_ci(ratios), "line_ranges": line_ranges,
            "n_bootstrap": len(ratios)}


def rq3_scale_pairs(data: pd.DataFrame, panel: pd.DataFrame, rng) -> dict:
    """Paired within-family difference in dissent, large minus small, per pair."""
    results = {}
    pairs = panel[panel["scale_pair"].notna() & (panel["scale_pair"] != "")]
    for pair_name, members in pairs.groupby("scale_pair"):
        small = members[members["scale_role"] == "small"]["model"].iloc[0]
        large = members[members["scale_role"] == "large"]["model"].iloc[0]
        wide = (data[data["model"].isin([small, large])]
                .pivot_table(index=["vignette_id", "run_id"], columns="model", values="d_i")
                .dropna())
        differences = (wide[large] - wide[small]).to_numpy()
        means = [rng.choice(differences, differences.size, replace=True).mean()
                 for _ in range(N_BOOTSTRAP)]
        results[pair_name] = {
            "small": small, "large": large, "n_paired_runs": int(differences.size),
            "mean_small": float(wide[small].mean()), "mean_large": float(wide[large].mean()),
            "paired_diff_large_minus_small": float(differences.mean()),
            "ci95": _percentile_ci(means),
            "direction": "L>S" if differences.mean() > 0 else "S>L",
        }
    return results


def rq4_most_divergent_voice(data: pd.DataFrame, rng) -> dict:
    """How often each model is the most divergent voice of its run.

    Under interchangeability a model would hold the position in about 1/n of the
    runs it contributes to, so the counts are read against that expectation.
    """
    argmax = data.loc[data.groupby(["vignette_id", "run_id"])["d_i"].idxmax()]
    counts = argmax["model"].value_counts().to_dict()
    n_runs = data[["vignette_id", "run_id"]].drop_duplicates().shape[0]

    keys = _run_keys(data)
    winner = {(row.vignette_id, row.run_id): row.model for row in argmax.itertuples()}
    bootstrap: dict = {model: [] for model in counts}
    for _ in range(N_BOOTSTRAP):
        picked = keys[rng.randint(0, len(keys), len(keys))]
        tally: dict = {}
        for key in picked:
            model = winner[(key[0], int(key[1]))]
            tally[model] = tally.get(model, 0) + 1
        for model in bootstrap:
            bootstrap[model].append(tally.get(model, 0))

    modal_by_vignette = (argmax.groupby("vignette_id")["model"]
                         .agg(lambda s: s.value_counts().idxmax()).value_counts().to_dict())
    return {
        "n_runs": n_runs,
        "counts": counts,
        "share": {model: count / n_runs for model, count in counts.items()},
        "ci95": {model: [int(x) for x in _percentile_ci(values)]
                 for model, values in bootstrap.items()},
        "never_most_divergent": sorted(set(data["model"]) - set(counts)),
        "modal_by_vignette": modal_by_vignette,
    }


def rq5_variance_partition(data: pd.DataFrame, rng, n_bootstrap: int = N_BOOTSTRAP_MIXED) -> dict:
    """Variance partition coefficients, with a bootstrap that refits the model."""
    def partition(frame: pd.DataFrame) -> dict:
        components = variance_components(frame)
        total = (components["sigma2_model"] + components["sigma2_case"]
                 + components["sigma2_resid"])
        return {"vpc_model": components["sigma2_model"] / total,
                "vpc_case": components["sigma2_case"] / total,
                "vpc_resid": components["sigma2_resid"] / total,
                "ratio": components["sigma2_model"] / components["sigma2_case"]}

    point = partition(data)
    keys = _run_keys(data)
    indexed = data.set_index(["vignette_id", "run_id"]).sort_index()
    samples: dict = {key: [] for key in point}
    for _ in range(n_bootstrap):
        picked = keys[rng.randint(0, len(keys), len(keys))]
        resample = pd.concat([indexed.loc[[tuple(k)]] for k in picked]).reset_index()
        try:
            for key, value in partition(resample).items():
                samples[key].append(value)
        except Exception:
            continue
    return {"point": point,
            "ci95": {key: _percentile_ci(values) for key, values in samples.items() if values},
            "n_bootstrap": len(samples["vpc_model"])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-rq5", action="store_true",
                        help="skip the variance partition, whose bootstrap refits the model")
    args = parser.parse_args()

    data = pd.read_csv(paths.PER_MODEL_DISSENT)
    panel = pd.read_csv(paths.INDICES / "panel.csv")
    results = {"seed": SEED, "n_bootstrap": N_BOOTSTRAP}

    rng = np.random.RandomState(SEED)
    results["rq2_family"] = rq2_family_grouping(data, panel, rng)
    print(f"RQ2 within {results['rq2_family']['within_line']:.5f} | "
          f"between {results['rq2_family']['between_line']:.5f} | "
          f"ratio {results['rq2_family']['ratio']:.4f} "
          f"CI {results['rq2_family']['ratio_ci95']}")

    rng = np.random.RandomState(SEED)
    results["rq3_scale"] = rq3_scale_pairs(data, panel, rng)
    for pair, values in results["rq3_scale"].items():
        print(f"RQ3 {pair:12s} diff {values['paired_diff_large_minus_small']:+.4f} "
              f"CI [{values['ci95'][0]:+.4f}, {values['ci95'][1]:+.4f}] "
              f"n={values['n_paired_runs']} {values['direction']}")

    rng = np.random.RandomState(SEED)
    results["rq4_most_divergent"] = rq4_most_divergent_voice(data, rng)
    top = sorted(results["rq4_most_divergent"]["counts"].items(),
                 key=lambda kv: -kv[1])[:4]
    for model, count in top:
        share = results["rq4_most_divergent"]["share"][model]
        print(f"RQ4 {model:38s} {count:3d} ({share:.1%}) "
              f"CI {results['rq4_most_divergent']['ci95'][model]}")

    if not args.skip_rq5:
        rng = np.random.RandomState(SEED)
        results["rq5_variance"] = rq5_variance_partition(data, rng)
        point = results["rq5_variance"]["point"]
        print(f"RQ5 VPC model {point['vpc_model']:.4f} | case {point['vpc_case']:.4f} | "
              f"resid {point['vpc_resid']:.4f} | ratio {point['ratio']:.3f}")

    output = paths.ensure_results() / "exploratory.json"
    output.write_text(json.dumps(results, indent=1))
    print(f"written: {output.relative_to(paths.ROOT)}")


if __name__ == "__main__":
    main()
