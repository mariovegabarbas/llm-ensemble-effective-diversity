> **Design document, frozen at registration.** This file is one of the four documents
> the sealed preregistration (osf.io/c5qk7) names as held in the project repository and
> released with the paper. It is reproduced here as it stood when the study was
> registered, and is not updated to match the executed study: it therefore describes a
> panel of **seventeen** models. One of them, `openai/gpt-oss-120b`, was excluded before
> execution because its reasoning could not be disabled, leaving the sixteen that were
> run. That exclusion is Deviation 1 in `deviations_from_preregistration.md`, which also
> records the second execution deviation and the departures adopted afterwards.
>
> For the same reason, the paths, file names and code references that appear in the body
> below belong to the project's internal working tree as it stood at registration, not to
> this deposit: `analizador.py`, the helper scripts and the intermediate result files named
> here are not part of the released repository. They are kept because these documents are
> the record of how the index was defined and tested at the time, and rewriting their
> references would misrepresent that record. The released implementation of the index is
> `src/dissent.py`.

# Per-model dissent metric and feasibility of the variance partition

**Scope:** a study, not an implementation. Pre-registration material for the 17-model paper.
**Date:** 2026-07-05
**How this was computed at the time:** ad-hoc scripts (`parte12.py`, `parte3b.py`), not retained. Seed `20260705`; `statsmodels 0.14.6`. Real data: `docs/casos_galeria_data.json` of the internal tree.
**Neither `analizador.py` nor any versioned artifact is touched.**

This dovetails with [model_case_decomposition.md](model_case_decomposition.md) (§6: "Paper B had no unified dominance test") and with [cdi_scaling_n.md](cdi_scaling_n.md) (S_norm / N_eff).

---

## Verdict (TL;DR)

- **Recommended metric (freezable):** candidate **(a)**, the **consensus separation** of each voice i:
  `dᵢ = 1 − (1/(n−1)) · Σⱼ≠ᵢ Mᵢⱼ`. Cheap (O(n²)), interpretable, direction guaranteed, coherent with `N_eff` (corr **0.9995**), and it **matches the Paper B SOLO exactly** (an identity, not an approximation).
- **Variance partition: feasible.** A mixed-effects model with `modelo` and `caso` as crossed random effects on `dᵢ` **converges and is identifiable** at the design size (17×450 = 7650 obs); the variance components (MixedLM) and the method of moments **agree**.
- **Power:** to **detect** a model effect, ≈1.00 even with small effects; to **demonstrate dominance** (σ²_modelo > σ²_caso), power **≥0.87 if the model contributes ≥2×** the case variance, ~0.51 at parity.
- **Substantive caveat:** "who diverges" (argmax of `dᵢ` = SOLO, categorical, concentrated on gpt-4o) **is not the same** as "what fraction of the variance in *how much* each voice separates is due to model" (VPC). The crude estimate from the 3 real cases suggests a ratio var_modelo/var_caso ≈ 0.35 (< 1). The 17-model paper must **measure and report both**, not infer one from the other.

---

## Part 1 — Per-model metric candidates

One figure per **model × case** pair (per run), derived from the same `M` (n×n cosine similarity) that yields `S_norm`/`N_eff`.

| | Definition | Range (practical, Mᵢⱼ≥0) | Interpretation | Cost (n=17) | Coherence with S_norm/N_eff | Edge cases |
|---|---|---|---|---|---|---|
| **(a)** consensus separation | `dᵢ = 1 − (1/(n−1))Σⱼ≠ᵢ Mᵢⱼ` | [0, 1] | **high = voice i separates more from the rest** | **0.0032 ms** (O(n²), M already available) | `mean_i dᵢ ≡ cdi_mean_dissent`; corr(mean dᵢ, N_eff)=**0.9995**, with S_norm=0.9985 | identical→**0**, orthogonal→**1** ✓ |
| **(b)** distance to centroid | `dᵢ = 1 − ⟨v̂ᵢ, c/‖c‖⟩`, `c=(1/n)Σⱼ v̂ⱼ` | [0, ~1] | same as (a) | O(n·D); **requires raw embeddings V̂** | monotone with (a); nearly identical | identical→0, orthogonal→~1 ✓ |
| **(c)** spectral leave-one-out | `dᵢ = N_eff(M) − N_eff(M₋ᵢ)` | can be **< 0** | direct link to N_eff, but direction **not monotone** | **0.34 ms** (n eigendecomps., ~100× (a)) | argmax correct (dissenter), **but redundant voices give a negative value** (confusing interpretation) |

