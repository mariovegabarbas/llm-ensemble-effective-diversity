"""Length as a confound in the per-model dissent contribution. Post-hoc, not preregistered.

Normalising an embedding removes magnitude but not the direction correlated with
extension, so two formulations that say the same thing at very different lengths
can sit further apart in cosine similarity than two of similar length. This module
quantifies how much of the dissent contribution that accounts for.

Four questions, in the order that matters most for the manuscript's claims:

1. whether length differs across clinical pictures, since dissent does;
2. how a voice's departure from the length of its run relates to its d_i;
3. what happens to the model factor when that departure enters as a covariate;
4. whether the models that most often hold the most-divergent position are
   atypical in length.

On (3) the answer is not a single number. The covariate is close to a function of
model identity, which accounts for 78% of its variance, so conditioning on it is
partly conditioning on the factor being measured and the estimate depends on the
order in which terms enter. The range is reported rather than a point value.

Length is measured in whitespace-delimited words. That is the unit the frozen
validity criteria already use, it is comparable across models, and it does not
depend on a tokeniser. Characters and provider-reported completion tokens are
computed alongside as a sensitivity; tokens are the weakest of the three here,
because each provider tokenises differently and a token count would confound
verbosity with tokeniser, which is the model-level artefact under investigation.

Deterministic: no resampling, no seed.

    python3 src/length_analysis.py
"""
import itertools
import json

import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm

import paths
from confirmatory import total_sum_of_squares

METRICS = ("words", "chars", "tokens")


def load() -> pd.DataFrame:
    """Join the dissent contributions with the length of each formulation."""
    records = []
    with paths.FORMULATIONS_JSONL.open() as handle:
        for line in handle:
            record = json.loads(line)
            if record["status"] != "analysed":
                continue
            text = record["text"]
            records.append({
                "vignette_id": record["vignette_id"], "run_id": record["run_id"],
                "model": record["model"], "words": len(text.split()),
                "chars": len(text), "tokens": record["completion_tokens"],
            })
    data = (pd.read_csv(paths.PER_MODEL_DISSENT)
              .merge(pd.DataFrame(records), on=["vignette_id", "run_id", "model"])
              .merge(pd.read_csv(paths.VIGNETTE_STRATA), on="vignette_id"))
    for metric in METRICS:
        grouped = data.groupby(["vignette_id", "run_id"])[metric]
        n = grouped.transform("count")
        others = (grouped.transform("sum") - data[metric]) / (n - 1)
        data[f"deviation_{metric}"] = data[metric] - others
        data[f"absolute_deviation_{metric}"] = data[f"deviation_{metric}"].abs()
    return data


def by_clinical_picture(data: pd.DataFrame) -> dict:
    """Does length track the clinical picture, as dissent does?"""
    indices = pd.read_csv(paths.ENSEMBLE_INDICES).merge(
        pd.read_csv(paths.VIGNETTE_STRATA), on="vignette_id")
    n_eff = indices.groupby("clinical_picture")["n_eff"].mean()
    table = data.groupby("clinical_picture").agg(
        mean_words=("words", "mean"), sd_words=("words", "std"),
        mean_chars=("chars", "mean"), mean_tokens=("tokens", "mean"))
    table["n_eff"] = n_eff
    spread = float(table.mean_words.max() - table.mean_words.min())
    return {
        "table": table,
        "spread_words": spread,
        "spread_as_share_of_shortest": spread / float(table.mean_words.min()),
        "mean_within_picture_sd": float(table.sd_words.mean()),
        "dispersion_ratio": float(table.sd_words.mean() / spread),
    }


def deviation_versus_dissent(data: pd.DataFrame) -> dict:
    """Correlation of d_i with the departure from the length of the run."""
    out = {}
    for metric in METRICS:
        for kind in ("deviation", "absolute_deviation"):
            column = f"{kind}_{metric}"
            out[column] = {
                "pearson": float(data[column].corr(data["d_i"])),
                "spearman": float(data[column].corr(data["d_i"], method="spearman")),
            }
    out["r_squared_linear"] = float(
        smf.ols("d_i ~ absolute_deviation_words", data=data).fit().rsquared)
    return out


