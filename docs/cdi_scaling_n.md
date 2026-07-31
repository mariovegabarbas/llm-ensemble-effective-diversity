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

# The CDI at increasing dimension (n = 3 → 17): does `|det(M)|^(1/n)` hold up?

**Scope:** conceptual study, blocking for the design.
**Date:** 2026-07-05
**Figure:** `docs/metrologia/cdi_escalado_n.png`
**How this was computed at the time:** ad-hoc scripts (`cdi_escalado.py`, `cdi_figura.py`), not retained, writing `cdi_results.json` / `cdi_interp.json` in the internal tree. Seed `20260705`, Monte Carlo R=400, d=3072 (the real dimension of `text-embedding-3-large`).

![Figure: Spectral dissent index scaling with dimension n](cdi_scaling_n.png)

---

## Verdict (TL;DR)

**The CDI `|det(M)|^(1/n)` does NOT hold up as-is when moving from n=3 to n=17.** It does not fail through determinant *underflow* (that happens at n≈250–385, far beyond 17), but for two deeper reasons:

1. **Scale strongly dependent on n.** The CDI collapses monotonically toward `1−ρ̄` (ρ̄ = mean similarity). At n=17, cases that at n=3 sat in the "moderate" band drop into the "low" band. **The clinical thresholds calibrated at n=3 (`0.25 / 0.60 / 0.85`) cease to be valid: at n=17 a case of *high* dissent is classified as "low".**
2. **Not robust to redundancy across models.** With families of models that respond similarly (the realistic case of 17 models from ~7 houses), the **geometric mean is dragged down by the small eigenvalues** that redundancy introduces. The separation of the high/low dissent means is **compressed ~5×** (from 0.143 to 0.028) between n=3 and n=17.

- **Does it hold up with normalization?** Only **partially**. Re-anchoring/standardizing the thresholds per n mitigates (1), but does **not** resolve (2): the fragility to small eigenvalues is structural to the geometric mean.
- **Does it need to be reformulated?** **Yes, reformulation is recommended** toward a JSD-type spectral metric (**normalized von Neumann entropy of the spectrum of M**, `S_norm ∈ [0,1]`): it is *intensive* (comparable across n), *robust* to redundancy, *preserves* discrimination as n grows, and uses the JSD apparatus already foreseen in the program. Keep `cdi_geometric` only for backward compatibility at n=3.

---

## 1. What the CDI is and how it must be read

In `analizador.py:193-197`:

```python
det = float(np.linalg.det(matriz_sim))
cdi_geometric = float(np.clip(abs(det) ** (1.0 / n), 0.0, 1.0))
```

`M` = n×n cosine-similarity matrix between the embeddings of the n responses (Gram of normalized vectors; symmetric, PSD, diagonal ≈ 1). Since `|det(M)| = ∏ λ_i` (product of eigenvalues),

> **CDI = `|det(M)|^(1/n)` = geometric mean of the eigenvalues of M = `exp( (1/n) Σ log λ_i )`.**

This reading is the key to the diagnosis: **the geometric mean is catastrophically sensitive to small eigenvalues** (`log λ → −∞` as `λ → 0`). A single near-redundant pair of models (contributing a `λ ≈ 0`) drags the whole metric toward 0, regardless of the actual dissent among the other voices.

Semantics: `M=I` (orthogonal responses, maximum dissent) → CDI=1; `M=11ᵀ` (identical responses, consensus) → CDI=0. Thresholds (`analizador.py:39-56`): low [0,0.25), moderate [0.25,0.60), high [0.60,0.85), maximum [0.85,1.01).

---

## 2. Methodology

**Calibration with real data.** The real 3×3 similarity matrices from Paper B (`docs/casos_galeria_data.json`) have off-diagonal similarity in **0.82–0.91** (ρ̄ ≈ 0.84–0.88): heavily compressed dissent. The simulator is anchored to that range.

