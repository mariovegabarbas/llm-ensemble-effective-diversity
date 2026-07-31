"""Confirmatory analysis: H1, the between-model variance component of dissent.

The single preregistered hypothesis is that model identity accounts for a
non-zero share of the variance in the per-model dissent contribution.

Three quantities, in the registered order:

1. a cross-classified mixed model of ``d_i`` with model and case as crossed
   random effects, fitted by REML, giving the variance components;
2. the registered decision criterion, a Monte Carlo permutation test in which
   model labels are permuted within cases; the statistic is the sum of squares
   of the model factor in a two-way ANOVA on the case-centred response;
3. a fixed-effects two-way ANOVA as the registered sensitivity analysis.

    python3 src/confirmatory.py
"""
import argparse
import json

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm

import paths

PERMUTATION_SEED = 20260722
N_PERMUTATIONS = 99999


def load_dissent() -> pd.DataFrame:
    return pd.read_csv(paths.PER_MODEL_DISSENT)


def variance_components(data: pd.DataFrame) -> dict:
    """Cross-classified mixed model, REML, model and case as random effects."""
    frame = data.copy()
    frame["group"] = 1  # single group; both factors enter as variance components
    model = smf.mixedlm(
        "d_i ~ 1", frame, groups=frame["group"],
        vc_formula={"model": "0 + C(model)", "case": "0 + C(vignette_id)"},
    )
    fit = model.fit(reml=True)
    # statsmodels orders the variance components by name, not by the order they
    # were declared in; map them back explicitly rather than by position.
    components = dict(zip(fit.model.exog_vc.names, (float(v) for v in fit.vcomp)))
    return {
        "converged": bool(fit.converged),
        "sigma2_model": components["model"],
        "sigma2_case": components["case"],
        "sigma2_resid": float(fit.scale),
    }


def permutation_test(data: pd.DataFrame, n_permutations: int = N_PERMUTATIONS,
                     seed: int = PERMUTATION_SEED) -> dict:
    """Permute model labels within cases; one-sided, on the model sum of squares.

    The response is centred within case first, so the case factor carries no
    signal and the statistic isolates the model factor.
    """
    centred = data.copy()
    centred["y"] = centred["d_i"] - centred.groupby("vignette_id")["d_i"].transform("mean")
    codes = pd.Categorical(centred["model"]).codes
    case_codes = pd.Categorical(centred["vignette_id"]).codes
    y = centred["y"].to_numpy()

    def model_sum_of_squares(labels: np.ndarray) -> float:
        total = 0.0
        for label in np.unique(labels):
            group = y[labels == label]
            total += group.size * group.mean() ** 2
        return float(total)

    observed = model_sum_of_squares(codes)
    rng = np.random.RandomState(seed)
    n_at_least = 0
    for _ in range(n_permutations):
        permuted = codes.copy()
        for case in np.unique(case_codes):
            mask = case_codes == case
            permuted[mask] = rng.permutation(permuted[mask])
        if model_sum_of_squares(permuted) >= observed:
            n_at_least += 1
    return {
        "statistic_T_obs": observed,
        "n_perm_ge_obs": n_at_least,
        "p_value": (n_at_least + 1) / (n_permutations + 1),
        "one_sided": True,
        "n_permutations": n_permutations,
        "seed": seed,
    }


def total_sum_of_squares(data: pd.DataFrame) -> float:
    """Corrected total sum of squares of the response, taken from the response.

    Deliberately not the sum of the ANOVA table. Classical eta squared divides an
    effect's sum of squares by the total sum of squares of the response; partial
    eta squared divides it by that effect plus its own error (Levine and Hullett,
    2002; Lakens, 2013). The two answer different questions and the table sum is
    neither of them.

    With type-II sums of squares the terms of the table do not add up to the total
    once they are collinear: the variance they share is attributed to none of them
    and leaves the table altogether. Dividing by the table sum therefore inflates
    every ratio, and inflates it by an amount that grows with collinearity, so the
    resulting figures are not comparable from one fitted model to the next. In this
    dataset the table sums to 99.9% of the total for the two-factor model but to
    only 90.4% once the framework covariate of framework_analysis.py is added.
    """
    y = data["d_i"].to_numpy(dtype=float)
    return float(((y - y.mean()) ** 2).sum())


def sensitivity_anova(data: pd.DataFrame) -> dict:
    """Fixed-effects two-way ANOVA; classical eta squared and omega squared."""
    fit = smf.ols("d_i ~ C(model) + C(vignette_id)", data=data).fit()
    table = anova_lm(fit, typ=2)
    total = total_sum_of_squares(data)
    ss_model = table.loc["C(model)", "sum_sq"]
    df_model = table.loc["C(model)", "df"]
    ms_resid = table.loc["Residual", "sum_sq"] / table.loc["Residual", "df"]
    return {
        "eta2_model": float(ss_model / total),
        "omega2_model": float((ss_model - df_model * ms_resid) / (total + ms_resid)),
        "eta2_case": float(table.loc["C(vignette_id)", "sum_sq"] / total),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--permutations", type=int, default=N_PERMUTATIONS,
                        help="reduce only for a quick check; the registered value is 99999")
    args = parser.parse_args()

    data = load_dissent()
    print(f"observations: {len(data)}")

    components = variance_components(data)
    print("mixed model (REML):")
    for key in ("sigma2_model", "sigma2_case", "sigma2_resid"):
        print(f"  {key} = {components[key]:.6e}")

    permutation = permutation_test(data, n_permutations=args.permutations)
    print(f"permutation test: T_obs = {permutation['statistic_T_obs']:.4f}, "
          f"p = {permutation['p_value']:.3e} "
          f"({permutation['n_perm_ge_obs']} of {permutation['n_permutations']} at least as extreme)")

    sensitivity = sensitivity_anova(data)
    print(f"sensitivity ANOVA: eta2_model = {sensitivity['eta2_model']:.4f}, "
          f"omega2_model = {sensitivity['omega2_model']:.4f}, "
          f"eta2_case = {sensitivity['eta2_case']:.4f}")

    result = {
        "hypothesis": "H1: between-model variance component of per-model dissent d_i > 0",
        "n_obs": len(data),
        "mixed_model": components,
        "permutation": permutation,
        "sensitivity_fixed_effects_anova": sensitivity,
        "verdict_H1": "CONFIRMED" if permutation["p_value"] < 0.05 else "NOT CONFIRMED",
    }
    output = paths.ensure_results() / "confirmatory.json"
    output.write_text(json.dumps(result, indent=1))
    print(f"written: {output.relative_to(paths.ROOT)}")


if __name__ == "__main__":
    main()
