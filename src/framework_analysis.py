"""Declared-framework analysis. Post-hoc, not preregistered.

Adds one instrument to the frozen artifacts: the therapeutic framework each model
declares in the first line of its formulation, recovered by
:mod:`framework_parser`. Deterministic given the data, so it uses no random seed.

Pre-declared threshold: a run is framework-homogeneous if its modal declared
framework is chosen by at least half of the run's valid mapped members. The
threshold was fixed before the effective voice count was tabulated by subset.

    python3 src/framework_analysis.py
"""
import json
import math
from collections import Counter, defaultdict

import pandas as pd

import framework_parser
import paths

HOMOGENEOUS_THRESHOLD = 0.50


def label_formulations() -> pd.DataFrame:
    """Parse the declared framework of every analysed formulation."""
    records = []
    with paths.FORMULATIONS_JSONL.open() as handle:
        for line in handle:
            record = json.loads(line)
            if record["status"] != "analysed":
                continue
            records.append({
                "vignette_id": record["vignette_id"],
                "run_id": record["run_id"],
                "model": record["model"],
                "declared_framework": framework_parser.parse(record["text"])["framework"],
            })
    return pd.DataFrame(records)


def modal_share_per_run(labels: pd.DataFrame) -> pd.DataFrame:
    """Share of a run's mapped members that declare the run's modal framework."""
    rows = []
    for (vignette, run), group in labels.groupby(["vignette_id", "run_id"]):
        mapped = [f for f in group["declared_framework"]
                  if f != framework_parser.FRAMEWORK_NOT_EXTRACTED]
        counts = Counter(mapped)
        modal, modal_count = counts.most_common(1)[0]
        proportions = [count / len(mapped) for count in counts.values()]
        rows.append({
            "vignette_id": vignette, "run_id": run,
            "n_mapped": len(mapped), "modal_framework": modal,
            "modal_share": modal_count / len(mapped),
            "distinct_frameworks": len(counts),
            "framework_entropy": -sum(p * math.log2(p) for p in proportions),
        })
    return pd.DataFrame(rows)


def main() -> None:
    labels = label_formulations()
    print(f"formulations labelled: {len(labels)}")

    distribution = labels["declared_framework"].value_counts()
    print("declared framework, panel-wide:")
    for framework, count in distribution.items():
        print(f"  {count:5d}  {framework}")

    per_run = modal_share_per_run(labels)
    indices = pd.read_csv(paths.ENSEMBLE_INDICES)
    merged = per_run.merge(indices, on=["vignette_id", "run_id"])

    homogeneous = merged[merged["modal_share"] >= HOMOGENEOUS_THRESHOLD]
    heterogeneous = merged[merged["modal_share"] < HOMOGENEOUS_THRESHOLD]
    gap = homogeneous["n_eff"].mean() - heterogeneous["n_eff"].mean()

    print(f"\nmodal share: mean {merged['modal_share'].mean():.3f}, "
          f"median {merged['modal_share'].median():.3f}, "
          f"range [{merged['modal_share'].min():.3f}, {merged['modal_share'].max():.3f}]")
    print(f"framework-homogeneous runs (share >= {HOMOGENEOUS_THRESHOLD}): "
          f"n={len(homogeneous)}, mean n_eff {homogeneous['n_eff'].mean():.4f}")
    print(f"framework-heterogeneous runs: n={len(heterogeneous)}, "
          f"mean n_eff {heterogeneous['n_eff'].mean():.4f}")
    print(f"difference: {gap:+.4f} effective voices")
    correlation = merged["modal_share"].corr(merged["n_eff"])
    print(f"corr(modal share, n_eff) = {correlation:.4f}")

    results = {
        "posthoc": True, "preregistered": False,
        "n_formulations": len(labels),
        "framework_distribution": distribution.to_dict(),
        "modal_share": {
            "mean": float(merged["modal_share"].mean()),
            "median": float(merged["modal_share"].median()),
            "min": float(merged["modal_share"].min()),
            "max": float(merged["modal_share"].max()),
        },
        "homogeneous_threshold": HOMOGENEOUS_THRESHOLD,
        "n_eff_homogeneous": float(homogeneous["n_eff"].mean()),
        "n_eff_heterogeneous": float(heterogeneous["n_eff"].mean()),
        "n_eff_gap": float(gap),
        "corr_modal_share_n_eff": float(correlation),
    }
    output = paths.ensure_results() / "framework_analysis.json"
    output.write_text(json.dumps(results, indent=1, ensure_ascii=False))
    per_run.to_csv(paths.ensure_results() / "framework_per_run.csv", index=False)
    print(f"written: {output.relative_to(paths.ROOT)}")


if __name__ == "__main__":
    main()