**Generative model** (unit embeddings in R³⁰⁷², building `M = cos_sim(V)`):
- **Scenario A — equicorrelation (homogeneous):** one common factor, all off-diagonals ≈ ρ. A "kind" baseline.
- **Scenario B — clustered/redundant (realistic):** 7 families with high intra-family similarity (~0.955) and lower inter-family similarity (ρ). Reproduces that the 17 models come from ~7 houses (OpenAI, Anthropic, Google, Mistral, Meta, Qwen, DeepSeek…) and that within each house the responses are nearly redundant.
- Two dissent levels anchored to the real range: **low** (ρ=0.90) and **high** (ρ=0.80).

**Simulator validation:** the real CDIs at n=3 (0.365, 0.400, 0.328) fall exactly within the simulated range at n=3 (0.30–0.52), and their real `S_norm` values (0.295–0.369) do too. The model is realistic (black diamonds in panel A).

**Sweep:** n = 3, 5, 8, 12, 17. Per cell we compute over R=400 replicates: CDI (current impl. with `det` and stable version with eigenvalues), `cond(M)`, number of eigenvalues below tolerance, `log10|det|`, underflow rate, `S_norm`, and mean separation / Cohen's d for high-vs-low.

---

## 3. Results

### 3.1 Scenario A — equicorrelation (homogeneous)

| n | CDI (low) | CDI (high) | S_norm (low) | S_norm (high) | cond(M) |
|--:|--:|--:|--:|--:|--:|
| 3 | 0.303 | 0.470 | 0.265 | 0.442 | 13 |
| 5 | 0.215 | 0.367 | 0.242 | 0.411 | 22 |
| 8 | 0.171 | 0.309 | 0.224 | 0.387 | 36 |
| 12 | 0.147 | 0.276 | 0.212 | 0.369 | 54 |
| 17 | 0.134 | 0.256 | 0.202 | 0.355 | 79 |

→ The CDI **does not collapse to 0**: it converges toward `1−ρ` (0.10 and 0.20). The `1/n` normalization *does* compensate for the geometric collapse of the determinant. `CDI_det` ≡ `CDI_eig` (no numerical error at n≤17). With homogeneous structure, the CDI **would hold up**.

### 3.2 Scenario B — clustered / redundant (realistic)

| n | CDI low (level) | CDI high (level) | **CDI mean sep.** | S_norm mean sep. | cond(M) | log10\|det\| |
|--:|--:|--:|--:|--:|--:|--:|
| 3 | 0.377 (moderate) | 0.520 (moderate) | **0.143** | 0.153 | 11 | −0.9 |
| 5 | 0.280 (moderate) | 0.417 (moderate) | **0.137** | 0.149 | 18 | −1.9 |
| 8 | 0.209 (**low**) | 0.307 (moderate) | **0.098** | 0.134 | 143 | −4.1 |
| 12 | 0.150 (low) | 0.198 (**low**) | **0.048** | 0.115 | 225 | −8.4 |
| 17 | 0.119 (low) | 0.147 (**low**) | **0.028** | 0.103 | 331 | −14.2 |

→ **This is the decisive failure.** With realistic redundancy:
- At **n=8** the levels already break: the low-dissent case drops to "low" while the high one stays at "moderate" — the scale ceases to be comparable.
- At **n=17** *both* levels fall into "low" (0.119 vs 0.147): **a high-dissent case would be labeled as low dissent (clinical false negative).**
- The mean separation collapses from 0.143 → **0.028** (−80%), whereas that of `S_norm` only drops 0.153 → 0.103 (−33%).
- `cond(M)` explodes (11 → 331): intra-family redundancy injects small eigenvalues that dominate the geometric mean.

### 3.3 Discriminative power (Cohen's d, high vs low)

| n | CDI (equi) | S_norm (equi) | **CDI (clustered)** | **S_norm (clustered)** |
|--:|--:|--:|--:|--:|
| 3 | 54 | 53 | 35 | 37 |
| 8 | 112 | 115 | 64 | 69 |
| 12 | 143 | 144 | **57** | 76 |
| 17 | 170 | 179 | **54 ↓** | **81 ↑** |

→ In the clustered case, the CDI's Cohen's d **degrades** from n=8 onward (64→54), while that of `S_norm` **keeps growing** (69→81). (The absolute values are high because Monte Carlo variance is low with ρ fixed; what matters is the *relative trend* and, above all, the mean separation of §3.2, which is what the clinician sees.)