def covariate_estimates(data: pd.DataFrame) -> dict:
    """The model factor's eta squared under every ordering of the terms.

    Sequential sums of squares are obtained by differencing the residual sum of
    squares of nested fits, not by asking for type I, because the formula parser
    reorders terms and would silently return the same decomposition either way.
    """
    total = total_sum_of_squares(data)
    covariate = "absolute_deviation_words"
    model, case = "C(model)", "C(vignette_id)"

    def residual(terms):
        return float(smf.ols("d_i ~ " + " + ".join(terms), data=data).fit().ssr)

    def sequential(order):
        previous, parts = total, {}
        for index in range(len(order)):
            current = residual(order[:index + 1])
            parts[order[index]] = (previous - current) / total
            previous = current
        return parts

    def partial(formula, typ, term):
        table = anova_lm(smf.ols(formula, data=data).fit(), typ=typ)
        return float(table.loc[term, "sum_sq"] / total)

    baseline_sequential = sequential([model, case])[model]
    baseline_partial = partial(f"d_i ~ {model} + {case}", 2, model)
    estimates = {
        "type I, covariate last": (sequential([model, case, covariate])[model],
                                   baseline_sequential),
        "type I, covariate first": (sequential([covariate, model, case])[model],
                                    baseline_sequential),
        "type II": (partial(f"d_i ~ {model} + {case} + {covariate}", 2, model),
                    baseline_partial),
        "type III": (partial(f"d_i ~ C(model, Sum) + C(vignette_id, Sum) + {covariate}",
                             3, "C(model, Sum)"),
                     partial("d_i ~ C(model, Sum) + C(vignette_id, Sum)", 3, "C(model, Sum)")),
    }
    shares = {k: 100 * with_it / without for k, (with_it, without) in estimates.items()}
    return {
        "total_sum_of_squares": total,
        "estimates": {k: {"eta2_with_covariate": w, "eta2_without": o,
                          "share_surviving_pct": shares[k]}
                      for k, (w, o) in estimates.items()},
        "share_surviving_range_pct": [min(shares.values()), max(shares.values())],
        "covariate_variance_by_model": float(
            smf.ols(f"{covariate} ~ C(model)", data=data).fit().rsquared),
        "covariate_variance_by_case": float(
            smf.ols(f"{covariate} ~ C(vignette_id)", data=data).fit().rsquared),
    }


def by_model(data: pd.DataFrame) -> pd.DataFrame:
    """Mean length per model against how often it is the most divergent voice."""
    argmax = data.loc[data.groupby(["vignette_id", "run_id"])["d_i"].idxmax()]
    counts = argmax["model"].value_counts()
    table = data.groupby("model").agg(
        mean_words=("words", "mean"), sd_words=("words", "std"),
        mean_absolute_deviation=("absolute_deviation_words", "mean"),
        mean_d_i=("d_i", "mean"))
    table["most_divergent"] = counts.reindex(table.index).fillna(0).astype(int)
    table["deviation_from_panel"] = table.mean_words - data.words.mean()
    return table.sort_values("most_divergent", ascending=False)


def main() -> None:
    data = load()
    print(f"formulations: {len(data)}\n")

    picture = by_clinical_picture(data)
    print("length by clinical picture")
    print(picture["table"].sort_values("n_eff").to_string(float_format=lambda x: f"{x:,.1f}"))
    print(f"  spread {picture['spread_words']:.1f} words, "
          f"{100 * picture['spread_as_share_of_shortest']:.1f}% of the shortest; "
          f"within-picture sd is {picture['dispersion_ratio']:.1f} times that spread")

    deviation = deviation_versus_dissent(data)
    print("\ncorrelation with d_i")
    for metric in METRICS:
        signed = deviation[f"deviation_{metric}"]["pearson"]
        absolute = deviation[f"absolute_deviation_{metric}"]["pearson"]
        print(f"  {metric:7s} signed {signed:+.4f}   absolute {absolute:+.4f}")
    print(f"  R^2 of d_i on absolute word deviation: {deviation['r_squared_linear']:.4f}")

    covariate = covariate_estimates(data)
    print("\nmodel factor with the length covariate")
    for label, values in covariate["estimates"].items():
        print(f"  {label:26s} eta2 {values['eta2_with_covariate']:.4f} of "
              f"{values['eta2_without']:.4f}  ->  {values['share_surviving_pct']:5.1f}% survives")
    low, high = covariate["share_surviving_range_pct"]
    print(f"  range {low:.1f}% to {high:.1f}%")
    print(f"  covariate variance explained by model identity "
          f"{covariate['covariate_variance_by_model']:.4f}, "
          f"by case identity {covariate['covariate_variance_by_case']:.4f}")

    models = by_model(data)
    print("\nlength by model, ordered by occupancy of the most-divergent position")
    print(f"  {'model':38s} {'words':>8s} {'vs panel':>9s} {'|dev|':>7s} {'argmax':>7s}")
    for name, row in models.iterrows():
        print(f"  {name:38s} {row.mean_words:8.1f} {row.deviation_from_panel:+9.1f} "
              f"{row.mean_absolute_deviation:7.1f} {int(row.most_divergent):7d}")

    results = {
        "posthoc": True, "preregistered": False,
        "by_clinical_picture": {
            "spread_words": picture["spread_words"],
            "spread_as_share_of_shortest": picture["spread_as_share_of_shortest"],
            "dispersion_ratio": picture["dispersion_ratio"],
            "table": picture["table"].to_dict(orient="index"),
        },
        "deviation_versus_dissent": deviation,
        "covariate_estimates": covariate,
        "by_model": models.to_dict(orient="index"),
    }
    output = paths.ensure_results() / "length_analysis.json"
    output.write_text(json.dumps(results, indent=1))
    models.to_csv(paths.ensure_results() / "length_by_model.csv")
    print(f"\nwritten: {output.relative_to(paths.ROOT)}")


if __name__ == "__main__":
    main()
