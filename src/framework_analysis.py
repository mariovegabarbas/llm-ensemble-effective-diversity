"""Declared-framework analysis. Post-hoc, not preregistered.

Adds one instrument to the frozen artifacts: the therapeutic framework each model
declares in the first line of its formulation, recovered by
:mod:`framework_parser`. Deterministic given the data, so it uses no random seed.

Two analyses, both reported in S9 of the Supplementary Material:

* the conditioned partition, which asks whether the model-level structure in the
  dissent contribution is a record of which framework each model prefers, by
  entering framework agreement as a covariate in the two-way decomposition;
* the homogeneity partition, which asks whether the convergence itself follows
  from the closed menu, by comparing the effective voice count across runs that
  differ in how far their members agree on a framework.

They answer different questions and neither substitutes for the other.

Pre-declared threshold: a run is framework-homogeneous if its modal declared
framework is chosen by at least half of the run's valid mapped members. The
threshold was fixed before the effective voice count was tabulated by subset.

    python3 src/framework_analysis.py
"""
import json
import math
from collections import Counter, defaultdict

import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm

import framework_parser
import paths
from confirmatory import total_sum_of_squares

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


def framework_agreement(labels: pd.DataFrame) -> pd.DataFrame:
    """Per-voice covariate: the share of a run's OTHER members declaring its framework.

    The denominator is every other member of the run, not only those whose
    declaration could be mapped, and a voice whose own framework was not recovered
    scores zero. Stated because the alternative reading of the denominator shifts
    the conditioned eta squared in the fourth decimal.
    """
    rows = []
    for _, group in labels.groupby(["vignette_id", "run_id"]):
        for row in group.itertuples():
            others = group[group.model != row.model]
            same = (0 if row.declared_framework == framework_parser.FRAMEWORK_NOT_EXTRACTED
                    else int((others.declared_framework == row.declared_framework).sum()))
            rows.append({"vignette_id": row.vignette_id, "run_id": row.run_id,
                         "model": row.model,
                         "framework_agreement": same / len(others) if len(others) else 0.0})
    return pd.DataFrame(rows)


def conditioned_partition(dissent: pd.DataFrame) -> dict:
    """Two-way decomposition of d_i with and without the framework covariate.

    Effect sizes are classical eta squared, the effect's sum of squares over the
    total sum of squares of the response; see `total_sum_of_squares` for why the
    denominator is not the sum of the ANOVA table.
    """
    total = total_sum_of_squares(dissent)

    def eta2(formula: str) -> dict:
        table = anova_lm(smf.ols(formula, data=dissent).fit(), typ=2)
        return {term: float(table.loc[term, "sum_sq"] / total)
                for term in table.index if term != "Residual"}

    baseline = eta2("d_i ~ C(model) + C(vignette_id)")
    conditioned = eta2("d_i ~ C(model) + C(vignette_id) + framework_agreement")
    # Which factor the covariate belongs to: it is an attribute of the case, which
    # is why it overlaps mainly with the case factor rather than with the model.
    by_model = smf.ols("framework_agreement ~ C(model)", data=dissent).fit().rsquared
    by_case = smf.ols("framework_agreement ~ C(vignette_id)", data=dissent).fit().rsquared
    return {
        "total_sum_of_squares": total,
        "eta2_model": baseline["C(model)"],
        "eta2_model_conditioned": conditioned["C(model)"],
        "eta2_model_share_surviving": conditioned["C(model)"] / baseline["C(model)"],
        "eta2_case": baseline["C(vignette_id)"],
        "eta2_case_conditioned": conditioned["C(vignette_id)"],
        "eta2_covariate": conditioned["framework_agreement"],
        "covariate_variance_by_model": float(by_model),
        "covariate_variance_by_case": float(by_case),
    }


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

    dissent = pd.read_csv(paths.PER_MODEL_DISSENT).merge(
        framework_agreement(labels), on=["vignette_id", "run_id", "model"])
    partition = conditioned_partition(dissent)
    print(f"\nconditioned partition (SS_total = {partition['total_sum_of_squares']:.6f}):")
    print(f"  eta2 model  {partition['eta2_model']:.4f} -> "
          f"{partition['eta2_model_conditioned']:.4f}  "
          f"({100 * partition['eta2_model_share_surviving']:.1f}% survives)")
    print(f"  eta2 case   {partition['eta2_case']:.4f} -> "
          f"{partition['eta2_case_conditioned']:.4f}")
    print(f"  eta2 covariate                {partition['eta2_covariate']:.4f}")
    print(f"  covariate variance explained by model identity "
          f"{partition['covariate_variance_by_model']:.4f}, "
          f"by case identity {partition['covariate_variance_by_case']:.4f}")

    results = {
        "conditioned_partition": partition,
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