**Recommendation: (a).** Reasons:
1. **Clean interpretation and guaranteed direction** (0 = consensus, 1 = orthogonal to the rest), verified at the limits.
2. **Maximal coherence with the primary index:** its mean is *exactly* `cdi_mean_dissent = 1 − mean(off-diag)` (verified: `0.150352 == 0.150352`), and it correlates 0.9995 with `N_eff`. It is the **per-voice additive decomposition** of an ensemble metric that already exists in the payload.
3. **Trivial cost** and it **needs only M** (not the raw embeddings, which Paper B does not persist) — a decisive practical advantage over (b).
4. (c) is theoretically the most tightly linked to `N_eff` but **does not work as a "separation"**: it yields negative values for redundant voices (removing a redundant voice *raises* N_eff) and costs ~100× more.

### Freezable definition

```
Input: M = n×n cosine similarity matrix (diag=1), the same one as S_norm/N_eff.
For each voice i:
    dᵢ = 1 − (1/(n−1)) · Σⱼ≠ᵢ Mᵢⱼ        # consensus separation
Properties:
    consenso_individualᵢ = 1 − dᵢ = (1/(n−1))Σⱼ≠ᵢ Mᵢⱼ   (mean similarity with the rest)
    mean_i dᵢ = 1 − mean(off-diag M) = cdi_mean_dissent  (reconstructs the ensemble metric)
    SOLO(case) = argmax_i dᵢ = argmin_i consenso_individualᵢ
Range: [0, 2] theoretical; [0, 1] with non-negative similarities (real case).
Direction: high = the voice separates more from consensus.
```

---

## Part 2 — Anchoring to the Paper B SOLO

The CHORUS SOLO is defined as the model with the **lowest** `consenso_individual` (field `solo` in `casos_galeria_data.json`), and `consenso_individual = 1 − dᵢ`. Therefore **`argmax dᵢ ≡ SOLO` is an identity**, not a coincidence. Verification on the 3 real cases (n=3):

| Case | dᵢ (gpt-4o, claude, gemini) | argmax → | Paper B SOLO | pred. vs reported consensus |
|---|---|---|---|---|
| REF-001 | (0.1451, **0.1456**, 0.1217) | **claude** | claude-sonnet-4.5 | 0.8544 == 0.8544 |
| REF-002 | (**0.1706**, 0.1536, 0.1462) | **gpt-4o** | gpt-4o | 0.8294 == 0.8294 |
| REF-003 | (**0.1275**, 0.1177, 0.1040) | **gpt-4o** | gpt-4o | 0.8725 == 0.8725 |

**3/3 exact matches**, with `consenso_individual` reproduced to 4 decimals. The continuous metric `dᵢ` **generalizes the categorical SOLO without contradicting it**: the SOLO is its argmax; `dᵢ` adds the *magnitude* of the separation (how much, not just who) and defines the separation of **all** voices, not only the dissenting one.

---

## Part 3 — Feasibility of the variance partition

**Simulated design:** 17 models across ~7 families with intra-family redundancy (`g=0.90`), 15 cases, 30 replicates → `dᵢ` per (model, case, replicate) = **7650 observations (17×450 runs)**. Statistical model: `d ~ 1 + (1|modelo) + (1|caso)` (**crossed** random effects).

### (i) Convergence and identifiability — **YES**
`MixedLM` (statsmodels, REML, lbfgs) **converges** (`converged=True`) on the 7650 obs. The variance components agree with the **method of moments** (balanced two-way ANOVA, closed form), which provides robustness:

| | σ²_modelo | σ²_caso | σ²_resid | VPC model | VPC case |
|---|---|---|---|---|---|
| Method of moments | 0.001196 | 0.000520 | 0.000008 | **69.3 %** | 30.2 % |
| Crossed MixedLM | 0.001158 | 0.000516 | 0.000009 | ~69 % | ~30 % |

(In this dataset, calibrated with a strong model effect, **the model dominates 2.3×** — the test recovers this correctly.)

### (ii) Interpretable partition — **YES**
The VPC (variance partition coefficient) `σ²_factor / (σ²_modelo+σ²_caso+σ²_int+σ²_resid)` gives directly interpretable per-factor fractions. `model dominance ⇔ σ²_modelo > σ²_caso ⇔ VPC_modelo > VPC_caso`.

### (iii) Power to detect dominance (model > case), B=300, α=0.05

| true ratio σ²_modelo/σ²_caso | **power (dominance)** | P(model effect significant) |
|---:|---:|---:|
| 0.5 (case dominates) | 0.127 | 0.997 |
| 1.0 (parity) | 0.513 | 1.000 |
| 2.0 | **0.870** | 1.000 |
| 4.0 | **0.987** | 1.000 |

Reading: **detecting** that a model effect exists is nearly certain (P≈1.00) even with small effects; **demonstrating dominance** requires the model to contribute ≥2× the case variance for power ≥0.87. At parity, power is ~0.5 (as expected: telling two nearly equal variances apart is hard). When the case truly dominates (0.5), the "dominance power" drops to 0.13 — correct: it **does not fabricate** false dominance.

### Recommended statistic
**Primary: variance components of the crossed mixed model (VPC/ICC per factor).** It treats `modelo` and `caso` as samples from broader populations (allowing "dissent is a model effect" to generalize beyond these 17 and 15), gives σ² on the same scale, and handles imbalance. **Sensitivity: ω²/η² from a two-way fixed-effects ANOVA** (answers "for these specific 17 models and 15 cases"). In a balanced design, moments and MixedLM agree (verified) — reporting both shields the result against the method.

### ⚠️ Critical caveat: categorical vs. variance
The Paper B SOLO (H3) is **categorical dominance** of *who* diverges (argmax concentrated on gpt-4o, validated 3/3 in Part 2). The variance partition answers a **different** question: what fraction of the variation in *how much* each voice separates is due to model vs. case. **They do not imply each other.** The **crude** estimate over the 3 real cases (3×3, indicative only):

| | dᵢ means | variance |
|---|---|---|
| by model (gpt, claude, gemini) | (0.1477, 0.1390, 0.1240) | 0.000144 |
| by case (REF-1,2,3) | (0.1375, 0.1568, 0.1164) | 0.000409 |

→ **ratio var_modelo/var_caso ≈ 0.35 (< 1)**: over the *magnitude* `dᵢ`, the **case** could explain more variance than the model, even though the SOLO is concentrated on one model. This is n=3×3, not reliable, but it warns: the 17-model paper must not assume that the SOLO's concentration implies model dominance in variance. **Measure the two things separately.**

---

## Implications for the re-pre-registration (17-model paper)

1. **Freeze `dᵢ` (candidate a)** as the per-model dissent metric, alongside `S_norm`/`N_eff` (ensemble) — all derived from the same `M`.
2. **Dominance test:** crossed mixed model `d ~ 1 + (1|modelo) + (1|caso)`, VPC as the primary statistic, ω²/η² as sensitivity. The 17×450 design is sufficient for convergence and identifiability.
3. **Pre-register two separate hypotheses:** (H-who) categorical concentration of the SOLO/argmax on a single model; (H-how-much) VPC_modelo > VPC_caso over `dᵢ`. They are distinct; power and conclusion differ.
4. **Power:** size the dominance claim to an effect ≥2× (power ≥0.87 with 17×450). If the true ratio is near 1, declare in advance that the design will have only ~0.5 power for "dominance" (although it will indeed detect the model effect).

*Study document; it does not alter code or versioned artifacts.*