### 3.4 Numerical diagnosis

- **Underflow of `np.linalg.det → 0.0`:** equicorrelation (ρ=0.85) at **n≈385**; clustered (ρ=0.80) at **n≈250**. → At n=17 there is **no underflow**; `log10|det|` reaches −14 (clustered), still far from the double limit (−308).
- **Eigenvalues < 1e-8:** none at n≤17 (with d=3072 the vectors are generically independent). The problem is **not** hard rank-deficiency, but **ill-conditioning** (`cond` up to ~330) that biases the geometric mean.
- **Numerical conclusion:** the current implementation with `np.linalg.det` does not blow up at n=17, but it should nonetheless be computed as `exp(mean(log λ))` via `eigvalsh` (identical result, numerically stable, and it yields `cond(M)` for free as a diagnostic).

---

## 4. Why `S_norm` is the correct reformulation

Candidate: **normalized spectral entropy** (= von Neumann entropy of the spectrum of M, normalized; equivalent to the JSD of the spectrum against the uniform spectrum):

```
p_i = λ_i / Σλ_j          # λ = eigenvalues of M (Σλ = trace = n)
S_norm = ( −Σ p_i log p_i ) / log n      # ∈ [0,1], high = dissent, intensive
```

- **Same semantics as the CDI:** `M=I` → `S_norm=1` (maximum dissent); rank-1 consensus → `S_norm=0`.
- **Robust to redundancy:** the weight `p_i log p_i → 0` as `p_i → 0`. A near-null eigenvalue (redundant pair) does **not** drag the metric, unlike the geometric mean.
- **Intensive:** comparable across different n (normalized by `log n`), which allows a single set of thresholds.
- **Connection to the program:** it is the Jensen–Shannon/entropy apparatus already foreseen for the longitudinal component (`README.md:190`, `casos_referencia.json`, `CHORUS_ISSUES.md`). Here it is applied to the *spectrum* of M (a natural probability distribution over the n "directions of consensus/dissent").

The empirical evidence in §3 supports it: `S_norm` maintains growing separation and Cohen's d under redundancy, where the CDI degrades.

> An equivalent and perhaps more intuitive alternative to communicate: **effective number of independent voices** `N_eff = exp(S) = exp(−Σ p_i log p_i)` ∈ [1, n]. It measures how many "genuinely distinct" voices there are once redundancy is discounted; `S_norm = log(N_eff)/log(n)`.

---

## 5. Design recommendation

| Question | Answer |
|---|---|
| Does the CDI hold up at n=17 **as-is**? | **No.** n-dependent scale (breaks thresholds) + non-robustness to redundancy. |
| Does it hold up **with normalization**? | **Partially.** Re-anchoring thresholds per n fixes the scale, not the fragility to small eigenvalues. Insufficient for 17 models with redundant families. |
| Does it need to be **reformulated**? | **Yes.** Adopt `S_norm` (normalized spectral entropy / JSD of the spectrum) as the multi-model metric. |

**Concrete suggested plan** (pending authorization — `analizador.py` has not been touched):
1. Add `cdi_spectral = S_norm` (via `eigvalsh`) to the `calcular_cdi` payload, alongside `cond(M)` and `N_eff` as diagnostics.
2. Promote `cdi_spectral` to the primary metric of the multi-model ensemble; keep `cdi_geometric` only for backward compatibility and comparison at n=3.
3. Recalibrate the clinical thresholds on `cdi_spectral` with the bank (the `cdi_geometric` thresholds are not transferable).
4. Always report `cond(M)` / `N_eff`: if redundancy is high, it warns that the ensemble contributes fewer independent voices than its nominal count — valuable information in itself for the design of the 17-model panel.

---

## 6. Frozen formal definition (spectral CDI)

> This section **extracts the exact definition as it was computed** in the test (`cdi_escalado.py`, function `metrics`, lines 17–31). **Nothing** is implemented in `analizador.py`; it is the reference specification for a future implementation.

