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

# Inventory of entropy uses in the repo (CDI and surroundings)

**Scope:** extraction, not modification.
**Date:** 2026-07-05
**Scope:** the entire repo (code + documents), excluding `venv/`, `.git/`, `__pycache__/`. **Nothing is modified.**

---

## Verdict (one line)

**Does a spectral / von Neumann entropy (category B — over the eigenvalues of a matrix) already exist in the repo?** → **NO.** There is none in either code or Paper B results; the only one implemented (`cdi_entropy`) is **category C** (Shannon over the off-diagonal *similarities*, not over eigenvalues) and is **degenerate/saturated**. The spectral entropy (B) exists only as a **proposal** in `docs/metrologia/cdi_escalado_n.md` (a recent study), with no implementation.

---

## 1. The only entropy computation in CODE

**`analizador.py:203-211`** (inside `calcular_cdi`):

```python
off = [float(matriz_sim[i, j]) for i in range(n) for j in range(n) if i != j]   # :203  off-diagonal of M
...
v = np.clip(off_arr, 1e-10, 1.0)          # :209  the off-diagonal similarities
v = v / v.sum()                            # :210  normalization BY SUM → pseudo-distribution
cdi_entropy = float(-np.sum(v * np.log(v + 1e-10)))   # :211  −Σ v·log v  (Shannon, nats)
```

- **Input:** the `n(n−1)` **off-diagonal cosine similarities** of matrix M, normalized by their sum. **These are not eigenvalues; this is not a categorical distribution of frameworks.**
- **What it represents (docstring `analizador.py:151`, `README.md:124`):** "whether the dissent is spread uniformly across the pairs or concentrated in a few." High = dispersed dissent; low = concentrated.
- **Category: C** (entropy over pairwise similarities).
- **Why it is degenerate:** with n=3 there are 6 off-diagonal entries that are almost equal (similarities ~0.83–0.91) → `v ≈ 1/6` each → `cdi_entropy ≈ log(6) = 1.7918`, **saturated at its maximum**. `SMOKE_TEST_FINDINGS.md:195`: "possibly saturated by the normalization by sum. It needs to be reviewed."
- **The only computation in the whole repo:** no other `.py` computes entropy (neither `scipy.stats.entropy`, nor any other `−Σ p·log p`). `scripts/analizar_paper_b.py:145` only **reads** `cdi_entropy` from the `meta.json`, it does not recompute it.

---

## 2. Table of findings

| # | Location | Input | Cat. | In Paper B results? | Values |
|---|---|---|:--:|---|---|
| 1 | `analizador.py:209-211` (**computation**) | off-diagonal similarities of M, norm. by sum | **C** | Yes (source of all `cdi_entropy`) | ≈ **1.7914–1.7917** (saturated ≈ log 6 = 1.7918) |
| 2 | `analizador.py:151, 218-228` | docstring + payload (`cdi_entropy`, `entropia`) | C | exposes the value | — |
| 3 | `scripts/analizar_paper_b.py:145` | `cdi.get("cdi_entropy")` (only reads it) | C | Yes → `dataframe_maestro.csv` | inherits 1.79… |
| 4 | `docs/strategy/exploratorios_paper_b.md:335,346-348,356,367-369,389,637` | analysis of `cdi_entropy` in Paper B | C | **Yes, as exploratory** → flagged **degenerate** | **mean 1.7916, sd 0.0002** ("nearly constant, does not discriminate"); corr. with others −0.32/−0.51/+0.51 |
| 5 | `docs/strategy/hipotesis_preregistradas_paper_b.md:48` | `cdi_entropy` as a **secondary** variant (supplementary) | C | Yes (secondary) | — |
| 6 | `docs/strategy/protocolo_analitico_paper_b.md:40` | `cdi_entropy` classified as **"exploratory"** | C | Yes (exploratory) | — |
| 7 | `docs/SMOKE_TEST_FINDINGS.md:186-195` | table of `cdi_entropy` + note "saturated, review" | C | Yes (smoke) | 3 cases identical to 3 decimals (~1.792) |
| 8 | `README.md:124` | description: "Shannon over normalized off-diagonal similarities" | C | doc | — |
| 9 | `docs/decisiones_diseno_prompt_v1.1.md:252` | mentions "entropy" as a computed variant of the CDI | C | doc | — |
| 10 | `docs/CHORUS_ISSUES.md:66,243` | `cdi_entropy` in the payload ("the entropic one already computed") | C | doc | — |
| 11 | `static/index.html:965,987-988`; `docs/index.html:1908,3228,3270,3312,3393` | UI that displays `cdi_entropy` / "entropy H" | C | UI (canonical values) | **1.7914 / 1.7915 / 1.7915** (REF-001/002/003) |
| 12 | `resultados/**/*.meta.json` (e.g. `ref_postIssue8/…REF-00X…`, `sub_experimento_v1_1/BANCO-003/run_*`) | persisted `cdi_entropy`/`entropia` field | C | Yes (raw artifacts) | **1.7914–1.7917** |
| 13 | `docs/metrologia/cdi_escalado_n.md:18,107,152,160,227,241` | **von Neumann / spectral entropy (S_norm)** over eigenvalues of M | **B** | **NO** — only a **proposal** (study 2026-07-05), not implemented, no results | formula `S=−Σ p·ln p`, `p=λ/tr(M)` |
| 14 | `README.md:190`; `docs/CHORUS_ISSUES.md:16,270`; `casos_referencia.json` | **Jensen-Shannon** longitudinal (drift of output distributions over time) | (future) | **NO** — future-work idea, not implemented | — |

---

## 3. Classification by category

- **(A) categorical over a discrete distribution** (e.g. chosen frameworks): **none.** The distribution of frameworks (H2) is analyzed with **χ²/Cramér's V**, not with entropy. There is no `scipy.stats.entropy` over frameworks in the repo.
- **(B) spectral over eigenvalues (≡ von Neumann):** **none implemented.** Only the **proposal** `S_norm` in `docs/metrologia/cdi_escalado_n.md` (row 13), a product of the scaling studies, with no code and no results.
- **(C) other:** the **only** real entropy in the repo — `cdi_entropy` = Shannon over the **off-diagonal similarities** normalized by sum (rows 1–12). Degenerate (saturated ≈ log 6).

---

## 4. Did it enter results? Yes (category C), and with what values

`cdi_entropy` **was** indeed computed and persisted in every `meta.json`, passed into Paper B's `dataframe_maestro.csv`, and reported as a **secondary/exploratory** variant:
- Canonical cases (UI/gallery): REF-001 **1.7914**, REF-002 **1.7915**, REF-003 **1.7915** (`docs/index.html:3228,3270,3312`); `ref_postIssue8`: 1.7915/1.7917/1.7917.
- Paper B, 450 runs (`exploratorios_paper_b.md:348`): **mean 1.7916, sd 0.0002** → **degenerate**, nearly constant, "does not discriminate"; noted as an item for CHORUS development (A8), not as a substantive result.

**Contrast with the spectral proposal (B):** `cdi_entropy` (C) saturates because the 6 off-diagonal similarities are almost equal; the spectral entropy `S_norm` (B) uses the **eigenvalues** of M (one dominant eigenvalue + small ones), which **do** vary, and for that reason it does not saturate — this is precisely why the scaling study proposes it as a replacement. Category B **does not yet exist** in the repo except as a proposal.

*Extraction document; it does not alter code or versioned artifacts.*