### 6.1 Starting object: the matrix M

`M` = **raw cosine-similarity matrix**, not re-normalized: `M = V̂ V̂ᵀ`, where `V̂` are the **L2-normalized** embeddings of the n responses (Gram of unit vectors). It is exactly the `matriz_sim` that `calcular_cdi` receives today (`analizador.py:131-136`, `cosine_similarity`).
- Symmetric and positive semidefinite (PSD) by construction.
- **Diagonal = 1** ⇒ **trace `tr(M) = Σᵢ λᵢ = n`** (verified: the 3 real cases give `tr(M)=3.0000`).
- No normalization is applied to M before spectral decomposition (the normalization is done *on the eigenvalues*, §6.2).

### 6.2 Spectral index: normalized von Neumann entropy

Let `λ₁,…,λₙ` be the spectrum of M (`np.linalg.eigvalsh`, after `clip(λ, 0, ∞)`; §6.6). The eigenvalues are normalized to a probability distribution **by the trace**:

```
pᵢ = λᵢ / Σⱼ λⱼ = λᵢ / tr(M) = λᵢ / n        (with diag(M)=1)
```

This is identical to taking the **density matrix** `ρ = M / tr(M)` and using its eigenvalues. The entropy (von Neumann of ρ; equivalently Shannon of the normalized spectrum), in **nats** (natural logarithm):

```
S = − Σᵢ pᵢ ln pᵢ                 with the convention  0·ln 0 ≡ 0
```

Range: **`S ∈ [0, ln n]`**.

**Normalization to [0,1]** — dividing by `ln n`, **not** by `ln N_eff`:

```
S_norm = S / ln n  ∈ [0, 1]
```

Reason for `ln n`: `ln n` is the **exact maximum** of `S` (uniform distribution `pᵢ=1/n`, which corresponds to `M = I`, maximum dissent). Dividing by `ln n` anchors maximum dissent to 1 independently of n → an **intensive** metric (comparable across n). `S_norm` is furthermore **invariant to the base of the logarithm** (the base cancels with that of `ln n`).

**Direction — "high = more dissent" (numerically confirmed, §6.4):** `M = I` (orthogonal responses, maximum disagreement) → `S_norm = 1`; rank-1 consensus (`M = 11ᵀ`) → `S_norm = 0`. Same direction as the current `cdi_geometric`.

### 6.3 Effective number of voices `N_eff`

```
N_eff = exp(S) = eˢ           (natural base, consistent with S in nats)
```

- It is the **perplexity / Hill number of order 1** of the spectrum. Units: **"number of independent voices"**.
- Range: **`N_eff ∈ [1, n]`**.
- Exact relation to the normalized index: **`S_norm = ln(N_eff) / ln(n) = log_n(N_eff)`**, equivalently **`N_eff = n^{S_norm}`**. (Base-invariant: `N_eff` comes out identical using `ln`+`exp` or `log₂`+`2^·`.)
- Design interpretation: `N_eff` counts how many "genuinely distinct" voices remain once redundancy between models is discounted. A nominal 17-model panel with redundant families can have `N_eff ≪ 17`.

### 6.4 Limiting cases (numerically verified)

| Configuration | Spectrum of M | S | S_norm | N_eff | Reading |
|---|---|--:|--:|--:|---|
| **Identical** `M=11ᵀ` (n=3,5,17) | `(0,…,0, n)` | 0 | **0** | **1** | minimum dissent (total consensus) |
| **Orthogonal** `M=I`, n=3 | `(1,1,1)` | ln3=1.0986 | **1** | **3** | maximum dissent |
| **Orthogonal** `M=I`, n=5 | `(1,…,1)` | ln5=1.6094 | **1** | **5** | maximum dissent |
| **Orthogonal** `M=I`, n=17 | `(1,…,1)` | ln17=2.8332 | **1** | **17** | maximum dissent |

The limits are exact: `N_eff → 1` (identical) and `N_eff → n` (orthogonal), with `S_norm ∈ {0,1}`.

### 6.5 Continuity anchor: real Paper B cases at n=3

Recomputed with the spectral formula (the `0.365/0.400/0.328` values were from the **old** index `|det|^{1/n}`):

| Case | Spectrum of M | `tr(M)` | old CDI `|det|^{1/n}` | **S** | **S_norm** | **N_eff** |
|---|---|--:|--:|--:|--:|--:|
| REF-001 | (0.106, 0.169, 2.725) | 3.0000 | 0.3652 | 0.3673 | **0.3343** | **1.444** |
| REF-002 | (0.128, 0.186, 2.687) | 3.0000 | 0.3995 | 0.4055 | **0.3691** | **1.500** |
| REF-003 | (0.089, 0.144, 2.767) | 3.0000 | 0.3283 | 0.3243 | **0.2952** | **1.383** |

**Good continuity:** at n=3, `S_norm` (0.295–0.369) stays very close to the old CDI (0.328–0.400) and **preserves the same ordering** (REF-002 > REF-001 > REF-003 with both metrics). All three have `N_eff ≈ 1.4–1.5`: of 3 nominal voices, only ~1½ are effectively independent → high redundancy/consensus, consistent with the 0.84–0.88 similarities.

### 6.6 Pending implementation decisions (they affect the definition)

To freeze before implementing in `analizador.py`:

1. **Tolerance for eigenvalues ~0.** In the test: `λ ← clip(λ, 0, ∞)` and then the strict `pᵢ = 0` values are discarded (`p = p[p>0]`), applying `0·ln 0 ≡ 0`. The small but >0 `pᵢ` cause **no** numerical problem (there is never `ln 0`). **Pending:** fix a relative threshold (e.g. `λ < εₘ·λ_max` → 0) or keep the strict `>0` filter? At n≤17 with d=3072 it is immaterial (there are no null eigenvalues), but it is worth fixing for large n.
2. **M not positive definite.** `cosine_similarity` is PSD in theory; through rounding it may yield slightly negative eigenvalues. In the test this was resolved with `clip(λ, 0, ∞)`. **Pending:** confirm `clip` (vs. `abs`) as the official policy.
3. **Normalization by trace vs. by n.** The test uses `pᵢ = λᵢ / Σλ` (trace). Since `diag(M)=1` ⇒ `tr(M)=n`, it coincides with `λᵢ/n`. **Recommendation:** keep `Σλ` (trace) in the formula, so it is robust if M ever had a diagonal not exactly 1.
4. **Base of the logarithm.** The test uses natural (nats). `S_norm` and `N_eff` are **base-invariant**; only raw `S` depends on it. **Pending:** report `S` in nats by convention, or expose `S_norm`/`N_eff` directly (invariant) and omit `S`.
5. **Clinical thresholds.** Those of `cdi_geometric` are **not** transferable to `S_norm`. It requires recalibration with the bank (outside the scope of this task).

**Frozen formula (summary):**
```
M  = V̂ V̂ᵀ                       # Gram of L2-normalized embeddings (= cosine similarity)
λ  = eigvalsh(M);  λ ← max(λ,0)   # spectrum, guards PSD
p  = λ / Σλ                       # normalization by trace (= λ/n if diag=1)
S      = − Σ p·ln p               # von Neumann (nats),  0·ln0≡0,   S ∈ [0, ln n]
S_norm = S / ln n                 # dissent index ∈ [0,1], high = more dissent
N_eff  = exp(S) = n^{S_norm}      # effective number of voices ∈ [1, n]
```

---

## 7. Reproducibility

How the sweep was run at the time. The two scripts below belong to the internal tree and were
not retained, so these commands are a record of the procedure and not instructions that can be
executed against this deposit.

```bash
python3 cdi_escalado.py   # MC sweep -> cdi_results.json (tables in §3)
python3 cdi_figura.py     # interpretability + figure cdi_escalado_n.png
```

Real input: `docs/casos_galeria_data.json` (3×3 matrices). Function under test: `analizador.py:calcular_cdi` (`cdi_geometric = |det(M)|^(1/n)`). Candidate metric: `S_norm` (normalized von Neumann entropy of the spectrum of M). Textbook JSD not yet implemented in the repo; `S_norm` is its spectral instance.
